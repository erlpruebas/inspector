from typing import List, Callable, Optional
import logging
from ..models import TaskRequest, RouteDecision, OrchestratorResult

logger = logging.getLogger("agent_v2_2.routing.fallbacks")

class FallbackManager:
    def __init__(self, executor_func: Callable[[TaskRequest, RouteDecision], OrchestratorResult]):
        self.executor_func = executor_func

    def is_provider_failure(self, error: str) -> bool:
        lower = error.casefold()
        markers = [
            "401", "403", "408", "429", "500", "502", "503", "504",
            "invalid api key", "unauthorized", "rate limit", "timed out",
            "timeout", "connection"
        ]
        return any(marker in lower for marker in markers)

    def execute_with_fallback(self, request: TaskRequest, decision: RouteDecision, allow_fallback: bool = True) -> OrchestratorResult:
        result = self.executor_func(request, decision)
        
        if result.ok or not allow_fallback or not self.is_provider_failure(result.error or ""):
            return result

        attempted = [decision.tool_id]
        logger.warning(f"Provider failure on {decision.tool_id}. Attempting fallbacks: {decision.alternatives}")
        
        for fallback_tool_id in decision.alternatives:
            if fallback_tool_id in attempted:
                continue
            
            attempted.append(fallback_tool_id)
            
            # Crear decision forzada
            fallback_decision = RouteDecision(
                tool_id=fallback_tool_id,
                tier=decision.tier,
                reason=f"Fallback automático desde {decision.tool_id}",
                alternatives=[],
                privacy_mode=decision.privacy_mode
            )
            
            fallback_result = self.executor_func(request, fallback_decision)
            
            if fallback_result.ok:
                fallback_result.output = (
                    f"{fallback_result.output}\n\n"
                    f"[Fallback automático: {decision.tool_id} falló; se usó {fallback_tool_id}.]"
                )
                return fallback_result
                
            if not self.is_provider_failure(fallback_result.error or ""):
                return fallback_result
                
        return result
