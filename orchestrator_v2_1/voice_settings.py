from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_SETTINGS_PATH = Path("orchestrator_v2_1/runtime/voice_settings.json")


@dataclass(frozen=True)
class VoiceSettings:
    generate_audio: bool = True
    play_audio: bool = True
    provider: str = "edge"
    voice_name: str = "es-ES-ElviraNeural"
    summarize_above_chars: int = 700
    warm_on_startup: bool = True
    comparison_enabled: bool = False
    comparison_provider: str = "elevenlabs"
    comparison_voice_name: str = "Laura"


def load_voice_settings(path: Path = DEFAULT_SETTINGS_PATH) -> VoiceSettings:
    if not path.exists():
        save_voice_settings(VoiceSettings(), path)
        return VoiceSettings()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return VoiceSettings()
    return VoiceSettings(
        generate_audio=bool(payload.get("generate_audio", True)),
        play_audio=bool(payload.get("play_audio", True)),
        provider=str(payload.get("provider", "edge")),
        voice_name=str(payload.get("voice_name", "es-ES-ElviraNeural")),
        summarize_above_chars=int(payload.get("summarize_above_chars", 700)),
        warm_on_startup=bool(payload.get("warm_on_startup", True)),
        comparison_enabled=bool(payload.get("comparison_enabled", False)),
        comparison_provider=str(payload.get("comparison_provider", "elevenlabs")),
        comparison_voice_name=str(payload.get("comparison_voice_name", "Laura")),
    )


def save_voice_settings(settings: VoiceSettings, path: Path = DEFAULT_SETTINGS_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(settings), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
