from __future__ import annotations

from .executor import execute_request
from .memory_store import MemoryStore
from .models import OrchestratorResult, TaskRequest
from .router import choose_tool, force_tool


class GestorOrquestador:
    def handle(self, request: TaskRequest, *, tool_id: str = "") -> OrchestratorResult:
        decision = force_tool(tool_id, request) if tool_id else choose_tool(request)
        if decision.needs_privacy_confirmation:
            return OrchestratorResult(
                ok=False,
                tool_id=decision.tool_id,
                engine="",
                output=(
                    "La tarea parece contener datos sensibles. "
                    "Confirma si quieres usar modo redacted, mixed o clear antes de ejecutar."
                ),
                workdir=__import__("pathlib").Path("."),
                elapsed_seconds=0,
                privacy_mode=str(decision.privacy_mode),
                error="privacy_confirmation_required",
            )
        result = execute_request(request, decision)
        MemoryStore.for_user(request.user_id, request.thread_id).append_interaction(
            request=request.text,
            response=result.output if result.ok else result.error,
            metadata={
                "tool_id": result.tool_id,
                "engine": result.engine,
                "ok": result.ok,
                "privacy_mode": result.privacy_mode,
                "elapsed_seconds": result.elapsed_seconds,
            },
        )
        return result
