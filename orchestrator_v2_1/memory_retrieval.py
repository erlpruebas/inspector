from __future__ import annotations

from typing import Iterable

from .memory_store import MemoryStore, normalize_text, summarize_event, tokenize
from .models import MemoryContext, MemoryFact


NAVIGATION_HINTS = (
    "como llego",
    "como ir",
    "ruta",
    "direccion",
    "mapa",
    "google maps",
    "desde mi casa",
    "ir a",
    "llevarme",
    "navegar",
)


def retrieve_memory_context(
    user_id: str,
    thread_id: str,
    query: str,
    *,
    store: MemoryStore | None = None,
    limit: int = 5,
) -> MemoryContext:
    store = store or MemoryStore()
    events = store.load_events(user_id, thread_id)
    facts = store.load_facts(user_id, thread_id)
    if not events and not facts:
        return MemoryContext(retrieval_query=normalize_text(query))

    ranked_events = rank_events(query, events, facts)
    selected_events = [event for event, _score in ranked_events[:limit] if _score > 0]
    if not selected_events:
        selected_events = list(events[-limit:])

    selected_facts = rank_facts(query, facts)[:limit]
    selected_memory_facts = tuple(fact for fact, _score in selected_facts if _score > 0)
    if not selected_memory_facts:
        selected_memory_facts = tuple(facts[-limit:])

    thread_summary = summarize_context(selected_events, selected_memory_facts)
    return MemoryContext(
        facts=selected_memory_facts,
        thread_summary=thread_summary,
        retrieval_query=normalize_text(query),
        source_count=len(events) or len(facts),
    )


def rank_events(query: str, events: Iterable[dict], facts: Iterable[MemoryFact]) -> list[tuple[dict, int]]:
    tokens = set(tokenize(query))
    lower = query.casefold()
    scores: list[tuple[dict, int]] = []

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


def rank_facts(query: str, facts: Iterable[MemoryFact]) -> list[tuple[MemoryFact, int]]:
    tokens = set(tokenize(query))
    lower = query.casefold()
    scored: list[tuple[MemoryFact, int]] = []
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
        if any(token in lower for token in tokenize(fact.source_text)):
            score += 1
        if score == 0 and any(token in " ".join(sorted(haystacks)) for token in tokens):
            score += 1
        scored.append((fact, score))
    scored.sort(key=lambda item: (item[1], len(item[0].value)), reverse=True)
    return scored


def summarize_context(events: list[dict], facts: tuple[MemoryFact, ...]) -> str:
    parts: list[str] = []
    if facts:
        parts.extend(f"{fact.label}: {fact.value}" for fact in facts[:3])
    for event in events[:3]:
        stamp = str(event.get("timestamp", ""))
        summary = summarize_event(event)
        if summary:
            parts.append(f"{stamp} | {summary}")
    return " | ".join(parts[:6])
