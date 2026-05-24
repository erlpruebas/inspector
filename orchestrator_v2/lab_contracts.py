from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal


SpeedMode = Literal["fixed", "jitter", "burst"]
TransportMode = Literal["dry_run", "telegram_group_bots", "telegram_user_sessions"]


@dataclass(frozen=True)
class ProfessionContract:
    id: str
    title: str
    description: str
    scope: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    evaluation_dimensions: tuple[str, ...] = ()
    output_standard: str = ""
    root: Path | None = None


@dataclass(frozen=True)
class TaskContract:
    id: str
    title: str
    prompt: str
    profession_id: str
    difficulty: int = 2
    level: str = "L2"
    category: str = ""
    skills: tuple[str, ...] = ()
    required_files: tuple[Path, ...] = ()
    expected_keys: tuple[str, ...] = ()
    response_shape: str = "respuesta util y trazable"
    rubric: dict[str, Any] = field(default_factory=dict)
    reference: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LabPersona:
    id: str
    name: str
    profession: str
    description: str = ""
    tone: str = ""
    risk: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BotSlot:
    id: str
    persona_id: str
    transport: TransportMode = "dry_run"
    token_env: str = ""
    chat_id_env: str = ""
    enabled: bool = True


@dataclass(frozen=True)
class LabActivation:
    id: str
    profession_id: str
    task_ids: tuple[str, ...] = ()
    persona_ids: tuple[str, ...] = ()
    speed_seconds: float = 60.0
    speed_mode: SpeedMode = "fixed"
    transport: TransportMode = "dry_run"
    max_tasks: int | None = None
    evidence_dir: Path = Path("orchestrator_v2/runtime/lab_runs")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence_dir"] = str(self.evidence_dir)
        return data


@dataclass(frozen=True)
class ScheduledLabMessage:
    activation_id: str
    sequence: int
    persona: LabPersona
    task: TaskContract
    delay_seconds: float
    transport: TransportMode

    def to_evidence(self) -> dict[str, Any]:
        return {
            "activation_id": self.activation_id,
            "sequence": self.sequence,
            "persona_id": self.persona.id,
            "persona_name": self.persona.name,
            "profession": self.persona.profession,
            "task_id": self.task.id,
            "task_title": self.task.title,
            "delay_seconds": self.delay_seconds,
            "transport": self.transport,
            "prompt": self.task.prompt,
            "required_files": [str(path) for path in self.task.required_files],
            "expected_keys": list(self.task.expected_keys),
        }
