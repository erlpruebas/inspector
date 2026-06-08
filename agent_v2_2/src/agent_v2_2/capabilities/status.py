from __future__ import annotations

import os
import time
from typing import Dict


class StatusManager:
    def __init__(self) -> None:
        self.start_time = time.time()

    def get_uptime(self) -> float:
        return time.time() - self.start_time

    def get_api_status(self) -> Dict[str, bool]:
        return {
            "telegram": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
            "groq": bool(os.getenv("GROQ_API_KEY")),
            "gemini": bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
            "elevenlabs": bool(os.getenv("ELEVENLABS_API_KEY")),
        }

    def get_feature_flags(self) -> Dict[str, bool]:
        return {
            "voz": os.getenv("VOICE_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"},
            "altavoz": os.getenv("SPEAKER_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"},
            "anonimización": os.getenv("ANONYMIZATION_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"},
            "modo desarrollo": os.getenv("DEV_MODE_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"},
        }

    def generate_status_report(self) -> str:
        uptime = self.get_uptime()
        hours, rem = divmod(uptime, 3600)
        minutes, seconds = divmod(rem, 60)

        api_status = self.get_api_status()
        feature_flags = self.get_feature_flags()
        missing_apis = [k for k, v in api_status.items() if not v]

        lines = [
            "📊 **Estado de Antigravity (Agent v2.2)**",
            f"⏱️ Uptime: {int(hours)}h {int(minutes)}m {int(seconds)}s",
            "",
            "🔌 **APIs Configuradas:**",
        ]

        for api, is_configured in api_status.items():
            icon = "✅" if is_configured else "❌"
            lines.append(f"{icon} {api.capitalize()}")

        lines.extend(["", "⚙️ **Funciones:**"])
        for feature, enabled in feature_flags.items():
            icon = "✅" if enabled else "❌"
            lines.append(f"{icon} {feature}")

        if missing_apis:
            lines.append("")
            lines.append("⚠️ **Advertencia:** Faltan claves API esenciales que podrían limitar capacidades.")

        return "\n".join(lines)
