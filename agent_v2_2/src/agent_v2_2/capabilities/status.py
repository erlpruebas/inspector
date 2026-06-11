from __future__ import annotations

import os
import json
import shutil
import time
from typing import Dict

from .preferences import PreferenceStore
from ..scheduling.codex_quota import CodexQuotaMonitor
from ..config import load_config


class StatusManager:
    """Reports operational state without exposing memory contents or counts."""

    def __init__(self) -> None:
        self.start_time = time.time()

    def get_uptime(self) -> float:
        return time.time() - self.start_time

    def get_api_status(self) -> Dict[str, bool]:
        return {
            "Telegram": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
            "Groq": bool(os.getenv("GROQ_API_KEY")),
            "OpenRouter": bool(os.getenv("OPENROUTER_API_KEY")),
            "Gemini": bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
            "ElevenLabs": bool(os.getenv("ELEVENLABS_API_KEY")),
        }

    def get_cli_status(self) -> Dict[str, bool]:
        return {
            "Codex CLI": bool(shutil.which("codex") or shutil.which("codex.exe")),
            "Gemini CLI": bool(shutil.which("gemini") or shutil.which("gemini.cmd")),
            "OpenCode": bool(shutil.which("opencode") or shutil.which("opencode.exe")),
        }

    def get_feature_flags(self) -> Dict[str, bool]:
        preferences = PreferenceStore().load()
        evolution_path = load_config().workspace_root / "evolution_state.json"
        try:
            evolution = json.loads(evolution_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            evolution = {}
        return {
            "Generacion de audio": preferences.voice_enabled,
            "Altavoz": preferences.speaker_enabled,
            "Anonimizacion": preferences.anonymization_enabled,
            "Modo desarrollo": preferences.development_mode_enabled,
            "Router evolutivo": bool(evolution.get("active")),
        }

    def get_configuration(self) -> Dict[str, str]:
        preferences = PreferenceStore().load()
        return {
            "Proveedor de voz": preferences.voice_provider,
            "Voz": preferences.voice_name or "predeterminada",
            "Privacidad": "anonimizada" if preferences.anonymization_enabled else "clara",
        }

    def get_codex_quota(self) -> Dict[str, str]:
        monitor = CodexQuotaMonitor()
        snapshot = monitor.snapshot(refresh=True)
        if snapshot is None:
            return {"Estado": "no disponible"}
        return {
            "Ventana de cinco horas": f"{snapshot.five_hour_remaining}% disponible",
            "Reinicio de cinco horas": self._format_timestamp(
                snapshot.five_hour_resets_at
            ),
            "Ventana semanal": f"{snapshot.weekly_remaining}% disponible",
            "Reinicio semanal": self._format_timestamp(snapshot.weekly_resets_at),
            "Rutas Codex": (
                "disponibles"
                if monitor.can_schedule_codex()
                else "pausadas por reserva"
            ),
        }

    def generate_status_report(self) -> str:
        uptime = self.get_uptime()
        hours, rem = divmod(uptime, 3600)
        minutes, seconds = divmod(rem, 60)

        api_status = self.get_api_status()
        cli_status = self.get_cli_status()
        feature_flags = self.get_feature_flags()
        configuration = self.get_configuration()
        codex_quota = self.get_codex_quota()

        lines = [
            "**Estado de Agent 2.2**",
            f"Runtime: activo ({int(hours)}h {int(minutes)}m {int(seconds)}s)",
            "",
            "**APIs**",
        ]
        lines.extend(self._format_switch(name, enabled) for name, enabled in api_status.items())
        lines.extend(["", "**Herramientas locales**"])
        lines.extend(self._format_switch(name, enabled) for name, enabled in cli_status.items())
        lines.extend(["", "**Configuracion**"])
        lines.extend(self._format_switch(name, enabled) for name, enabled in feature_flags.items())
        lines.extend(f"- {name}: {value}" for name, value in configuration.items())
        lines.extend(["", "**Cuota Codex**"])
        lines.extend(f"- {name}: {value}" for name, value in codex_quota.items())
        return "\n".join(lines)

    def generate_provider_diagnostics(self) -> str:
        lines = ["**Diagnostico de proveedores**", "", "**APIs configuradas**"]
        lines.extend(
            self._format_switch(name, enabled)
            for name, enabled in self.get_api_status().items()
        )
        lines.extend(["", "**CLI detectadas**"])
        lines.extend(
            self._format_switch(name, enabled)
            for name, enabled in self.get_cli_status().items()
        )
        lines.extend(
            [
                "",
                "Este diagnostico comprueba configuracion y ejecutables; "
                "no muestra claves ni consume una peticion de prueba.",
            ]
        )
        return "\n".join(lines)

    def _format_switch(self, name: str, enabled: bool) -> str:
        return f"- {name}: {'on' if enabled else 'off'}"

    def _format_timestamp(self, value: int | None) -> str:
        if value is None:
            return "desconocido"
        return time.strftime("%Y-%m-%d %H:%M", time.localtime(value))
