from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Optional

from ..evolution.experience import ExperienceStore
from ..evolution.matrix import CapabilityCell, CapabilityMatrixBuilder
from ..models import RouteDecision
from .contract import RequestContract
from .selector import CapabilitySelector, NoCompatibleToolError


@dataclass(frozen=True)
class EvolutionPolicy:
    minimum_samples: int = 3
    minimum_confidence: float = 0.3
    minimum_pass_rate: float = 0.7
    minimum_score: float = 7.0
    exploration_rate: float = 0.05


class EvolutionarySelector(CapabilitySelector):
    """Selects the fastest compatible tool supported by learned evidence."""

    def __init__(
        self,
        *,
        experience_store: Optional[ExperienceStore] = None,
        policy: Optional[EvolutionPolicy] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.experience_store = experience_store or ExperienceStore()
        self.matrix_builder = CapabilityMatrixBuilder(self.experience_store)
        self.policy = policy or EvolutionPolicy()

    def select_contract(self, contract: RequestContract) -> RouteDecision:
        compatible = self.compatible_tools(contract)
        if not compatible:
            raise NoCompatibleToolError(
                f"No eligible tool satisfies: {sorted(contract.required_accesses())}"
            )

        primary = str(contract.metadata.get("primary_capability") or "")
        shape = contract.execute.operation.value
        report = self.matrix_builder.build()
        exact = {
            (cell.tool_id, cell.capability, cell.task_shape): cell
            for cell in report.cells
        }
        by_capability: dict[tuple[str, str], list[CapabilityCell]] = {}
        for cell in report.cells:
            by_capability.setdefault((cell.tool_id, cell.capability), []).append(cell)

        ranked: list[tuple[tuple, object, CapabilityCell | None]] = []
        for tool in compatible:
            cell = exact.get((tool.tool_id, primary, shape))
            if cell is None:
                candidates = by_capability.get((tool.tool_id, primary), [])
                if candidates:
                    cell = max(candidates, key=lambda item: (item.confidence, item.samples))
            eligible = self._evidence_is_sufficient(cell)
            learned_latency = (
                cell.mean_seconds
                if cell is not None and cell.live_samples > 0
                else float(tool.observed_latency_seconds.get("median", 10_000))
            )
            rank = (
                0 if eligible else 1,
                learned_latency,
                -float(cell.confidence if cell else 0.0),
                tool.tool_id,
            )
            ranked.append((rank, tool, cell))

        ranked.sort(key=lambda item: item[0])
        selected_index = 0
        if len(ranked) > 1 and self._should_explore(contract):
            exploratory = [
                index
                for index, (_rank, _tool, cell) in enumerate(ranked[1:], start=1)
                if cell is not None and cell.live_samples > 0
            ]
            if exploratory:
                selected_index = exploratory[0]

        _rank, selected, cell = ranked[selected_index]
        ordered = [item for index, item in enumerate(ranked) if index != selected_index]
        alternatives = [tool.tool_id for _candidate_rank, tool, _cell in ordered[:4]]
        evidence = (
            f"live_samples={cell.live_samples}, live_pass={cell.live_pass_rate:.2f}, "
            f"live_score={cell.live_mean_score:.2f}, confidence={cell.confidence:.2f}, "
            f"latency={cell.mean_seconds:.2f}s"
            if cell is not None
            else "no learned cell; catalog fallback"
        )
        mode = "safe exploration" if selected_index else "fastest sufficient"
        return RouteDecision(
            tool_id=selected.tool_id,
            tier=selected.cognitive_max,
            model_id=selected.model or None,
            reason=f"Evolutionary router: {mode}; {evidence}.",
            alternatives=alternatives,
            privacy_mode="clear",
        )

    def _evidence_is_sufficient(self, cell: CapabilityCell | None) -> bool:
        if cell is None:
            return False
        return (
            cell.live_samples >= self.policy.minimum_samples
            and cell.confidence >= self.policy.minimum_confidence
            and cell.live_pass_rate >= self.policy.minimum_pass_rate
            and (
                cell.live_judge_samples == 0
                or cell.live_mean_score >= self.policy.minimum_score
            )
        )

    def _should_explore(self, contract: RequestContract) -> bool:
        if self.policy.exploration_rate <= 0:
            return False
        metadata = contract.metadata
        reproducible = bool(metadata.get("reproducible"))
        source_path = str(metadata.get("source_path") or "").casefold()
        if not reproducible and "benchmarks" not in source_path:
            return False
        digest = hashlib.sha256(contract.normalized_request.encode("utf-8")).digest()
        bucket = int.from_bytes(digest[:4], "big") / 2**32
        return bucket < self.policy.exploration_rate
