import logging
from typing import Any, Dict
from ..models import OperationTimings, TaskRequest, RouteDecision, OrchestratorResult

logger = logging.getLogger("agent_v2_2.routing.tracing")

class TracingManager:
    """Gestiona las trazas de ruta, modelo, versión, tiempos y errores."""
    def __init__(self):
        self._traces = []

    def record_trace(self, request: TaskRequest, decision: RouteDecision, result: OrchestratorResult):
        trace = {
            "request_id": request.request_id,
            "tool_id": decision.tool_id,
            "tier": decision.tier,
            "ok": result.ok,
            "error": result.error,
            "timings": result.timings.model_dump() if result.timings else None,
            "privacy_mode": result.privacy_mode
        }
        self._traces.append(trace)
        if result.ok:
            logger.info(f"Trace recorded: {trace['tool_id']} in {result.timings.total_seconds if result.timings else 0}s")
        else:
            logger.error(f"Trace recorded (Error): {trace['tool_id']} - {result.error}")
            
    def get_traces(self) -> list:
        return self._traces
