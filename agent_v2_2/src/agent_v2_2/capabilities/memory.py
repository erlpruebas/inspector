import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, List, Optional, Tuple, Dict, Set
from ..config import load_config

# ------------------------------------------------------------------------------
# Constants & Models
# ------------------------------------------------------------------------------

STOP_WORDS = {
    "a", "al", "algo", "as", "bajo", "con", "como", "cual", "de", "del", "desde",
    "el", "ella", "ellos", "en", "entre", "era", "es", "esta", "está", "esto", "la",
    "las", "le", "les", "lo", "los", "mi", "mis", "no", "o", "para", "por", "que",
    "qué", "se", "si", "sí", "su", "sus", "te", "un", "una", "y", "ya",
}

NAVIGATION_HINTS = (
    "como llego", "como ir", "ruta", "direccion", "mapa", "google maps",
    "desde mi casa", "ir a", "llevarme", "navegar",
)

@dataclass
class MemoryFact:
    kind: str
    label: str
    value: str
    source_text: str
    user_id: str
    thread_id: str
    created_at: str
    confidence: float = 1.0
    aliases: Tuple[str, ...] = field(default_factory=tuple)

@dataclass
class MemoryContext:
    retrieval_query: str
    facts: Tuple[MemoryFact, ...] = field(default_factory=tuple)
    thread_summary: str = ""
    source_count: int = 0

# ------------------------------------------------------------------------------
# Utils
# ------------------------------------------------------------------------------

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()

def safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9._-]+", "_", value.casefold())
    return slug.strip("_") or "default"

def tokenize(text: str) -> Tuple[str, ...]:
    return tuple(
        token
        for token in re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+", text.casefold())
        if len(token) > 1
    )

def fact_aliases(kind: str, label: str) -> Tuple[str, ...]:
    aliases = {kind.casefold(), label.casefold()}
    if "home" in kind or "casa" in label.casefold():
        aliases.update({"mi casa", "casa", "home", "direccion de mi casa", "dirección de mi casa"})
    if "address" in kind or "direccion" in label.casefold():
        aliases.update({"mi direccion", "mi dirección", "direccion", "dirección"})
    return tuple(sorted(aliases))

def extract_memory_facts(text: str, user_id: str, thread_id: str) -> Tuple[MemoryFact, ...]:
    normalized = normalize_text(text)
    lower = normalized.casefold()
    facts: List[MemoryFact] = []

    patterns: List[Tuple[str, str, List[str]]] = [
        (r"(?:recuerda que\s+)?mi casa (?:esta|está) en (?P<value>.+)", "home_address", ["Casa"]),
        (r"(?:recuerda que\s+)?mi direccion (?:es|está en|esta en) (?P<value>.+)", "address", ["Direccion"]),
        (r"(?:recuerda que\s+)?este cliente se llama (?P<value>.+)", "client_name", ["Cliente"]),
        (r"(?:recuerda que\s+)?mi proveedor (?:es|preferido es) (?P<value>.+)", "provider", ["Proveedor"]),
        (r"cuando diga (?P<label>.+?) me refiero a (?P<value>.+)", "alias", ["Alias"]),
        (r"(?:recuerda que\s+)?prefiero que (?P<value>.+)", "preference", ["Preferencia"]),
        (r"(?:recuerda que\s+)?(?:mi|la) contrasena (?:es|esta en|está en) (?P<value>.+)", "secret", ["Credencial"]),
    ]

    for pattern, kind, labels in patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if not match:
            continue
        raw_value = normalize_text(match.group("value"))
        if not raw_value:
            continue
        label = normalize_text(match.groupdict().get("label") or labels[0])
        aliases = fact_aliases(kind, label)
        facts.append(
            MemoryFact(
                kind=kind,
                label=label,
                value=raw_value,
                source_text=normalized,
                user_id=user_id,
                thread_id=thread_id,
                created_at=now_iso(),
                aliases=aliases,
            )
        )

    if "mi casa" in lower and not any(f.kind == "home_address" for f in facts):
        match = re.search(r"mi casa (?:es|está|esta) (?P<value>.+)", normalized, flags=re.IGNORECASE)
        if match:
            raw_value = normalize_text(match.group("value"))
            if raw_value:
                facts.append(
                    MemoryFact(
                        kind="home_address",
                        label="Casa",
                        value=raw_value,
                        source_text=normalized,
                        user_id=user_id,
                        thread_id=thread_id,
                        created_at=now_iso(),
                        aliases=fact_aliases("home_address", "Casa"),
                    )
                )

    return tuple(facts)

def summarize_event(event: Dict[str, Any]) -> str:
    event_type = str(event.get("type", "event"))
    if event_type == "message":
        return normalize_text(str(event.get("text", "")))[:180]
    if event_type == "fact":
        fact = event.get("fact") if isinstance(event.get("fact"), dict) else event
        if isinstance(fact, dict):
            return normalize_text(f"{fact.get('label', '')}: {fact.get('value', '')}")[:180]
    if event_type == "decision":
        return normalize_text(f"{event.get('tool_id', '')} {event.get('reason', '')}")[:180]
    if event_type == "result":
        return normalize_text(str(event.get("output", "")))[:180]
    return normalize_text(json.dumps({k: v for k, v in event.items() if k != "timestamp"}, ensure_ascii=False))[:180]

def render_event_markdown(event: Dict[str, Any]) -> str:
    timestamp = str(event.get("timestamp", now_iso()))
    event_type = str(event.get("type", "event"))
    role = str(event.get("role", "system"))
    lines = [f"## {timestamp} | {event_type} | {role}"]

    def add_field(name: str, value: Any) -> None:
        if value is None or value == "" or value == [] or value == {}:
            return
        if isinstance(value, list):
            lines.append(f"- {name}:")
            for item in value:
                lines.append(f"  - {item}")
            return
        if isinstance(value, dict):
            lines.append(f"- {name}:")
            for key, item in value.items():
                if isinstance(item, (dict, list)):
                    lines.append(f"  - {key}: {json.dumps(item, ensure_ascii=False)}")
                else:
                    lines.append(f"  - {key}: {item}")
            return
        lines.append(f"- {name}: {value}")

    for key in ("request_id", "user_id", "thread_id", "tool_id", "tier", "reason", "privacy_mode", "ok", "error"):
        add_field(key, event.get(key))

    if event_type == "message":
        add_field("metadata", event.get("metadata"))
        text = normalize_text(str(event.get("text", "")))
        if text:
            lines.append("")
            lines.append("> " + text.replace("\n", "\n> "))
    elif event_type == "fact":
        fact = event.get("fact") or {}
        if isinstance(fact, dict):
            for key in ("kind", "label", "value", "source_text", "user_id", "thread_id", "confidence", "created_at"):
                add_field(key, fact.get(key))
            aliases = fact.get("aliases") or []
            if aliases:
                lines.append("- aliases:")
                for alias in aliases:
                    lines.append(f"  - {alias}")
    elif event_type == "decision":
        add_field("memory_retrieval_query", event.get("memory_retrieval_query"))
        add_field("memory_fact_labels", event.get("memory_fact_labels"))
    elif event_type == "result":
        add_field("output", event.get("output"))
        add_field("attachments", event.get("attachments"))
        add_field("requires_human_confirmation", event.get("requires_human_confirmation"))
        add_field("human_confirmation", event.get("human_confirmation"))
    else:
        add_field("data", {k: v for k, v in event.items() if k not in {"timestamp", "type", "role"}})

    return "\n".join(lines).rstrip()

def parse_markdown_events(text: str) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None
    lines = text.splitlines()
    i = 0

    def finish() -> None:
        nonlocal current
        if current:
            events.append(current)
        current = None

    while i < len(lines):
        line = lines[i].rstrip("\n")
        match = re.match(r"^##\s+(?P<timestamp>[^|]+)\s+\|\s+(?P<type>[^|]+)\s+\|\s+(?P<role>.+)$", line)
        if match:
            finish()
            current = {
                "timestamp": match.group("timestamp").strip(),
                "type": match.group("type").strip(),
                "role": match.group("role").strip(),
            }
            i += 1
            continue
        if current is None:
            i += 1
            continue
        if line.startswith("> "):
            body_lines = [line[2:]]
            i += 1
            while i < len(lines) and lines[i].startswith("> "):
                body_lines.append(lines[i][2:])
                i += 1
            current["text"] = normalize_text("\n".join(body_lines))
            continue
        bullet = re.match(r"^-\s+([^:]+):\s*(.*)$", line)
        if bullet:
            key = bullet.group(1).strip()
            value = bullet.group(2)
            if i + 1 < len(lines) and lines[i + 1].startswith("  - "):
                items: List[str] = []
                if value:
                    items.append(value)
                i += 1
                while i < len(lines) and lines[i].startswith("  - "):
                    items.append(lines[i][4:])
                    i += 1
                current[key] = items
                continue
            current[key] = value
        i += 1
    finish()
    return events


# ------------------------------------------------------------------------------
# Core Class
# ------------------------------------------------------------------------------

class MemoryStore:
    def __init__(self, base_dir: Optional[Path] = None):
        if not base_dir:
            config = load_config()
            self.base_dir = config.workspace_root / "memory"
        else:
            self.base_dir = base_dir.resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def thread_dir(self, user_id: str, thread_id: str) -> Path:
        thread_dir = self.base_dir / safe_slug(user_id) / safe_slug(thread_id)
        (thread_dir / "raw").mkdir(parents=True, exist_ok=True)
        return thread_dir

    def raw_day_path(self, user_id: str, thread_id: str, timestamp: Optional[str] = None) -> Path:
        timestamp = timestamp or now_iso()
        day = timestamp[:10]
        return self.thread_dir(user_id, thread_id) / "raw" / f"{day}.md"

    def append_event(self, user_id: str, thread_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
        event = {
            "timestamp": event.get("timestamp") or now_iso(),
            "user_id": user_id,
            "thread_id": thread_id,
            **event,
        }
        path = self.raw_day_path(user_id, thread_id, timestamp=str(event["timestamp"]))
        with path.open("a", encoding="utf-8") as handle:
            handle.write(render_event_markdown(event))
            handle.write("\n\n")
        return event

    def record_message(self, user_id: str, thread_id: str, role: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.append_event(
            user_id,
            thread_id,
            {
                "type": "message",
                "role": role,
                "text": normalize_text(text),
                "metadata": metadata or {},
            },
        )

    def record_fact(self, fact: MemoryFact) -> Dict[str, Any]:
        return self.append_event(
            fact.user_id,
            fact.thread_id,
            {
                "type": "fact",
                "fact": asdict(fact),
            },
        )

    def load_events(self, user_id: str, thread_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        raw_dir = self.thread_dir(user_id, thread_id) / "raw"
        if raw_dir.exists():
            for path in sorted(raw_dir.glob("*.md")):
                events.extend(parse_markdown_events(path.read_text(encoding="utf-8")))

        # Legacy JSONL reader (migrator)
        legacy_jsonl = self.base_dir / safe_slug(user_id) / f"{safe_slug(thread_id)}.jsonl"
        if legacy_jsonl.exists():
            for line in legacy_jsonl.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        if limit is not None:
            return events[-limit:]
        return events

    def load_facts(self, user_id: str, thread_id: str) -> List[MemoryFact]:
        facts: List[MemoryFact] = []
        for event in self.load_events(user_id, thread_id):
            if event.get("type") == "fact":
                raw = event.get("fact") if isinstance(event.get("fact"), dict) else event
                facts.append(
                    MemoryFact(
                        kind=str(raw.get("kind", "")),
                        label=str(raw.get("label", "")),
                        value=str(raw.get("value", "")),
                        source_text=str(raw.get("source_text", "")),
                        user_id=str(raw.get("user_id", user_id)),
                        thread_id=str(raw.get("thread_id", thread_id)),
                        confidence=float(raw.get("confidence", 1.0)),
                        created_at=str(raw.get("created_at", "")),
                        aliases=tuple(raw.get("aliases", ()) or ()),
                    )
                )
        return facts

    def build_markdown_index(self, events: List[Dict[str, Any]]) -> str:
        buckets: Dict[str, List[str]] = {}
        for event in events:
            timestamp = str(event.get("timestamp", ""))
            label = event.get("type", "event")
            summary = summarize_event(event)
            tokens = tokenize(summary)
            for token in tokens:
                if token in STOP_WORDS:
                    continue
                buckets.setdefault(token, []).append(f"- {timestamp} | {label} | {summary}")

        lines = ["# Memory index", ""]
        if not buckets:
            lines.append("_No memory yet._")
            return "\n".join(lines).rstrip()

        for token in sorted(buckets):
            lines.append(f"## {token}")
            seen: Set[str] = set()
            for item in buckets[token]:
                if item in seen:
                    continue
                seen.add(item)
                lines.append(item)
            lines.append("")
        return "\n".join(lines).rstrip()

    def compact_thread(self, user_id: str, thread_id: str) -> Path:
        events = self.load_events(user_id, thread_id)
        index = self.build_markdown_index(events)
        path = self.thread_dir(user_id, thread_id) / "index.md"
        path.write_text(index, encoding="utf-8")
        return path

    def retrieve_memory_context(self, user_id: str, thread_id: str, query: str, limit: int = 5) -> MemoryContext:
        events = self.load_events(user_id, thread_id)
        facts = self.load_facts(user_id, thread_id)
        if not events and not facts:
            return MemoryContext(retrieval_query=normalize_text(query))

        ranked_events = self._rank_events(query, events, facts)
        selected_events = [event for event, _score in ranked_events[:limit] if _score > 0]

        selected_facts = self._rank_facts(query, facts)[:limit]
        selected_memory_facts = tuple(fact for fact, _score in selected_facts if _score > 0)

        parts: List[str] = []
        if selected_memory_facts:
            parts.extend(f"{fact.label}: {fact.value}" for fact in selected_memory_facts[:3])
        for event in selected_events[:3]:
            stamp = str(event.get("timestamp", ""))
            summary = summarize_event(event)
            if summary:
                parts.append(f"{stamp} | {summary}")
        
        thread_summary = " | ".join(parts[:6])

        return MemoryContext(
            facts=selected_memory_facts,
            thread_summary=thread_summary,
            retrieval_query=normalize_text(query),
            source_count=len(selected_events) + len(selected_memory_facts),
        )

    def _rank_events(self, query: str, events: Iterable[Dict], facts: Iterable[MemoryFact]) -> List[Tuple[Dict, int]]:
        tokens = {token for token in tokenize(query) if token not in STOP_WORDS}
        lower = query.casefold()
        scores: List[Tuple[Dict, int]] = []

        for event in events:
            summary = summarize_event(event)
            summary_lower = summary.casefold()
            score = 0
            if any(hint in lower for hint in NAVIGATION_HINTS):
                if "casa" in summary_lower or "home" in summary_lower:
                    score += 4
            if "casa" in lower and "casa" in summary_lower:
                score += 5
            if "cliente" in lower and "cliente" in summary_lower:
                score += 4
            if "recorda" in lower or "recuerda" in lower:
                score += 1
            for token in tokens:
                if token in summary_lower:
                    score += 1
            if event.get("type") == "fact":
                fact = event.get("fact") or {}
                if isinstance(fact, dict):
                    fact_text = f"{fact.get('label', '')} {fact.get('value', '')} {fact.get('source_text', '')}".casefold()
                    for token in tokens:
                        if token in fact_text:
                            score += 2
                    if fact.get("kind") == "home_address" and any(hint in lower for hint in NAVIGATION_HINTS):
                        score += 6
            if event.get("type") == "message":
                text = str(event.get("text", "")).casefold()
                if any(token in text for token in tokens):
                    score += 1
            scores.append((event, score))

        scores.sort(key=lambda item: (item[1], str(item[0].get("timestamp", ""))), reverse=True)
        return scores

    def _rank_facts(self, query: str, facts: Iterable[MemoryFact]) -> List[Tuple[MemoryFact, int]]:
        tokens = {token for token in tokenize(query) if token not in STOP_WORDS}
        lower = query.casefold()
        scored: List[Tuple[MemoryFact, int]] = []
        for fact in facts:
            score = 0
            haystacks = {fact.kind.casefold(), fact.label.casefold(), fact.value.casefold(), fact.source_text.casefold()}
            haystacks.update(alias.casefold() for alias in fact.aliases)

            if any(alias in lower for alias in fact.aliases):
                score += 5
            if fact.kind == "home_address" and any(hint in lower for hint in NAVIGATION_HINTS):
                score += 4
            if "mi casa" in lower and fact.kind == "home_address":
                score += 6
            if "cliente" in lower and fact.kind == "client_name":
                score += 4
            if "direccion" in lower and fact.kind in {"address", "home_address"}:
                score += 4
            if "recuerda" in lower and fact.value:
                score += 1

            value_tokens = set(tokenize(fact.value))
            label_tokens = set(tokenize(fact.label))
            if tokens & value_tokens:
                score += 2
            if tokens & label_tokens:
                score += 2
            source_tokens = {token for token in tokenize(fact.source_text) if token not in STOP_WORDS}
            if any(token in lower for token in source_tokens):
                score += 1
            if score == 0 and any(token in " ".join(sorted(haystacks)) for token in tokens):
                score += 1
            scored.append((fact, score))
        scored.sort(key=lambda item: (item[1], len(item[0].value)), reverse=True)
        return scored


class ThreadRegistry:
    """Persists the active conversational thread and known thread names."""

    def __init__(self, path: Optional[Path] = None) -> None:
        config = load_config()
        self.path = path or (config.workspace_root / "memory" / "threads.json")

    def current(self, user_id: str) -> str:
        state = self._load()
        user = state.get(str(user_id), {})
        return str(user.get("active") or user_id)

    def create(self, user_id: str, name: str) -> str:
        thread_id = safe_slug(name)
        state = self._load()
        user = state.setdefault(
            str(user_id),
            {"active": str(user_id), "threads": {}},
        )
        threads = user.setdefault("threads", {})
        threads[thread_id] = normalize_text(name)
        user["active"] = thread_id
        self._save(state)
        return thread_id

    def switch(self, user_id: str, name_or_id: str) -> Optional[str]:
        requested = safe_slug(name_or_id)
        state = self._load()
        user = state.get(str(user_id), {})
        threads = user.get("threads", {})
        if requested not in threads:
            match = next(
                (
                    thread_id
                    for thread_id, display in threads.items()
                    if safe_slug(str(display)) == requested
                ),
                None,
            )
            if match is None and requested != str(user_id):
                return None
            requested = match or requested
        user["active"] = requested
        state[str(user_id)] = user
        self._save(state)
        return requested

    def list(self, user_id: str) -> List[Tuple[str, str, bool]]:
        state = self._load()
        user = state.get(str(user_id), {})
        active = str(user.get("active") or user_id)
        threads = dict(user.get("threads", {}))
        threads.setdefault(str(user_id), "principal")
        return [
            (thread_id, str(display), thread_id == active)
            for thread_id, display in sorted(threads.items())
        ]

    def _load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except Exception:
            return {}

    def _save(self, state: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(state, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.path)
