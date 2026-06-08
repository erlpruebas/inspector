import re
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass
from ..models import TaskRequest, RouteDecision

class PrivacyLevels:
    CLEAR = "clear"
    MIXED = "mixed"
    REDACTED = "redacted"

@dataclass
class HumanConfirmation:
    request: str
    decision_reason: str
    risk: str
    message: str

def should_require_human_confirmation(text: str) -> Tuple[bool, Optional[str]]:
    """
    Determina si la intención expresada en texto requiere confirmación humana obligatoria.
    """
    lower = text.casefold()
    sensitive_markers = [
        ("borra", "posible borrado de datos"),
        ("elimina", "posible borrado de datos"),
        ("envia", "envío de datos al exterior"),
        ("compra", "transacción económica"),
        ("paga", "transacción económica"),
        ("publica", "publicación externa")
    ]
    
    for marker, reason in sensitive_markers:
        if re.search(r'\b' + re.escape(marker) + r'\b', lower):
            return True, reason
    return False, None

def build_human_confirmation(request: TaskRequest, decision: RouteDecision, reason: str) -> HumanConfirmation:
    """
    Construye el objeto y mensaje de confirmación que el orquestador enviará.
    """
    message = (
        f"⚠️ Acción sensible detectada.\n"
        f"Se solicita confirmación para ejecutar mediante `{decision.tool_id}`.\n"
        f"Motivo: {reason}\n\n"
        f"Responde `sí` para confirmar o `no` para cancelar."
    )
    return HumanConfirmation(
        request=request.text,
        decision_reason=decision.reason,
        risk=reason,
        message=message
    )

def is_confirmation_yes(text: str) -> bool:
    return normalize_text(text).casefold() in {"si", "sí", "yes", "s", "y", "confirmo", "confirmar", "adelante", "hazlo"}

def is_confirmation_no(text: str) -> bool:
    return normalize_text(text).casefold() in {"no", "n", "cancela", "cancelar", "abortar"}

def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

class PrivacyManager:
    """Gestiona el estado de privacidad por usuario."""
    def __init__(self):
        self._user_modes: Dict[str, str] = {}
        
    def get_mode(self, user_id: str) -> str:
        return self._user_modes.get(user_id, PrivacyLevels.CLEAR)
        
    def set_mode(self, user_id: str, mode: str):
        if mode in {PrivacyLevels.CLEAR, PrivacyLevels.MIXED, PrivacyLevels.REDACTED}:
            self._user_modes[user_id] = mode
