from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Tuple

from .matrix import CapabilityCell, CapabilityMatrixReport
from .normalization import NormalizedTask


@dataclass(frozen=True)
class TrainingPair:
    tool_id: str
    capability: str
    live_samples: int = 0
    judge_samples: int = 0
    pass_rate: float = 0.0
    mean_score: float = 0.0

    @property
    def demonstrated(self) -> bool:
        return (
            self.live_samples >= 1
            and self.judge_samples >= 1
            and self.pass_rate >= 0.7
            and self.mean_score >= 7.0
        )

    @property
    def trained(self) -> bool:
        return self.demonstrated and self.live_samples >= 3 and self.judge_samples >= 3


@dataclass
class TrainingCoverageReport:
    pairs: List[TrainingPair] = field(default_factory=list)

    @property
    def expected_pairs(self) -> int:
        return len(self.pairs)

    @property
    def demonstrated_pairs(self) -> int:
        return sum(1 for pair in self.pairs if pair.demonstrated)

    @property
    def trained_pairs(self) -> int:
        return sum(1 for pair in self.pairs if pair.trained)

    def missing_demonstrations(self) -> List[TrainingPair]:
        return [pair for pair in self.pairs if not pair.demonstrated]

    def missing_training(self) -> List[TrainingPair]:
        return [pair for pair in self.pairs if not pair.trained]

    def to_markdown(self) -> str:
        lines = [
            "# Tool-capability training coverage",
            "",
            f"- expected pairs: {self.expected_pairs}",
            f"- demonstrated pairs: {self.demonstrated_pairs}",
            f"- trained pairs: {self.trained_pairs}",
            "",
            "## Pairs",
        ]
        for pair in self.pairs:
            state = "trained" if pair.trained else "demonstrated" if pair.demonstrated else "missing"
            lines.append(
                f"- {pair.tool_id} | {pair.capability}: {state}; "
                f"live={pair.live_samples}, judged={pair.judge_samples}, "
                f"pass={pair.pass_rate:.2f}, score={pair.mean_score:.2f}"
            )
        return "\n".join(lines)


class TrainingCoverageAnalyzer:
    def analyze(
        self,
        tasks: Iterable[NormalizedTask],
        matrix: CapabilityMatrixReport,
    ) -> TrainingCoverageReport:
        expected = sorted(
            {
                (tool_id, task.primary_capability)
                for task in tasks
                for tool_id in task.compatible_tools
                if tool_id != "local_direct"
            }
        )
        grouped: Dict[Tuple[str, str], List[CapabilityCell]] = {}
        for cell in matrix.cells:
            grouped.setdefault((cell.tool_id, cell.capability), []).append(cell)

        pairs: List[TrainingPair] = []
        for tool_id, capability in expected:
            cells = grouped.get((tool_id, capability), [])
            live_samples = sum(cell.live_samples for cell in cells)
            judge_samples = sum(cell.live_judge_samples for cell in cells)
            sample_weight = sum(cell.live_samples for cell in cells)
            judged_weight = sum(cell.live_judge_samples for cell in cells)
            pass_rate = (
                sum(
                    cell.live_pass_rate * cell.live_samples
                    for cell in cells
                )
                / sample_weight
                if sample_weight
                else 0.0
            )
            mean_score = (
                sum(
                    cell.live_mean_score * cell.live_judge_samples
                    for cell in cells
                )
                / judged_weight
                if judged_weight
                else 0.0
            )
            pairs.append(
                TrainingPair(
                    tool_id=tool_id,
                    capability=capability,
                    live_samples=live_samples,
                    judge_samples=judge_samples,
                    pass_rate=pass_rate,
                    mean_score=mean_score,
                )
            )
        return TrainingCoverageReport(pairs=pairs)
