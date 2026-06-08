from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class Attachment(BaseModel):
    """Archivo adjunto que puede viajar con una petición."""

    kind: str
    path: Path
    label: str
    source: str = "user"


class TaskRequest(BaseModel):
    """Petición base que usan el router, la cola y los ejecutores."""

    request_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: Optional[str] = None
    thread_id: Optional[str] = None
    text: str = ""
    capability: str = ""
    tool_name: str = ""
    format: str = ""
    operation: str = ""
    payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    attachments: List[Attachment] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CapabilityRequest(TaskRequest):
    """Alias compatible con la nomenclatura anterior."""


class RouteDecision(BaseModel):
    """Decisión de enrutado producida por el selector."""

    model_config = {"protected_namespaces": ()}

    tool_id: str
    tier: str
    reason: str
    alternatives: List[str] = Field(default_factory=list)
    privacy_mode: str = "clear"
    model_id: Optional[str] = None


class OperationTimings(BaseModel):
    """Tiempos por fase para trazas y evaluación."""

    transcription_seconds: float = 0.0
    memory_seconds: float = 0.0
    routing_seconds: float = 0.0
    execution_seconds: float = 0.0
    voice_seconds: float = 0.0
    total_seconds: float = 0.0


class OrchestratorResult(BaseModel):
    """Resultado canónico que usan router, fallback y trazas."""

    ok: bool
    tool_id: str
    tier: str
    output: str = ""
    error: Optional[str] = None
    elapsed_seconds: float = 0.0
    privacy_mode: str = "clear"
    workdir: Optional[Path] = None
    timings: Optional[OperationTimings] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionResult(BaseModel):
    """
    Resultado de ejecución compatibile con algunas pruebas y utilidades antiguas.
    """

    success: bool
    output: str
    error: Optional[str] = None
    execution_time_ms: int = 0
