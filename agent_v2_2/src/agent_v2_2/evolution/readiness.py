from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from ..capabilities.catalog import create_default_catalog
from .audit import TaskAuditReport
from .coverage import CoverageReport, TaskCoverageAnalyzer
from .experience import ExperienceStore
from .matrix import CapabilityMatrixBuilder
from .maturity import MaturityReport
from .normalization import TaskNormalizer
from .training_coverage import TrainingCoverageAnalyzer


@dataclass
class HITLReadinessReport:
    ready: bool
    reasons: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)

    def to_markdown(self) -> str:
        lines = [
            "# HITL readiness report",
            "",
            f"- ready: {'yes' if self.ready else 'no'}",
            "",
            "## Reasons",
        ]
        lines.extend(f"- {reason}" for reason in self.reasons)
        if not self.reasons:
            lines.append("- none")
        lines.extend(["", "## Metrics"])
        for key, value in sorted(self.metrics.items()):
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)


class HITLReadinessGate:
    """Strict gate for starting real human-in-the-loop trials."""

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
        all_experiences = self.experience_store.load()
        experiences = [
            item
            for item in all_experiences
            if str(item.metadata.get("evidence_kind", "historical"))
            not in {"simulated", "unavailable", "queued"}
            and not bool(item.metadata.get("evidence_invalidated"))
        ]
        judged_experiences = sum(
            1 for item in experiences if self._has_valid_judgement(item.judge_scores)
        )
        sufficient_experiences = sum(
            1 for item in experiences if item.outcome == "sufficient"
        )
        shape_coverage = len(
            {item.task_shape for item in experiences if item.task_shape}
        )
        coverage = self.coverage or TaskCoverageAnalyzer().analyze(
            Path.cwd() / "benchmarks" / "tasks"
        )

        catalog = create_default_catalog()
        eligible_tools = {
            tool.tool_id
            for tool in catalog.tools
            if tool.selection_eligible and tool.tool_id != "local_direct"
        }
        operational_capabilities = {
            capability.id for capability in catalog.capabilities
        }
        matrix = CapabilityMatrixBuilder(self.experience_store).build(experiences)
        normalized_tasks = TaskNormalizer().normalize_audit(self.audit)
        training = TrainingCoverageAnalyzer().analyze(
            normalized_tasks.records,
            matrix,
        )
        learned_tools = {
            cell.tool_id for cell in matrix.cells if cell.live_samples > 0
        }
        judged_capabilities = {
            cell.capability
            for cell in matrix.cells
            if cell.live_judge_samples > 0 and cell.live_samples > 0
        }
        missing_tools = sorted(eligible_tools - learned_tools)
        missing_capabilities = sorted(
            operational_capabilities - judged_capabilities
        )

        reasons: List[str] = []
        if self.audit.total_tasks < 25:
            reasons.append(
                f"Only {self.audit.total_tasks} audited tasks; at least 25 are required."
            )
        if self.audit.invalid_files:
            preview = ", ".join(sorted(self.audit.invalid_files)[:5])
            reasons.append(
                f"{len(self.audit.invalid_files)} benchmark fixtures are missing or "
                f"invalid: {preview}"
            )
        if not self.maturity.mature:
            reasons.append("Functional parity is not mature.")
        if len(experiences) < 50:
            reasons.append(
                f"Only {len(experiences)} valid experiences; at least 50 are required."
            )
        if judged_experiences < 10:
            reasons.append(
                f"Only {judged_experiences} judged experiences; at least 10 are required."
            )
        if shape_coverage < 5:
            reasons.append(
                f"Only {shape_coverage} task shapes are covered; at least 5 are required."
            )
        if missing_tools:
            reasons.append(
                "Missing valid evidence for selectable tools: "
                + ", ".join(missing_tools)
            )
        if missing_capabilities:
            reasons.append(
                "Missing judged operational capabilities: "
                + ", ".join(missing_capabilities)
            )
        missing_pairs = training.missing_demonstrations()
        if missing_pairs:
            preview = ", ".join(
                f"{pair.tool_id}/{pair.capability}" for pair in missing_pairs[:8]
            )
            suffix = "..." if len(missing_pairs) > 8 else ""
            reasons.append(
                f"{len(missing_pairs)} tool-capability pairs lack a passing "
                f"live blind-judge demonstration: {preview}{suffix}"
            )
        if len(coverage.missing_buckets()) > 3:
            reasons.append(
                "Too many file-format gaps remain: "
                + ", ".join(coverage.missing_buckets()[:5])
            )
        if len(coverage.levels) < 3:
            reasons.append("The battery does not cover enough difficulty levels.")

        metrics = {
            "tasks": float(self.audit.total_tasks),
            "experiences": float(len(experiences)),
            "excluded_experiences": float(len(all_experiences) - len(experiences)),
            "judged_experiences": float(judged_experiences),
            "sufficient_experiences": float(sufficient_experiences),
            "tool_coverage": float(len(learned_tools & eligible_tools)),
            "required_tool_coverage": float(len(eligible_tools)),
            "judged_capability_coverage": float(
                len(judged_capabilities & operational_capabilities)
            ),
            "required_capability_coverage": float(
                len(operational_capabilities)
            ),
            "shape_coverage": float(shape_coverage),
            "completion_ratio": float(self.maturity.completion_ratio),
            "format_coverage": float(len(coverage.file_buckets)),
            "missing_buckets": float(len(coverage.missing_buckets())),
            "expected_training_pairs": float(training.expected_pairs),
            "demonstrated_training_pairs": float(training.demonstrated_pairs),
            "trained_training_pairs": float(training.trained_pairs),
        }
        ready = not reasons
        if ready:
            reasons.append(
                "The router, evidence matrix and task battery are ready for real HITL trials."
            )
        return HITLReadinessReport(
            ready=ready,
            reasons=reasons,
            metrics=metrics,
        )

    def _has_valid_judgement(self, judgements: List[dict]) -> bool:
        for judgement in judgements:
            if not isinstance(judgement, dict):
                continue
            score = judgement.get("score")
            capability_scores = judgement.get("capability_scores")
            if isinstance(capability_scores, dict) and capability_scores:
                return True
            if (
                isinstance(score, (int, float))
                and (
                    str(judgement.get("judge") or "").casefold() != "unknown"
                    or bool(str(judgement.get("comment") or "").strip())
                )
            ):
                return True
        return False
