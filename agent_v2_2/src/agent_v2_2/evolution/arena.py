from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Protocol, Sequence
from uuid import uuid4

from ..models import OperationTimings, OrchestratorResult, RouteDecision, TaskRequest
from ..routing.contract import RequestContract
from .experience import ExperienceStore, RouterExperience
from .normalization import NormalizedTask, NormalizedTaskReport, TaskNormalizer


class ArenaExecutor(Protocol):
    def __call__(
        self,
        task: NormalizedTask,
        tool_id: str,
        contract: RequestContract,
    ) -> OrchestratorResult: ...


class ArenaJudge(Protocol):
    def __call__(
        self,
        task: NormalizedTask,
        result: OrchestratorResult,
    ) -> Dict[str, object]: ...


@dataclass
class ArenaRunResult:
    task_id: str
    task_shape: str
    tool_id: str
    success: bool
    elapsed_seconds: float
    objective_checks: Dict[str, object]
    judge_scores: List[Dict[str, object]] = field(default_factory=list)
    outcome: str = "insufficient"
    failure_reason: Optional[str] = None


@dataclass
class ArenaReport:
    total_runs: int
    passed_runs: int
    tool_counts: Dict[str, int]
    shape_counts: Dict[str, int]
    average_seconds: float
    judge_count: int
    runs: List[ArenaRunResult] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = [f"# Benchmark arena report ({self.total_runs} runs)", ""]
        lines.append(f"- passed runs: {self.passed_runs}")
        lines.append(f"- average seconds: {self.average_seconds:.3f}")
        lines.append(f"- judge scores recorded: {self.judge_count}")
        lines.append("")
        lines.append("## Tools")
        for tool_id, count in sorted(self.tool_counts.items()):
            lines.append(f"- {tool_id}: {count}")
        lines.append("")
        lines.append("## Shapes")
        for shape, count in sorted(self.shape_counts.items()):
            lines.append(f"- {shape}: {count}")
        lines.append("")
        lines.append("## Sample runs")
        for run in self.runs[:10]:
            lines.append(
                f"- {run.task_id} -> {run.tool_id}: "
                f"{'pass' if run.success else 'fail'} ({run.elapsed_seconds:.3f}s)"
            )
        return "\n".join(lines)


class BenchmarkArena:
    """Runs normalized tasks against compatible tools and stores evidence."""

    def __init__(
        self,
        *,
        normalizer: Optional[TaskNormalizer] = None,
        experience_store: Optional[ExperienceStore] = None,
    ) -> None:
        self.normalizer = normalizer or TaskNormalizer()
        self.experience_store = experience_store or ExperienceStore()

    def run(
        self,
        tasks: Sequence[NormalizedTask],
        *,
        executor: ArenaExecutor,
        judge: Optional[ArenaJudge] = None,
        limit: Optional[int] = None,
    ) -> ArenaReport:
        runs: List[ArenaRunResult] = []
        selected_tasks = list(tasks[: limit or len(tasks)])
        for task in selected_tasks:
            contract = RequestContract.model_validate(task.contract)
            if not task.compatible_tools:
                continue
            tool_id = task.compatible_tools[0]
            started = datetime.now(timezone.utc)
            result = executor(task, tool_id, contract)
            elapsed = result.timings.total_seconds if result.timings else result.elapsed_seconds
            objective_checks = self._objective_checks(task, result)
            judge_scores = []
            if judge is not None:
                judgement = judge(task, result)
                judge_scores = [judgement]
            outcome = "sufficient" if result.ok and bool(result.output.strip()) and objective_checks.get("passed") else "insufficient"
            if judge_scores and any(float(score.get("score", 0.0)) < 5 for score in judge_scores if isinstance(score, dict)):
                outcome = "insufficient"
            run = ArenaRunResult(
                task_id=task.task_id,
                task_shape=task.task_shape,
                tool_id=tool_id,
                success=bool(result.ok and result.output.strip()),
                elapsed_seconds=float(elapsed),
                objective_checks=objective_checks,
                judge_scores=judge_scores,
                outcome=outcome,
                failure_reason=result.error,
            )
            runs.append(run)
            self.experience_store.append(
                RouterExperience(
                    experience_id=str(uuid4()),
                    timestamp=started.isoformat(),
                    catalog_version=4,
                    task_id=task.task_id,
                    task_shape=task.task_shape,
                    tool_id=tool_id,
                    required_capabilities=[item.value for item in contract.execute.instrumental_capabilities],
                    cognitive_requirements=[item.value for item in contract.execute.cognitive_requirements],
                    elapsed_seconds=float(elapsed),
                    objective_checks=objective_checks,
                    judge_scores=judge_scores,
                    outcome=outcome,
                    failure_reason=result.error,
                    metadata={
                        "task_title": task.title,
                        "primary_capability": task.primary_capability,
                        "secondary_capabilities": list(task.secondary_capabilities),
                        "compatible_tools": list(task.compatible_tools[:5]),
                    },
                )
            )
        return self._report(runs)

    def run_path(
        self,
        path: Path,
        *,
        executor: ArenaExecutor,
        judge: Optional[ArenaJudge] = None,
        limit: Optional[int] = None,
    ) -> ArenaReport:
        report = self.normalizer.normalize_path(path)
        return self.run(report.records, executor=executor, judge=judge, limit=limit)

    def _objective_checks(self, task: NormalizedTask, result: OrchestratorResult) -> Dict[str, object]:
        checks = [
            {"name": "non_empty_output", "passed": bool(result.output.strip()), "detail": ""},
        ]
        output = result.output.casefold()
        key_checks = []
        for item in task.objective_checks[:10]:
            if item.startswith("contains:"):
                expected = item.split(":", 1)[1]
                key_checks.append(
                    {
                        "name": item,
                        "passed": expected.casefold() in output,
                        "detail": expected,
                    }
                )
        checks.extend(key_checks)
        return {
            "passed": all(check["passed"] for check in checks),
            "checks": checks,
        }

    def _report(self, runs: List[ArenaRunResult]) -> ArenaReport:
        tool_counts = Counter(run.tool_id for run in runs)
        shape_counts = Counter(run.task_shape for run in runs)
        total_seconds = sum(run.elapsed_seconds for run in runs)
        passed = sum(1 for run in runs if run.success)
        judge_count = sum(len(run.judge_scores) for run in runs)
        average = (total_seconds / len(runs)) if runs else 0.0
        return ArenaReport(
            total_runs=len(runs),
            passed_runs=passed,
            tool_counts=dict(tool_counts),
            shape_counts=dict(shape_counts),
            average_seconds=average,
            judge_count=judge_count,
            runs=runs,
        )
