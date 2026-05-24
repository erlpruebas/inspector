from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import json


@dataclass
class QuietHours:
    start: str = "22:00"
    end: str = "08:00"
    timezone: str = "Europe/Madrid"


@dataclass
class VoiceSettings:
    local_button_enabled: bool = True
    local_whisper_model: str = "large-v3"
    stt_primary: str = "local_whisper_large_v3"
    stt_fallback: str = "groq_whisper_large_v3_turbo"
    tts_primary: str = "gemini"
    speaker_enabled: bool = False
    voice_response_enabled: bool = True
    long_voice_threshold_chars: int = 900
    voice_summary_max_chars: int = 650


@dataclass
class UserPreferences:
    user_id: str
    display_name: str = ""
    conversation_human_level: int = 3
    proactivity_level: int = 2
    quiet_hours: QuietHours = field(default_factory=QuietHours)
    voice: VoiceSettings = field(default_factory=VoiceSettings)
    always_confirm_voice_orders: bool = True
    privacy_default: str = "ask"


def load_user_preferences(path: Path, user_id: str) -> UserPreferences:
    if not path.exists():
        return UserPreferences(user_id=user_id)
    data = json.loads(path.read_text(encoding="utf-8"))
    quiet = QuietHours(**data.get("quiet_hours", {}))
    voice = VoiceSettings(**data.get("voice", {}))
    return UserPreferences(
        user_id=data.get("user_id", user_id),
        display_name=data.get("display_name", ""),
        conversation_human_level=int(data.get("conversation_human_level", 3)),
        proactivity_level=int(data.get("proactivity_level", 2)),
        quiet_hours=quiet,
        voice=voice,
        always_confirm_voice_orders=bool(data.get("always_confirm_voice_orders", True)),
        privacy_default=data.get("privacy_default", "ask"),
    )


def save_user_preferences(path: Path, preferences: UserPreferences) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(preferences), indent=2, ensure_ascii=False), encoding="utf-8")
