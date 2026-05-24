from __future__ import annotations

import re


DEFAULT_LONG_VOICE_THRESHOLD_CHARS = 900
DEFAULT_VOICE_SUMMARY_MAX_CHARS = 650


def needs_voice_summary(text: str, threshold_chars: int = DEFAULT_LONG_VOICE_THRESHOLD_CHARS) -> bool:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    return len(text) > threshold_chars or len(paragraphs) > 2


def summarize_for_voice(text: str, max_chars: int = DEFAULT_VOICE_SUMMARY_MAX_CHARS) -> str:
    """Deterministic fallback summary until a model summary step is wired in."""

    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) <= max_chars:
        return clean
    sentences = re.split(r"(?<=[.!?])\s+", clean)
    picked: list[str] = []
    total = 0
    for sentence in sentences:
        if not sentence:
            continue
        next_total = total + len(sentence) + 1
        if next_total > max_chars:
            break
        picked.append(sentence)
        total = next_total
    summary = " ".join(picked).strip()
    if not summary:
        summary = clean[: max_chars - 1].rstrip() + "..."
    return (
        f"Te resumo la respuesta para no mandarte un audio largo: {summary} "
        "Si quieres, dime 'leeme la respuesta completa' y te la leo entera."
    )


def voice_text_for_response(text: str, threshold_chars: int = 900, max_chars: int = 650) -> str:
    if not needs_voice_summary(text, threshold_chars):
        return text.strip()
    return summarize_for_voice(text, max_chars)
