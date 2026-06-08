from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .audit import TaskAuditReport
from .coverage import CoverageReport, TaskCoverageAnalyzer
from .experience import ExperienceStore
from .maturity import MaturityReport


@dataclass
class HITLReadinessReport:
    ready: bool
    reasons: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)

    def to_markdown(self) -> str:
        lines = ["# HITL readiness report", "", f"- ready: {'yes' if self.ready else 'no'}", ""]
        lines.append("## Reasons")
        if self.reasons:
            for reason in self.reasons:
                lines.append(f"- {reason}")
        else:
            lines.append("- none")
        lines.append("")
        lines.append("## Metrics")
        for key, value in sorted(self.metrics.items()):
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)


class HITLReadinessGate:
    def __init__(
        self,
        audit: TaskAuditReport,
        maturity: MaturityReport,
        experience_store: Optional[ExperienceStore] = None,
        coverage: Optional[CoverageReport] = None,
    ) -> None:
        self.audit = audit
        self.maturity = maturity
        self.experience_store = experience_store or ExperienceStore()
        self.coverage = coverage

    def evaluate(self) -> HITLReadinessReport:
        experiences = self.experience_store.load()
        total_experiences = len(experiences)
        judged_experiences = sum(1 for item in experiences if item.judge_scores)
        sufficient_experiences = sum(1 for item in experiences if item.outcome == "sufficient")
        tool_coverage = len({item.tool_id for item in experiences if item.tool_id})
        shape_coverage = len({item.task_shape for item in experiences if item.task_shape})
        coverage = self.coverage or TaskCoverageAnalyzer().analyze(Path.cwd() / "benchmarks" / "tasks")

        reasons: List[str] = []
        ready = True

        if self.audit.total_tasks < 25:
            ready = False
            reasons.append(f"Solo hay {self.audit.total_tasks} tareas auditadas; necesitamos al menos 25.")
        if not self.maturity.mature:
            ready = False
            reasons.append("La matriz de paridad aún no está madura.")
        if total_experiences < 50:
            ready = False
            reasons.append(f"Solo hay {total_experiences} experiencias importadas; necesitamos al menos 50.")
        if judged_experiences < 10:
            ready = False
            reasons.append(f"Solo hay {judged_experiences} experiencias con juez; necesitamos al menos 10.")
        if shape_coverage < 5:
            ready = False
            reasons.append(f"Solo hay {shape_coverage} formas de tarea cubiertas; necesitamos más variedad.")
        if tool_coverage < 3:
            ready = False
            reasons.append(f"Solo hay {tool_coverage} herramientas con experiencia; necesitamos más diversidad.")
        if len(coverage.missing_buckets()) > 3:
            ready = False
            reasons.append(
                "Todavía faltan demasiados formatos de archivo en la auditoría "
                f"({', '.join(coverage.missing_buckets()[:5])})."
            )
        if len(coverage.levels) < 3:
            ready = False
            reasons.append("La batería todavía no cubre suficientes niveles de dificultad.")

        metrics = {
            "tasks": float(self.audit.total_tasks),
            "experiences": float(total_experiences),
            "judged_experiences": float(judged_experiences),
            "sufficient_experiences": float(sufficient_experiences),
            "tool_coverage": float(tool_coverage),
            "shape_coverage": float(shape_coverage),
            "completion_ratio": float(self.maturity.completion_ratio),
            "format_coverage": float(len(coverage.file_buckets)),
            "missing_buckets": float(len(coverage.missing_buckets())),
        }
        if ready:
            reasons.append("Cobertura, madurez y experiencias suficientes para empezar comprobaciones HITL.")
        return HITLReadinessReport(ready=ready, reasons=reasons, metrics=metrics)
