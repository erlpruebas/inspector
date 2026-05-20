from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
TASKS_FILE = ROOT / "tasks" / "tasks.json"
ASSETS_DIR = ROOT / "assets"
RESULTS_DIR = ROOT / "results"


@dataclass(frozen=True)
class BenchmarkTask:
    id: str
    prompt: str
    required_files: list[str] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    requires_network: bool = False
    level: str = ""
    category: str = ""
    rubric: dict[str, int] = field(default_factory=dict)
    skills: list[str] = field(default_factory=list)
    expected_keys: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "BenchmarkTask":
        return cls(
            id=str(raw["id"]),
            prompt=str(raw["prompt"]),
            required_files=[str(item) for item in raw.get("required_files", [])],
            expected_outputs=[str(item) for item in raw.get("expected_outputs", [])],
            requires_network=bool(raw.get("requires_network", False)),
            level=str(raw.get("level", "")),
            category=str(raw.get("category", "")),
            rubric={str(key): int(value) for key, value in (raw.get("rubric") or {}).items()},
            skills=[str(item) for item in raw.get("skills", [])],
            expected_keys=[str(item) for item in raw.get("expected_keys", [])],
        )


def load_tasks(path: Path = TASKS_FILE) -> list[BenchmarkTask]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"{path} must contain a JSON list")
    return [BenchmarkTask.from_dict(item) for item in raw]


def prepare_workdir(task: BenchmarkTask, engine_name: str, run_id: str, clean: bool = True) -> Path:
    return prepare_workdir_in_root(RESULTS_DIR / run_id, task, engine_name, clean=clean)


def prepare_workdir_in_root(root: Path, task: BenchmarkTask, engine_name: str, clean: bool = True) -> Path:
    workdir = root / "work" / engine_name / task.id
    if clean and workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True, exist_ok=True)

    for filename in task.required_files:
        source = ASSETS_DIR / filename
        if not source.exists():
            raise FileNotFoundError(f"Missing benchmark asset: {source}")
        target = workdir / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    return workdir


def prefixed_result_name(engine_name: str, task_id: str, filename: str) -> str:
    return f"{engine_name}_{task_id}_{filename}"
