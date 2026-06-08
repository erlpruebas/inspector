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
from .maturity import MaturityGate, MaturityReport
from .readiness import HITLReadinessGate, HITLReadinessReport


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
        self.experience_store = ExperienceStore(self.workspace_root / "evolution" / "experiences.jsonl")
        self.benchmark_importer = BenchmarkExperienceImporter()

    def audit_tasks(self, task_paths: Optional[Iterable[Path]] = None) -> TaskAuditReport:
        auditor = TaskAuditor(task_paths)
        if task_paths:
            return auditor.audit_paths(task_paths)
        root = Path(__file__).resolve().parents[4] / "benchmarks" / "tasks"
        return auditor.audit(root)

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
        active = maturity.mature and audit.total_tasks >= 10
        reason = "Sistema evolutivo activado" if active else "Aún no hay madurez suficiente para activar el sistema evolutivo"
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
