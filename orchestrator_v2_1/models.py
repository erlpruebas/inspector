from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal


PrivacyMode = Literal["ask", "clear", "mixed", "redacted"]
ToolChannel = Literal["local", "api", "agentic_cli", "desktop"]
AttachmentKind = Literal["image", "json", "markdown", "text", "directory"]


@dataclass(frozen=True)
class MemoryFact:
    kind: str
    label: str
    value: str
    source_text: str = ""
    user_id: str = "local"
    thread_id: str = "default"
    confidence: float = 1.0
    created_at: str = ""
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class MemoryContext:
    facts: tuple[MemoryFact, ...] = ()
    thread_summary: str = ""
    retrieval_query: str = ""
    source_count: int = 0


@dataclass(frozen=True)
class HumanConfirmation:
    title: str
    message: str
    action: str = ""
    risk: str = ""
    reply_hint: str = "si/no"


@dataclass(frozen=True)
class TaskRequest:
    text: str
    request_id: str = ""
    user_id: str = "local"
    thread_id: str = "default"
    files: tuple[Path, ...] = ()
    privacy_mode: PrivacyMode = "ask"
    memory_context: MemoryContext = field(default_factory=MemoryContext)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolSpec:
    id: str
    tier: int
    channel: ToolChannel
    engine: str
    role: str
    description: str
    requires_confirmation: bool = False


@dataclass(frozen=True)
class RouteDecision:
    tool_id: str
    tier: int
    reason: str
    privacy_mode: PrivacyMode
    needs_privacy_confirmation: bool = False
    alternatives: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResultAttachment:
    kind: AttachmentKind
    path: Path
    label: str = ""
    source: str = ""


@dataclass(frozen=True)
class OperationTimings:
    memory_seconds: float = 0
    routing_seconds: float = 0
    execution_seconds: float = 0
    total_seconds: float = 0


@dataclass(frozen=True)
class OrchestratorResult:
    ok: bool
    tool_id: str
    tier: int
    engine: str
    output: str
    workdir: Path
    elapsed_seconds: float
    privacy_mode: str
    requires_human_confirmation: bool = False
    human_confirmation: HumanConfirmation | None = None
    attachments: tuple[ResultAttachment, ...] = ()
    error: str = ""
    timings: OperationTimings = field(default_factory=OperationTimings)
