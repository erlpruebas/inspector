from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
from ..models import TaskRequest, OrchestratorResult

@dataclass
class ToolDefinition:
    id: str
    name: str
    description: str
    tier: str # "fast", "smart", "heavy"
    handler: Callable[[TaskRequest], OrchestratorResult]
    is_experimental: bool = False

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition):
        self._tools[tool.id] = tool

    def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
        return self._tools.get(tool_id)

    def list_tools(self) -> List[ToolDefinition]:
        return list(self._tools.values())
        
    def get_tools_by_tier(self, tier: str) -> List[ToolDefinition]:
        return [t for t in self._tools.values() if t.tier == tier]
