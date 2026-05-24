from __future__ import annotations

from dataclasses import dataclass

from .settings import UserPreferences


@dataclass(frozen=True)
class ConfigQuestion:
    key: str
    prompt: str
    expected: str


CONFIG_TRIGGER_PHRASES = (
    "vamos a configurar",
    "quiero configurar",
    "modo configuracion",
    "configura el gestor",
)


QUESTIONS: tuple[ConfigQuestion, ...] = (
    ConfigQuestion("display_name", "Que nombre quieres que use contigo?", "texto corto"),
    ConfigQuestion("conversation_human_level", "De 0 a 5, cuanto de humana quieres la conversacion?", "numero 0-5"),
    ConfigQuestion("proactivity_level", "De 0 a 5, cuanto de proactivo quieres que sea el gestor?", "numero 0-5"),
    ConfigQuestion("quiet_start", "Desde que hora debe dejar de mandar mensajes no solicitados?", "HH:MM"),
    ConfigQuestion("quiet_end", "A que hora puede volver a mandar mensajes no solicitados?", "HH:MM"),
    ConfigQuestion("speaker_enabled", "Quieres que las respuestas suenen por el altavoz del ordenador?", "si/no"),
    ConfigQuestion("always_confirm_voice_orders", "Quieres confirmar siempre las ordenes dictadas por voz antes de ejecutarlas?", "si/no"),
    ConfigQuestion("privacy_default", "Privacidad por defecto: ask, redacted, mixed o clear?", "opcion"),
    ConfigQuestion("voice_response_enabled", "Quieres recibir siempre audio sintetizado ademas del texto en Telegram?", "si/no"),
)


def is_config_request(text: str) -> bool:
    lower = text.casefold()
    return any(phrase in lower for phrase in CONFIG_TRIGGER_PHRASES)


def apply_config_answer(preferences: UserPreferences, key: str, answer: str) -> UserPreferences:
    value = answer.strip()
    if key == "display_name":
        preferences.display_name = value
    elif key == "conversation_human_level":
        preferences.conversation_human_level = clamp_0_5(value)
    elif key == "proactivity_level":
        preferences.proactivity_level = clamp_0_5(value)
    elif key == "quiet_start":
        preferences.quiet_hours.start = value
    elif key == "quiet_end":
        preferences.quiet_hours.end = value
    elif key == "speaker_enabled":
        preferences.voice.speaker_enabled = parse_bool(value)
    elif key == "always_confirm_voice_orders":
        preferences.always_confirm_voice_orders = parse_bool(value)
    elif key == "privacy_default":
        preferences.privacy_default = value if value in {"ask", "redacted", "mixed", "clear"} else "ask"
    elif key == "voice_response_enabled":
        preferences.voice.voice_response_enabled = parse_bool(value)
    return preferences


def clamp_0_5(raw: str) -> int:
    try:
        return max(0, min(5, int(raw)))
    except ValueError:
        return 3


def parse_bool(raw: str) -> bool:
    return raw.strip().casefold() in {"si", "s", "yes", "y", "true", "1", "on", "encendido"}
