from __future__ import annotations

from typing import List, Optional

from ..capabilities.catalog import CapabilityCatalog, ToolEntry, create_default_catalog
from ..models import RouteDecision, TaskRequest
from .contract import CognitiveLevel, RequestContract
from .registry import ToolRegistry


COGNITIVE_RANK = {
    "none": 0,
    "light": 1,
    "general": 2,
    "reasoning": 3,
}


class NoCompatibleToolError(RuntimeError):
    pass


class CapabilitySelector:
    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        catalog: Optional[CapabilityCatalog] = None,
    ) -> None:
        self.registry = registry or ToolRegistry()
        self.catalog = catalog or create_default_catalog()

    def select_contract(self, contract: RequestContract) -> RouteDecision:
        compatible = [
            tool
            for tool in self.catalog.tools
            if self._is_compatible(tool, contract)
        ]
        if not compatible:
            raise NoCompatibleToolError(
                f"No eligible tool satisfies: {sorted(contract.required_accesses())}"
            )

        compatible.sort(key=lambda tool: self._rank(tool, contract))
        selected = compatible[0]
        alternatives = [tool.tool_id for tool in compatible[1:4]]
        return RouteDecision(
            tool_id=selected.tool_id,
            tier=selected.cognitive_max,
            model_id=selected.model or None,
            reason=(
                "Fastest eligible tool satisfying all mandatory access and "
                "cognitive requirements."
            ),
            alternatives=alternatives,
            privacy_mode="clear",
        )

    def select_route(self, request: TaskRequest) -> RouteDecision:
        contract_payload = request.metadata.get("request_contract")
        if contract_payload:
            contract = RequestContract.model_validate(contract_payload)
            return self.select_contract(contract)

        # Compatibility path for direct commands while the fast contract router
        # is integrated in Step 3.
        if request.operation == "direct_command" or request.tool_name == "local_direct":
            return RouteDecision(
                tool_id="local_direct",
                tier="none",
                reason="Explicit registered local command.",
                alternatives=[],
                privacy_mode="mixed",
            )
        raise ValueError("A validated request_contract is required for routing")

    def compatible_tools(self, contract: RequestContract) -> List[ToolEntry]:
        return [
            tool for tool in self.catalog.tools if self._is_compatible(tool, contract)
        ]

    def _is_compatible(self, tool: ToolEntry, contract: RequestContract) -> bool:
        if not tool.selection_eligible:
            return False
        primary = str(contract.metadata.get("primary_capability") or "")
        if (
            primary
            and tool.operational_capabilities
            and primary not in tool.operational_capabilities
        ):
            return False
        required_level = COGNITIVE_RANK[contract.execute.cognitive_level.value]
        if COGNITIVE_RANK.get(tool.cognitive_max, -1) < required_level:
            return False

        capabilities = set(tool.instrumental_capabilities)
        if not {
            item.value for item in contract.execute.instrumental_capabilities
        }.issubset(capabilities):
            return False
        cognitive_strengths = set(tool.cognitive_strengths)
        if not {
            item.value for item in contract.execute.cognitive_requirements
        }.issubset(cognitive_strengths):
            return False

        access = {
            f"{method.operation}:{method.format}"
            for method in tool.access_methods
            if method.support == "direct"
        }
        for requirement in contract.execute.file_requirements:
            for operation in requirement.operations:
                if f"{operation.value}:{requirement.format.value}" not in access:
                    return False
        return True

    @staticmethod
    def _rank(tool: ToolEntry, contract: RequestContract) -> tuple[float, int, str]:
        operation_penalty = 0 if contract.execute.operation.value in tool.best_for else 1
        median = float(tool.observed_latency_seconds.get("median", 10_000))
        return (operation_penalty, median, tool.tool_id)
