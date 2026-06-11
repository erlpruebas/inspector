from __future__ import annotations

import json
import re
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import HumanConfirmation, MemoryContext, MemoryFact, OrchestratorResult, RouteDecision, TaskRequest


PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_RUNTIME_ROOT = PACKAGE_ROOT / "runtime"
DEFAULT_MEMORY_ROOT = DEFAULT_RUNTIME_ROOT / "memory"
DEFAULT_STATE_ROOT = DEFAULT_RUNTIME_ROOT / "state"

STOP_WORDS = {
    "a",
    "al",
    "algo",
    "as",
    "bajo",
    "con",
    "como",
    "cual",
    "de",
    "del",
    "desde",
    "el",
    "ella",
    "ellos",
    "en",
    "entre",
    "era",
    "es",
    "esta",
    "está",
    "esto",
    "esto",
    "la",
    "las",
    "le",
    "les",
    "lo",
    "los",
    "mi",
    "mis",
    "no",
    "o",
    "para",
    "por",
    "que",
    "qué",
    "se",
    "si",
    "sí",
    "su",
    "sus",
    "te",
    "un",
    "una",
    "y",
    "ya",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9._-]+", "_", value.casefold())
    return slug.strip("_") or "default"


def fact_aliases(kind: str, label: str) -> tuple[str, ...]:
    aliases = {kind.casefold(), label.casefold()}
    if "home" in kind or "casa" in label.casefold():
        aliases.update({"mi casa", "casa", "home", "direccion de mi casa", "dirección de mi casa"})
    if "address" in kind or "direccion" in label.casefold():
        aliases.update({"mi direccion", "mi dirección", "direccion", "dirección"})
    return tuple(sorted(aliases))


def extract_memory_facts(text: str, *, user_id: str, thread_id: str) -> tuple[MemoryFact, ...]:
    normalized = normalize_text(text)
    lower = normalized.casefold()
    facts: list[MemoryFact] = []

    patterns: list[tuple[str, str, list[str]]] = [
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


class MemoryStore:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = (base_dir or DEFAULT_MEMORY_ROOT).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def thread_dir(self, user_id: str, thread_id: str) -> Path:
        thread_dir = self.base_dir / safe_slug(user_id) / safe_slug(thread_id)
        (thread_dir / "raw").mkdir(parents=True, exist_ok=True)
        return thread_dir

    def raw_day_path(self, user_id: str, thread_id: str, *, timestamp: str | None = None) -> Path:
        timestamp = timestamp or now_iso()
        day = timestamp[:10]
        return self.thread_dir(user_id, thread_id) / "raw" / f"{day}.md"

    def index_path(self, user_id: str, thread_id: str) -> Path:
        return self.thread_dir(user_id, thread_id) / "index.md"

    def legacy_jsonl_path(self, user_id: str, thread_id: str) -> Path:
        return self.base_dir / safe_slug(user_id) / f"{safe_slug(thread_id)}.jsonl"

    def append_event(self, user_id: str, thread_id: str, event: dict[str, Any]) -> dict[str, Any]:
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

    def record_message(self, user_id: str, thread_id: str, role: str, text: str, *, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
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

    def record_fact(self, fact: MemoryFact) -> dict[str, Any]:
        return self.append_event(
            fact.user_id,
            fact.thread_id,
            {
                "type": "fact",
                "fact": asdict(fact),
            },
        )

    def record_interaction(
        self,
        request: TaskRequest,
        decision: RouteDecision,
        result: OrchestratorResult | None,
        *,
        human_confirmation: HumanConfirmation | None = None,
        memory_context: MemoryContext | None = None,
    ) -> None:
        self.record_message(
            request.user_id,
            request.thread_id,
            "user",
            request.text,
            metadata={
                "request_id": request.request_id,
                "privacy_mode": request.privacy_mode,
            },
        )

        for fact in extract_memory_facts(request.text, user_id=request.user_id, thread_id=request.thread_id):
            self.record_fact(fact)

        self.append_event(
            request.user_id,
            request.thread_id,
            {
                "type": "decision",
                "request_id": request.request_id,
                "tool_id": decision.tool_id,
                "tier": decision.tier,
                "reason": decision.reason,
                "privacy_mode": decision.privacy_mode,
                "memory_retrieval_query": memory_context.retrieval_query if memory_context else "",
                "memory_fact_labels": [fact.label for fact in (memory_context.facts if memory_context else ())],
            },
        )

        if result is None:
            return

        self.append_event(
            request.user_id,
            request.thread_id,
            {
                "type": "result",
                "request_id": request.request_id,
                "ok": result.ok,
                "tool_id": result.tool_id,
                "tier": result.tier,
                "output": result.output,
                "error": result.error,
                "privacy_mode": result.privacy_mode,
                "requires_human_confirmation": result.requires_human_confirmation,
                "human_confirmation": asdict(human_confirmation) if human_confirmation else None,
                "attachments": [
                    {
                        "kind": attachment.kind,
                        "path": str(attachment.path),
                        "label": attachment.label,
                        "source": attachment.source,
                    }
                    for attachment in result.attachments
                ],
            },
        )

    def load_events(self, user_id: str, thread_id: str, *, limit: int | None = None) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        raw_dir = self.thread_dir(user_id, thread_id) / "raw"
        if raw_dir.exists():
            for path in sorted(raw_dir.glob("*.md")):
                events.extend(parse_markdown_events(path.read_text(encoding="utf-8")))

        legacy_jsonl = self.legacy_jsonl_path(user_id, thread_id)
        if legacy_jsonl.exists():
            events.extend(parse_legacy_jsonl(legacy_jsonl.read_text(encoding="utf-8")))

        if limit is not None:
            return events[-limit:]
        return events

    def load_facts(self, user_id: str, thread_id: str) -> list[MemoryFact]:
        facts: list[MemoryFact] = []
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

    def compact_thread(self, user_id: str, thread_id: str) -> Path:
        events = self.load_events(user_id, thread_id)
        index = build_markdown_index(events)
        path = self.index_path(user_id, thread_id)
        path.write_text(index, encoding="utf-8")
        return path


def render_event_markdown(event: dict[str, Any]) -> str:
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


def parse_markdown_events(text: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
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
                items: list[str] = []
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


def parse_legacy_jsonl(text: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def build_markdown_index(events: list[dict[str, Any]]) -> str:
    buckets: dict[str, list[str]] = {}
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
        seen: set[str] = set()
        for item in buckets[token]:
            if item in seen:
                continue
            seen.add(item)
            lines.append(item)
        lines.append("")
    return "\n".join(lines).rstrip()


def summarize_event(event: dict[str, Any]) -> str:
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


def tokenize(text: str) -> tuple[str, ...]:
    return tuple(
        token
        for token in re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+", text.casefold())
        if len(token) > 1
    )
