from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from ..config import load_config
from .audit import TaskAuditReport, TaskAuditor
from .coverage import CoverageReport, TaskCoverageAnalyzer
from .experience import BenchmarkExperienceImporter, ExperienceStore
from .benchmark_runner import BenchmarkRunner
from .matrix import CapabilityMatrixBuilder, CapabilityMatrixReport
from .maturity import MaturityGate, MaturityReport
from .normalization import NormalizedTaskReport, TaskNormalizer
from .readiness import HITLReadinessGate, HITLReadinessReport
from .training_coverage import TrainingCoverageAnalyzer, TrainingCoverageReport
from .training_plan import TrainingPlan, TrainingPlanner


@dataclass
class EvolutionStatus:
    active: bool
    reason: str
    maturity: MaturityReport
    audit: TaskAuditReport


class EvolutionController:
    """Controla la auditoría de tareas y la activación del sistema evolutivo."""

    def __init__(self, workspace_root: Optional[Path] = None, parity_matrix_path: Optional[Path] = None) -> None:
        config = load_config()
        self.workspace_root = (workspace_root or config.workspace_root).resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.parity_matrix_path = parity_matrix_path or (Path(__file__).resolve().parents[3] / "docs" / "FUNCTIONAL_PARITY_MATRIX.md")
        self.state_path = self.workspace_root / "evolution_state.json"
        self.experience_store = ExperienceStore(
            self.workspace_root / "evolution" / "experiences.jsonl",
            bootstrap_seed=True,
        )
        self.benchmark_importer = BenchmarkExperienceImporter()
        self.matrix_builder = CapabilityMatrixBuilder(self.experience_store)
        self.benchmark_runner = BenchmarkRunner(workspace_root=self.workspace_root / "arena")

    def audit_tasks(self, task_paths: Optional[Iterable[Path]] = None) -> TaskAuditReport:
        paths = [Path(path) for path in (task_paths or [])]
        auditor = TaskAuditor(paths)
        if paths:
            return auditor.audit_paths(paths)
        root = Path(__file__).resolve().parents[4] / "benchmarks" / "tasks"
        return auditor.audit(root)

    def normalize_tasks(self, task_paths: Optional[Iterable[Path]] = None) -> NormalizedTaskReport:
        paths = [Path(path) for path in (task_paths or [])]
        normalizer = TaskNormalizer()
        if paths:
            auditor = TaskAuditor(paths)
            return normalizer.normalize_records(auditor.load_records(paths))
        root = Path(__file__).resolve().parents[4] / "benchmarks" / "tasks"
        return normalizer.normalize_path(root)

    def coverage(self) -> CoverageReport:
        root = Path(__file__).resolve().parents[4] / "benchmarks" / "tasks"
        return TaskCoverageAnalyzer().analyze(root)

    def evaluate_maturity(self) -> MaturityReport:
        return MaturityGate(self.parity_matrix_path).evaluate()

    def _save_state(self, payload: dict) -> None:
        self.state_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def activate(self, task_paths: Optional[Iterable[Path]] = None) -> EvolutionStatus:
        audit = self.audit_tasks(task_paths)
        maturity = self.evaluate_maturity()
        readiness = self.readiness()
        active = readiness.ready
        reason = (
            "Sistema evolutivo activado"
            if active
            else "Sistema evolutivo bloqueado por el gate HITL: "
            + "; ".join(readiness.reasons)
        )
        self._save_state(
            {
                "active": active,
                "reason": reason,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "maturity": {
                    "total_items": maturity.total_items,
                    "completed_items": maturity.completed_items,
                    "pending_items": maturity.pending_items,
                    "completion_ratio": maturity.completion_ratio,
                    "critical_pending": maturity.critical_pending,
                },
                "audit_tasks": audit.total_tasks,
                "readiness": {
                    "ready": readiness.ready,
                    "reasons": readiness.reasons,
                    "metrics": readiness.metrics,
                },
            }
        )
        return EvolutionStatus(active=active, reason=reason, maturity=maturity, audit=audit)

    def status(self) -> EvolutionStatus:
        if self.state_path.exists():
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
            active = bool(payload.get("active", False))
            reason = str(payload.get("reason", ""))
        else:
            active = False
            reason = "Sistema evolutivo no activado"
        audit = self.audit_tasks()
        maturity = self.evaluate_maturity()
        return EvolutionStatus(active=active, reason=reason, maturity=maturity, audit=audit)

    def import_benchmark_experiences(self) -> int:
        return self.benchmark_importer.import_all(self.experience_store)

    def capability_matrix(self) -> CapabilityMatrixReport:
        return self.matrix_builder.build()

    def training_coverage(self) -> TrainingCoverageReport:
        normalized = self.normalize_tasks()
        matrix = self.capability_matrix()
        return TrainingCoverageAnalyzer().analyze(normalized.records, matrix)

    def training_plan(self, *, samples_per_pair: int = 3) -> TrainingPlan:
        normalized = self.normalize_tasks()
        coverage = TrainingCoverageAnalyzer().analyze(
            normalized.records,
            self.capability_matrix(),
        )
        return TrainingPlanner(samples_per_pair=samples_per_pair).build(
            normalized.records,
            coverage,
        )

    def run_benchmark_arena(
        self,
        task_paths: Optional[Iterable[Path]] = None,
        limit: Optional[int] = None,
        tool_ids: Optional[list[str]] = None,
        all_compatible_tools: bool = False,
        task_ids: Optional[list[str]] = None,
    ):
        if task_paths:
            root_paths = [Path(path) for path in task_paths]
            if len(root_paths) == 1 and root_paths[0].is_dir():
                path = root_paths[0]
            else:
                path = root_paths[0]
        else:
            path = Path(__file__).resolve().parents[4] / "benchmarks" / "tasks"
        return self.benchmark_runner.run_arena(
            path,
            limit=limit,
            tool_ids=tool_ids,
            all_compatible_tools=all_compatible_tools,
            task_ids=task_ids,
        )

    def readiness(self) -> HITLReadinessReport:
        audit = self.audit_tasks()
        maturity = self.evaluate_maturity()
        coverage = self.coverage()
        return HITLReadinessGate(
            audit=audit,
            maturity=maturity,
            experience_store=self.experience_store,
            coverage=coverage,
        ).evaluate()
