from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from math import sqrt
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .experience import ExperienceStore, RouterExperience


@dataclass
class CapabilityCell:
    tool_id: str
    capability: str
    task_shape: str
    samples: int
    pass_rate: float
    mean_score: float
    mean_seconds: float
    stdev_seconds: float
    confidence: float
    judge_samples: int


@dataclass
class CapabilityMatrixReport:
    total_experiences: int
    total_cells: int
    cells: List[CapabilityCell] = field(default_factory=list)
    by_tool: Dict[str, int] = field(default_factory=dict)
    by_capability: Dict[str, int] = field(default_factory=dict)
    by_shape: Dict[str, int] = field(default_factory=dict)

    def to_markdown(self) -> str:
        lines = [f"# Learned capability matrix ({self.total_cells} cells)", ""]
        lines.append(f"- experiences: {self.total_experiences}")
        lines.append("")
        lines.append("## Tool coverage")
        for key, count in sorted(self.by_tool.items()):
            lines.append(f"- {key}: {count}")
        lines.append("")
        lines.append("## Capability coverage")
        for key, count in sorted(self.by_capability.items()):
            lines.append(f"- {key}: {count}")
        lines.append("")
        lines.append("## Task shapes")
        for key, count in sorted(self.by_shape.items()):
            lines.append(f"- {key}: {count}")
        lines.append("")
        lines.append("## Sample cells")
        for cell in sorted(self.cells, key=lambda item: (-item.samples, item.tool_id, item.capability, item.task_shape))[:20]:
            lines.append(
                f"- {cell.tool_id} | {cell.capability} | {cell.task_shape}: "
                f"samples={cell.samples}, pass={cell.pass_rate:.2f}, "
                f"score={cell.mean_score:.2f}, latency={cell.mean_seconds:.2f}s, "
                f"stdev={cell.stdev_seconds:.2f}s, confidence={cell.confidence:.2f}"
            )
        return "\n".join(lines)


class CapabilityMatrixBuilder:
    """Aggregates router experiences into a learned capability matrix."""

    def __init__(self, experience_store: Optional[ExperienceStore] = None) -> None:
        self.experience_store = experience_store or ExperienceStore()

    def build(self, experiences: Optional[Iterable[RouterExperience]] = None) -> CapabilityMatrixReport:
        records = list(experiences) if experiences is not None else self.experience_store.load()
        cells = self._aggregate_cells(records)
        by_tool = Counter(cell.tool_id for cell in cells)
        by_capability = Counter(cell.capability for cell in cells)
        by_shape = Counter(cell.task_shape for cell in cells)
        return CapabilityMatrixReport(
            total_experiences=len(records),
            total_cells=len(cells),
            cells=cells,
            by_tool=dict(by_tool),
            by_capability=dict(by_capability),
            by_shape=dict(by_shape),
        )

    def _aggregate_cells(self, experiences: List[RouterExperience]) -> List[CapabilityCell]:
        groups: Dict[Tuple[str, str, str], List[RouterExperience]] = defaultdict(list)
        for experience in experiences:
            capabilities = self._capabilities_for_experience(experience)
            for capability in capabilities:
                groups[(experience.tool_id, capability, experience.task_shape)].append(experience)

        cells: List[CapabilityCell] = []
        for (tool_id, capability, task_shape), group in groups.items():
            scores = [self._score_from_experience(experience) for experience in group]
            seconds = [experience.elapsed_seconds for experience in group]
            pass_rate = sum(1 for experience in group if self._passed(experience)) / len(group)
            score_values = [score for score in scores if score is not None]
            judge_samples = len(score_values)
            mean_score = mean(score_values) if score_values else 0.0
            mean_seconds = mean(seconds) if seconds else 0.0
            stdev_seconds = self._stdev(seconds)
            confidence = min(1.0, len(group) / 10.0)
            cells.append(
                CapabilityCell(
                    tool_id=tool_id,
                    capability=capability,
                    task_shape=task_shape,
                    samples=len(group),
                    pass_rate=pass_rate,
                    mean_score=mean_score,
                    mean_seconds=mean_seconds,
                    stdev_seconds=stdev_seconds,
                    confidence=confidence,
                    judge_samples=judge_samples,
                )
            )
        return cells

    def _capabilities_for_experience(self, experience: RouterExperience) -> List[str]:
        capabilities: List[str] = []
        metadata_primary = str(experience.metadata.get("primary_capability") or "").strip()
        if metadata_primary:
            capabilities.append(metadata_primary)
        for item in experience.required_capabilities:
            if item:
                capabilities.append(str(item))
        if not capabilities and experience.objective_checks.get("capability"):
            capabilities.append(str(experience.objective_checks["capability"]))
        return self._unique(capabilities)

    def _score_from_experience(self, experience: RouterExperience) -> Optional[float]:
        if not experience.judge_scores:
            return None
        scores = []
        for item in experience.judge_scores:
            if isinstance(item, dict):
                value = item.get("score")
            else:
                value = getattr(item, "score", None)
            if isinstance(value, (int, float)):
                scores.append(float(value))
        if not scores:
            return None
        return mean(scores)

    def _passed(self, experience: RouterExperience) -> bool:
        passed = experience.objective_checks.get("passed")
        return bool(passed) or experience.outcome == "sufficient"

    def _stdev(self, values: List[float]) -> float:
        if len(values) < 2:
            return 0.0
        avg = mean(values)
        variance = sum((value - avg) ** 2 for value in values) / (len(values) - 1)
        return sqrt(variance)

    def _unique(self, values: List[str]) -> List[str]:
        seen: set[str] = set()
        result: List[str] = []
        for value in values:
            key = value.casefold()
            if key in seen:
                continue
            seen.add(key)
            result.append(value)
        return result

