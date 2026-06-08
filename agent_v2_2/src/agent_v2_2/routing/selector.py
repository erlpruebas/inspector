from typing import List, Optional
from ..models import TaskRequest, RouteDecision
from .registry import ToolRegistry

class CapabilitySelector:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def select_route(self, request: TaskRequest) -> RouteDecision:
        """
        Analiza el request y determina el mejor tool y fallback.
        Esta es una versión simplificada de la lógica original.
        """
        text = request.text.lower()
        
        # Simple heuristics for routing
        if any(keyword in text for keyword in ["bash", "cmd", "powershell", "comando", "terminal"]):
            return RouteDecision(
                tool_id="local_cmd",
                tier="fast",
                reason="Solicitud explícita de comando de terminal.",
                alternatives=[],
                privacy_mode="mixed"
            )
            
        if any(keyword in text for keyword in ["codigo", "programa", "python", "script", "app"]):
            return RouteDecision(
                tool_id="codex",
                tier="smart",
                reason="Solicitud de generación o análisis de código.",
                alternatives=["gemini_coder", "opencode"],
                privacy_mode="mixed"
            )
            
        return RouteDecision(
            tool_id="groq_fast",
            tier="fast",
            reason="Consulta conversacional general, se envía al modelo rápido.",
            alternatives=["gemini_fast"],
            privacy_mode="clear"
        )
