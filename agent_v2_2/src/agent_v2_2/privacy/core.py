from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..config import load_config


class PrivacyLevels:
    CLEAR = "clear"
    MIXED = "mixed"
    REDACTED = "redacted"


def normalize_confirmation(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", (text or "").casefold())
    without_accents = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return " ".join(without_accents.strip().split()).strip(" .,!¡?¿")


def should_require_human_confirmation(text: str) -> Tuple[bool, Optional[str]]:
    normalized = normalize_confirmation(text)
    sensitive_markers = (
        (r"\b(?:borra|borrar|elimina|eliminar)\b", "borrado de datos"),
        (r"\b(?:envia|enviar|manda|mandar)\b", "envio de datos al exterior"),
        (r"\b(?:compra|comprar|paga|pagar)\b", "transaccion economica"),
        (r"\b(?:publica|publicar|sube|subir)\b", "publicacion externa"),
    )
    for pattern, reason in sensitive_markers:
        if re.search(pattern, normalized):
            return True, reason
    return False, None


def build_confirmation_message(tool_id: str, reason: str) -> str:
    return (
        "**Confirmacion necesaria**\n"
        f"- Accion: {reason}\n"
        f"- Herramienta prevista: {tool_id}\n\n"
        "Responde `si` para continuar o `no` para cancelar."
    )


def is_confirmation_yes(text: str) -> bool:
    return normalize_confirmation(text) in {
        "si",
        "yes",
        "s",
        "y",
        "confirmo",
        "adelante",
        "hazlo",
    }


def is_confirmation_no(text: str) -> bool:
    return normalize_confirmation(text) in {
        "no",
        "n",
        "cancela",
        "cancelar",
        "abortar",
    }


class ConfirmationStore:
    """Persists one pending sensitive action per Telegram chat."""

    def __init__(self, root: Optional[Path] = None) -> None:
        config = load_config()
        self.root = root or (config.workspace_root / "confirmations")

    def get(self, chat_id: int | str) -> Optional[Dict[str, Any]]:
        path = self._path(chat_id)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else None
        except Exception:
            return None

    def set(self, chat_id: int | str, payload: Dict[str, Any]) -> None:
        path = self._path(chat_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
        temporary.replace(path)

    def clear(self, chat_id: int | str) -> None:
        path = self._path(chat_id)
        if path.exists():
            path.unlink()

    def _path(self, chat_id: int | str) -> Path:
        safe = re.sub(r"[^A-Za-z0-9_-]+", "-", str(chat_id)).strip("-") or "chat"
        return self.root / f"{safe}.json"


class PrivacyManager:
    def __init__(self) -> None:
        self._user_modes: Dict[str, str] = {}

    def get_mode(self, user_id: str) -> str:
        return self._user_modes.get(user_id, PrivacyLevels.CLEAR)

    def set_mode(self, user_id: str, mode: str) -> None:
        if mode in {PrivacyLevels.CLEAR, PrivacyLevels.MIXED, PrivacyLevels.REDACTED}:
            self._user_modes[user_id] = mode


def redact_sensitive_text(text: str) -> str:
    """Redacts common personal and financial identifiers before provider calls."""

    patterns = (
        (
            r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]){10,30}\b",
            "[IBAN REDACTADO]",
        ),
        (
            r"\b[A-Z]\d{7}[A-Z0-9]\b",
            "[IDENTIFICADOR FISCAL REDACTADO]",
        ),
        (
            r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b",
            "[EMAIL REDACTADO]",
        ),
        (
            r"(?<!\d)(?:\+34[\s.-]?)?(?:[6789]\d{2}[\s.-]?\d{3}[\s.-]?\d{3})(?!\d)",
            "[TELEFONO REDACTADO]",
        ),
    )
    redacted = text
    for pattern, replacement in patterns:
        redacted = re.sub(pattern, replacement, redacted, flags=re.IGNORECASE)
    return redacted
