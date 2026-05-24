from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal


PrivacyMode = Literal["ask", "clear", "mixed", "redacted"]
ToolKind = Literal["api_directa", "cli_agentico", "runtime_agentico", "desktop_operator"]


@dataclass(frozen=True)
class Herramienta:
    id: str
    engine: str
    kind: ToolKind
    role: str
    description: str
    strengths: tuple[str, ...] = ()
    weaknesses: tuple[str, ...] = ()
    cost_level: str = "medium"
    reliability: str = "candidate"


@dataclass(frozen=True)
class TaskRequest:
    text: str
    user_id: str = "local"
    thread_id: str = "default"
    files: tuple[Path, ...] = ()
    privacy_mode: PrivacyMode = "ask"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class UserMessage:
    """Normalized input coming from Telegram, local voice, CLI, or the lab."""

    text: str
    user_id: str
    thread_id: str = "default"
    source: Literal["telegram", "local_voice", "cli", "lab"] = "cli"
    files: tuple[Path, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RouteDecision:
    tool_id: str
    reason: str
    privacy_mode: PrivacyMode
    needs_privacy_confirmation: bool = False
    alternatives: tuple[str, ...] = ()


@dataclass(frozen=True)
class OrchestratorResult:
    ok: bool
    tool_id: str
    engine: str
    output: str
    workdir: Path
    elapsed_seconds: float
    privacy_mode: str
    error: str = ""
