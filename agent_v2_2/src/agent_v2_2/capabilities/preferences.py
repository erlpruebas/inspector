from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from ..config import load_config


class PreferenceState(BaseModel):
    voice_enabled: bool = False
    speaker_enabled: bool = False
    voice_provider: str = "edge"
    voice_name: str = ""
    anonymization_enabled: bool = False
    development_mode_enabled: bool = False


class PreferenceStore:
    def __init__(self, path: Optional[Path] = None) -> None:
        config = load_config()
        self.path = path or (config.workspace_root / "agent_preferences.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> PreferenceState:
        if not self.path.exists():
            return PreferenceState()
        try:
            return PreferenceState.model_validate_json(self.path.read_text(encoding="utf-8"))
        except Exception:
            return PreferenceState()

    def save(self, state: PreferenceState) -> PreferenceState:
        self.path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
        return state

    def update(self, **changes) -> PreferenceState:
        state = self.load().model_copy(update=changes)
        return self.save(state)

    def toggle_voice(self, enabled: Optional[bool] = None) -> PreferenceState:
        state = self.load()
        value = (not state.voice_enabled) if enabled is None else bool(enabled)
        return self.save(state.model_copy(update={"voice_enabled": value}))

    def toggle_speaker(self, enabled: Optional[bool] = None) -> PreferenceState:
        state = self.load()
        value = (not state.speaker_enabled) if enabled is None else bool(enabled)
        return self.save(state.model_copy(update={"speaker_enabled": value}))

    def set_voice_provider(self, provider: str) -> PreferenceState:
        provider = provider.strip().casefold()
        if provider not in {"edge", "gemini", "elevenlabs"}:
            raise ValueError("Proveedor de voz no soportado.")
        return self.update(voice_provider=provider)

    def set_voice_name(self, voice_name: str) -> PreferenceState:
        return self.update(voice_name=voice_name.strip())

    def set_anonymization(self, enabled: bool) -> PreferenceState:
        return self.update(anonymization_enabled=bool(enabled))

    def set_development_mode(self, enabled: bool) -> PreferenceState:
        return self.update(development_mode_enabled=bool(enabled))

