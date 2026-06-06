from __future__ import annotations

import os
import time
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from benchmarks.env_utils import load_env_files

from .executor import execute_request
from .conversation_state import (
    build_human_confirmation,
    should_require_human_confirmation,
)
from .memory_retrieval import retrieve_memory_context
from .memory_store import MemoryStore
from .models import OperationTimings, OrchestratorResult, RouteDecision, TaskRequest
from .router import choose_tool, force_tool


class OrchestratorV21:
    def __init__(self, memory_store: MemoryStore | None = None) -> None:
        self.memory_store = memory_store or MemoryStore()

    def route(self, request: TaskRequest, *, tool_id: str = "") -> RouteDecision:
        return force_tool(tool_id, request) if tool_id else choose_tool(request)

    def prepare_request(self, request: TaskRequest) -> TaskRequest:
        memory_context = retrieve_memory_context(
            request.user_id,
            request.thread_id,
            request.text,
            store=self.memory_store,
        )
        metadata = dict(request.metadata)
        metadata["memory_context"] = {
            "facts": [asdict(fact) for fact in memory_context.facts],
            "thread_summary": memory_context.thread_summary,
            "retrieval_query": memory_context.retrieval_query,
            "source_count": memory_context.source_count,
        }
        metadata["system_context"] = self._system_context(request, memory_context.source_count)
        return replace(request, memory_context=memory_context, metadata=metadata)

    def handle(
        self,
        request: TaskRequest,
        *,
        tool_id: str = "",
        progress_callback: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> OrchestratorResult:
        total_started = time.monotonic()
        memory_started = time.monotonic()
        prepared_request = self.prepare_request(request)
        memory_seconds = time.monotonic() - memory_started

        routing_started = time.monotonic()
        decision = self.route(prepared_request, tool_id=tool_id)
        routing_seconds = time.monotonic() - routing_started
        self._notify_progress(
            progress_callback,
            "routed",
            {"decision": decision, "seconds": routing_seconds, "memory_seconds": memory_seconds},
        )
        approved = bool(prepared_request.metadata.get("human_confirmation_approved", False))
        needs_human_confirmation, human_reason = should_require_human_confirmation(prepared_request.text)
        if needs_human_confirmation and not approved:
            confirmation = build_human_confirmation(
                prepared_request,
                decision,
                human_reason or "This action is better approved by a human first.",
            )
            result = OrchestratorResult(
                ok=False,
                tool_id=decision.tool_id,
                tier=decision.tier,
                engine="",
                output=confirmation.message,
                workdir=Path(".").resolve(),
                elapsed_seconds=0,
                privacy_mode=str(decision.privacy_mode),
                requires_human_confirmation=True,
                human_confirmation=confirmation,
                error="human_confirmation_required",
            )
            result = self._with_timings(result, memory_seconds, routing_seconds, 0, total_started)
            self.memory_store.record_interaction(
                prepared_request,
                decision,
                result,
                human_confirmation=confirmation,
                memory_context=prepared_request.memory_context,
            )
            return result
        if decision.needs_privacy_confirmation:
            result = OrchestratorResult(
                ok=False,
                tool_id=decision.tool_id,
                tier=decision.tier,
                engine="",
                output="Sensitive data detected. Confirm privacy_mode as clear, mixed, or redacted before execution.",
                workdir=Path(".").resolve(),
                elapsed_seconds=0,
                privacy_mode=str(decision.privacy_mode),
                error="privacy_confirmation_required",
            )
            result = self._with_timings(result, memory_seconds, routing_seconds, 0, total_started)
            self.memory_store.record_interaction(
                prepared_request,
                decision,
                result,
                memory_context=prepared_request.memory_context,
            )
            return result
        execution_started = time.monotonic()
        result = self._execute_with_fallback(prepared_request, decision, allow_fallback=not bool(tool_id))
        execution_seconds = time.monotonic() - execution_started
        result = self._with_timings(result, memory_seconds, routing_seconds, execution_seconds, total_started)
        self._notify_progress(
            progress_callback,
            "executed",
            {"decision": decision, "result": result, "seconds": execution_seconds},
        )
        self.memory_store.record_interaction(
            prepared_request,
            decision,
            result,
            memory_context=prepared_request.memory_context,
        )
        return result

    @staticmethod
    def _notify_progress(
        callback: Callable[[str, dict[str, Any]], None] | None,
        event: str,
        payload: dict[str, Any],
    ) -> None:
        if callback is not None:
            callback(event, payload)

    @staticmethod
    def _with_timings(
        result: OrchestratorResult,
        memory_seconds: float,
        routing_seconds: float,
        execution_seconds: float,
        total_started: float,
    ) -> OrchestratorResult:
        return replace(
            result,
            timings=OperationTimings(
                memory_seconds=round(memory_seconds, 3),
                routing_seconds=round(routing_seconds, 3),
                execution_seconds=round(execution_seconds, 3),
                total_seconds=round(time.monotonic() - total_started, 3),
            ),
        )

    def _execute_with_fallback(
        self,
        request: TaskRequest,
        decision: RouteDecision,
        *,
        allow_fallback: bool,
    ) -> OrchestratorResult:
        result = execute_request(request, decision)
        if result.ok or not allow_fallback or not is_provider_failure(result.error):
            return result

        attempted = [decision.tool_id]
        for tool_id in decision.alternatives:
            if tool_id in attempted:
                continue
            attempted.append(tool_id)
            fallback_decision = force_tool(tool_id, request)
            fallback_result = execute_request(request, fallback_decision)
            if fallback_result.ok:
                return replace(
                    fallback_result,
                    output=(
                        f"{fallback_result.output}\n\n"
                        f"[Fallback automático: {decision.tool_id} no estaba disponible; se usó {tool_id}.]"
                    ).strip(),
                )
            result = fallback_result
            if not is_provider_failure(result.error):
                break
        return result

    def _system_context(self, request: TaskRequest, memory_event_count: int) -> dict[str, object]:
        load_env_files()
        source = str(request.metadata.get("source", "unknown"))
        return {
            "orchestrator": "orchestrator_v2_1",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "request_source": source,
            "telegram_connected": source in {"text", "voice"},
            "memory_events_available": memory_event_count,
            "providers_configured_not_health_checked": {
                "groq": bool(os.getenv("GROQ_API_KEY", "").strip()),
                "openrouter": bool(os.getenv("OPENROUTER_API_KEY", "").strip()),
                "gemini": bool(
                    os.getenv("GOOGLE_API_KEY", "").strip()
                    or os.getenv("GEMINI_API_KEY", "").strip()
                    or os.getenv("ORCH_GOOGLE_API_KEY", "").strip()
                ),
            },
        }


def is_provider_failure(error: str) -> bool:
    lower = error.casefold()
    return any(
        marker in lower
        for marker in (
            "401",
            "403",
            "408",
            "429",
            "500",
            "502",
            "503",
            "504",
            "invalid api key",
            "unauthorized",
            "rate limit",
            "timed out",
            "timeout",
            "connection",
        )
    )
