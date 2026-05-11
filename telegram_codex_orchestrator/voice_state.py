from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class VoiceState:
    voz: bool = False
    altavoz: bool = False
    tts_backend: str = "groq"
    tts_fallback_order: list[str] | None = None
    groq_api_key: str = ""
    groq_model: str = "canopylabs/orpheus-v1-english"
    groq_voice: str = "troy"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash-preview-tts"
    gemini_voice: str = "Kore"
    kokoro_voice: str = "ef_dora"
    piper_voice: str = "es_ES-davefx-medium"

    def normalized_order(self) -> list[str]:
        order = self.tts_fallback_order or ["groq", "kokoro", "piper"]
        cleaned: list[str] = []
        for item in order:
            backend = str(item).strip().lower()
            if backend in {"groq", "gemini", "kokoro", "piper"} and backend not in cleaned:
                cleaned.append(backend)
        for backend in ("groq", "kokoro", "piper"):
            if backend not in cleaned:
                cleaned.append(backend)
        return cleaned


class VoiceStateStore:
    def __init__(self, path: Path, default_google_api_key: str = "", default_groq_api_key: str = "") -> None:
        self.path = path
        self.default_google_api_key = default_google_api_key
        self.default_groq_api_key = default_groq_api_key

    def load(self) -> VoiceState:
        raw: dict[str, Any] = {}
        if self.path.exists():
            try:
                parsed = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(parsed, dict):
                    raw = parsed
            except (OSError, json.JSONDecodeError):
                raw = {}
        state = VoiceState(
            voz=bool(raw.get("voz", False)),
            altavoz=bool(raw.get("altavoz", False)),
            tts_backend=str(raw.get("tts_backend", "groq") or "groq").lower(),
            tts_fallback_order=list(raw.get("tts_fallback_order", ["groq", "kokoro", "piper"])),
            groq_api_key=str(raw.get("groq_api_key", "") or ""),
            groq_model=str(raw.get("groq_model", "canopylabs/orpheus-v1-english") or "canopylabs/orpheus-v1-english"),
            groq_voice=str(raw.get("groq_voice", "troy") or "troy"),
            gemini_api_key=str(raw.get("gemini_api_key", "") or ""),
            gemini_model=str(raw.get("gemini_model", "gemini-2.5-flash-preview-tts") or "gemini-2.5-flash-preview-tts"),
            gemini_voice=str(raw.get("gemini_voice", "Kore") or "Kore"),
            kokoro_voice=str(raw.get("kokoro_voice", "ef_dora") or "ef_dora"),
            piper_voice=str(raw.get("piper_voice", "es_ES-davefx-medium") or "es_ES-davefx-medium"),
        )
        if not state.gemini_api_key:
            state.gemini_api_key = self.default_google_api_key
        if not state.groq_api_key:
            state.groq_api_key = self.default_groq_api_key
        if state.tts_backend not in {"groq", "gemini", "kokoro", "piper"}:
            state.tts_backend = "groq"
        if state.altavoz:
            state.voz = True
        return state

    def save(self, state: VoiceState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        state.tts_fallback_order = state.normalized_order()
        if state.altavoz:
            state.voz = True
        self.path.write_text(json.dumps(asdict(state), indent=2, ensure_ascii=False), encoding="utf-8")
