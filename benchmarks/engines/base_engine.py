from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class EngineResult:
    engine: str
    task_id: str
    returncode: int
    stdout: str
    stderr: str
    output_files: list[str] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    timed_out: bool = False
    usage: dict[str, Any] = field(default_factory=dict)
    model: str = ""
    error_type: str = ""
    retry_after_seconds: int = 0

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.timed_out


class Engine(Protocol):
    name: str
    model: str

    def run(self, task_id: str, prompt: str, workdir: Path, expected_outputs: list[str]) -> EngineResult:
        ...
