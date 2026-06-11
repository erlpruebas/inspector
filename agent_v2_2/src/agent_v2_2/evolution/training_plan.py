from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List

from .audit import fixture_validation_error
from .normalization import NormalizedTask
from .training_coverage import TrainingCoverageReport, TrainingPair


@dataclass(frozen=True)
class PlannedRun:
    tool_id: str
    capability: str
    task_id: str
    source_path: Path
    priority: int
    reason: str


@dataclass
class TrainingPlan:
    runs: List[PlannedRun] = field(default_factory=list)
    unresolved_pairs: List[TrainingPair] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = [
            "# Evolutionary router training plan",
            "",
            f"- planned runs: {len(self.runs)}",
            f"- unresolved pairs: {len(self.unresolved_pairs)}",
            "",
            "## Runs",
        ]
        for run in self.runs:
            lines.append(
                f"- P{run.priority} {run.tool_id} | {run.capability} | "
                f"{run.task_id} | `{run.source_path}`: {run.reason}"
            )
        if self.unresolved_pairs:
            lines.extend(["", "## Pairs without a valid task"])
            for pair in self.unresolved_pairs:
                lines.append(f"- {pair.tool_id} | {pair.capability}")
        return "\n".join(lines)


class TrainingPlanner:
    def __init__(self, *, samples_per_pair: int = 3) -> None:
        self.samples_per_pair = max(1, samples_per_pair)

    def build(
        self,
        tasks: Iterable[NormalizedTask],
        coverage: TrainingCoverageReport,
    ) -> TrainingPlan:
        records = list(tasks)
        runs: List[PlannedRun] = []
        unresolved: List[TrainingPair] = []
        for pair in coverage.missing_training():
            candidates = [
                task
                for task in records
                if task.primary_capability == pair.capability
                and pair.tool_id in task.compatible_tools
                and self._is_valid_candidate(task)
            ]
            candidates.sort(key=self._candidate_rank)
            candidates = self._unique_tasks(candidates)
            needed = max(
                0,
                self.samples_per_pair - pair.live_samples,
                self.samples_per_pair - pair.judge_samples,
            )
            if not pair.demonstrated:
                needed = max(1, needed)
            selected = candidates[:needed]
            if not selected:
                unresolved.append(pair)
                continue
            for task in selected:
                priority = 1 if not pair.demonstrated else 2
                runs.append(
                    PlannedRun(
                        tool_id=pair.tool_id,
                        capability=pair.capability,
                        task_id=task.task_id,
                        source_path=task.source_path,
                        priority=priority,
                        reason=(
                            "first passing blind-judge demonstration"
                            if priority == 1
                            else "raise sample confidence to three"
                        ),
                    )
                )
        return TrainingPlan(runs=runs, unresolved_pairs=unresolved)

    def _unique_tasks(self, tasks: List[NormalizedTask]) -> List[NormalizedTask]:
        selected: List[NormalizedTask] = []
        seen: set[str] = set()
        for task in tasks:
            if task.task_id in seen:
                continue
            seen.add(task.task_id)
            selected.append(task)
        return selected

    def _is_valid_candidate(self, task: NormalizedTask) -> bool:
        prompt = task.prompt.casefold()
        if task.requires_network and (
            ".example" in prompt
            or "simulada" in prompt
            or "simulado" in prompt
            or "captura web actual simulada" in prompt
        ):
            return False
        if task.requires_network:
            for relative in task.required_files:
                path = self._resolve_file(relative)
                if path is None:
                    return False
                try:
                    content = path.read_text(
                        encoding="utf-8",
                        errors="replace",
                    ).casefold()
                except OSError:
                    return False
                if ".example" in content or "simulada" in content:
                    return False
        if not task.objective_checks and not task.judge_rubric:
            return False
        for relative in task.required_files:
            path = self._resolve_file(relative)
            if path is None or fixture_validation_error(path):
                return False
        return True

    def _candidate_rank(self, task: NormalizedTask) -> tuple:
        objective_count = len(task.objective_checks)
        file_count = len(task.required_files)
        level = self._level_number(str(task.dimensions.get("level") or ""))
        return (
            0 if objective_count else 1,
            file_count,
            level,
            task.task_id,
            str(task.source_path),
        )

    def _resolve_file(self, relative: str) -> Path | None:
        candidates = (
            Path.cwd() / relative,
            Path.cwd() / "benchmarks" / "assets" / relative,
            Path.cwd() / "benchmarks" / "tasks" / relative,
        )
        return next((path for path in candidates if path.exists()), None)

    def _level_number(self, value: str) -> int:
        digits = "".join(character for character in value if character.isdigit())
        return int(digits) if digits else 99
