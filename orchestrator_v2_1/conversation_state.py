from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .models import HumanConfirmation, MemoryContext, RouteDecision, TaskRequest
from .memory_store import DEFAULT_STATE_ROOT


CONFIRM_YES = {"si", "sí", "confirmo", "adelante", "vale", "ok", "okay", "continua", "continuar"}
CONFIRM_NO = {"no", "cancela", "cancelar", "para", "stop", "detente"}
HITL_PATTERNS = (
    "enviar a",
    "enviar mensaje",
    "mandar mensaje",
    "publicar",
    "publica",
    "borrar",
    "borra",
    "eliminar",
    "elimina",
    "comprar",
    "compra",
    "pagar",
    "paga",
    "transferir",
    "cambiar configuración",
    "cambiar configuracion",
    "login",
    "iniciar sesión",
    "iniciar sesion",
    "2fa",
    "captcha",
    "credencial",
    "contraseña",
    "password",
    "sesion abierta",
    "sesión abierta",
)

def state_path(user_id: str, thread_id: str) -> Path:
    root = (DEFAULT_STATE_ROOT / safe_slug(user_id)).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{safe_slug(thread_id)}.json"


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9._-]+", "_", value.casefold())
    return slug.strip("_") or "default"


def load_state(user_id: str, thread_id: str) -> dict[str, Any]:
    path = state_path(user_id, thread_id)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_state(user_id: str, thread_id: str, state: dict[str, Any]) -> None:
    path = state_path(user_id, thread_id)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def clear_pending_confirmation(user_id: str, thread_id: str) -> None:
    state = load_state(user_id, thread_id)
    state.pop("pending_confirmation", None)
    save_state(user_id, thread_id, state)


def set_pending_confirmation(
    user_id: str,
    thread_id: str,
    request: TaskRequest,
    decision: RouteDecision,
    confirmation: HumanConfirmation,
) -> None:
    state = load_state(user_id, thread_id)
    state["pending_confirmation"] = {
        "request": serialize_task_request(request),
        "decision": serialize_route_decision(decision),
        "confirmation": asdict(confirmation),
    }
    save_state(user_id, thread_id, state)


def get_pending_confirmation(user_id: str, thread_id: str) -> dict[str, Any] | None:
    state = load_state(user_id, thread_id)
    pending = state.get("pending_confirmation")
    return pending if isinstance(pending, dict) else None


def is_confirmation_yes(text: str) -> bool:
    return normalize_reply(text) in CONFIRM_YES


def is_confirmation_no(text: str) -> bool:
    return normalize_reply(text) in CONFIRM_NO


def normalize_reply(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def should_require_human_confirmation(text: str) -> tuple[bool, str]:
    lower = normalize_reply(text)
    if any(pattern in lower for pattern in HITL_PATTERNS):
        return True, "Action may be risky, sensitive, or irreversible."
    return False, ""


def serialize_task_request(request: TaskRequest) -> dict[str, Any]:
    return {
        "text": request.text,
        "request_id": request.request_id,
        "user_id": request.user_id,
        "thread_id": request.thread_id,
        "files": [str(path) for path in request.files],
        "privacy_mode": request.privacy_mode,
        "memory_context": serialize_memory_context(request.memory_context),
        "metadata": request.metadata,
    }


def deserialize_task_request(payload: dict[str, Any]) -> TaskRequest:
    return TaskRequest(
        text=str(payload.get("text", "")),
        request_id=str(payload.get("request_id", "")),
        user_id=str(payload.get("user_id", "local")),
        thread_id=str(payload.get("thread_id", "default")),
        files=tuple(Path(item) for item in payload.get("files", []) or []),
        privacy_mode=str(payload.get("privacy_mode", "ask")),
        memory_context=deserialize_memory_context(payload.get("memory_context") or {}),
        metadata=dict(payload.get("metadata", {}) or {}),
    )


def serialize_route_decision(decision: RouteDecision) -> dict[str, Any]:
    return asdict(decision)


def deserialize_route_decision(payload: dict[str, Any]) -> RouteDecision:
    return RouteDecision(
        tool_id=str(payload.get("tool_id", "")),
        tier=int(payload.get("tier", 1)),
        reason=str(payload.get("reason", "")),
        privacy_mode=str(payload.get("privacy_mode", "ask")),
        needs_privacy_confirmation=bool(payload.get("needs_privacy_confirmation", False)),
        alternatives=tuple(payload.get("alternatives", ()) or ()),
    )


def serialize_memory_context(memory_context: MemoryContext) -> dict[str, Any]:
    return asdict(memory_context)


def deserialize_memory_context(payload: dict[str, Any]) -> MemoryContext:
    from .models import MemoryFact

    facts = []
    for item in payload.get("facts", []) or []:
        if not isinstance(item, dict):
            continue
        facts.append(
            MemoryFact(
                kind=str(item.get("kind", "")),
                label=str(item.get("label", "")),
                value=str(item.get("value", "")),
                source_text=str(item.get("source_text", "")),
                user_id=str(item.get("user_id", "local")),
                thread_id=str(item.get("thread_id", "default")),
                confidence=float(item.get("confidence", 1.0)),
                created_at=str(item.get("created_at", "")),
                aliases=tuple(item.get("aliases", ()) or ()),
            )
        )
    return MemoryContext(
        facts=tuple(facts),
        thread_summary=str(payload.get("thread_summary", "")),
        retrieval_query=str(payload.get("retrieval_query", "")),
        source_count=int(payload.get("source_count", 0)),
    )


def build_human_confirmation(request: TaskRequest, decision: RouteDecision, reason: str) -> HumanConfirmation:
    return HumanConfirmation(
        title="Confirmacion humana requerida",
        message=(
            f"Esta accion puede ser sensible o irreversible.\n"
            f"Accion: {request.text}\n"
            f"Tier sugerido: {decision.tier} ({decision.tool_id})\n"
            f"Motivo: {reason}\n"
            "Responde 'si' para continuar o 'no' para cancelar."
        ),
        action=decision.tool_id,
        risk=reason,
    )
