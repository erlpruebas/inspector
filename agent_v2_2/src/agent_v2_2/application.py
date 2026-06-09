from __future__ import annotations

import time
from dataclasses import asdict
from pathlib import Path
from typing import Callable, Optional

from .capabilities.memory import MemoryStore
from .capabilities.voice import VoiceCapabilities
from .evolution.experience import ExperienceStore, RouterExperience
from .models import OperationTimings, OrchestratorResult, TaskRequest
from .routing.contract import RequestContract
from .routing.selector import CapabilitySelector


Executor = Callable[[TaskRequest, object], OrchestratorResult]


class AgentApplication:
    """One vertical request flow shared by CLI and Telegram transports."""

    def __init__(
        self,
        *,
        selector: Optional[CapabilitySelector] = None,
        executor: Executor,
        memory_store: Optional[MemoryStore] = None,
        experience_store: Optional[ExperienceStore] = None,
        voice: Optional[VoiceCapabilities] = None,
    ) -> None:
        self.selector = selector or CapabilitySelector()
        self.executor = executor
        self.memory_store = memory_store or MemoryStore()
        self.experience_store = experience_store or ExperienceStore()
        self.voice = voice or VoiceCapabilities()

    def handle(
        self,
        request: TaskRequest,
        contract: RequestContract,
    ) -> OrchestratorResult:
        total_started = time.monotonic()
        user_id = request.user_id or "anonymous"
        thread_id = request.thread_id or "default"
        self.memory_store.record_message(
            user_id,
            thread_id,
            "user",
            request.text,
            metadata={"request_id": request.request_id},
        )

        memory_started = time.monotonic()
        memory_context = self.memory_store.retrieve_memory_context(
            user_id,
            thread_id,
            request.text,
        )
        memory_seconds = time.monotonic() - memory_started

        metadata = dict(request.metadata)
        metadata["request_contract"] = contract.model_dump(mode="json")
        if memory_context.source_count:
            metadata["memory_context"] = {
                "facts": [asdict(fact) for fact in memory_context.facts],
                "thread_summary": memory_context.thread_summary,
                "retrieval_query": memory_context.retrieval_query,
                "source_count": memory_context.source_count,
            }
        prepared = request.model_copy(update={"metadata": metadata})

        routing_started = time.monotonic()
        decision = self.selector.select_contract(contract)
        routing_seconds = time.monotonic() - routing_started

        execution_started = time.monotonic()
        result = self.executor(prepared, decision)
        execution_seconds = time.monotonic() - execution_started
        result.timings = OperationTimings(
            memory_seconds=memory_seconds,
            routing_seconds=routing_seconds,
            execution_seconds=execution_seconds,
            total_seconds=time.monotonic() - total_started,
        )

        verified = bool(result.ok and result.output.strip())
        self.experience_store.append(
            RouterExperience(
                experience_id=request.request_id,
                timestamp=request.created_at.isoformat(),
                catalog_version=3,
                task_id=request.request_id,
                task_shape=contract.execute.operation.value,
                tool_id=decision.tool_id,
                required_capabilities=[
                    item.value
                    for item in contract.execute.instrumental_capabilities
                ],
                cognitive_requirements=[
                    item.value
                    for item in contract.execute.cognitive_requirements
                ],
                elapsed_seconds=result.timings.total_seconds,
                objective_checks={
                    "passed": verified,
                    "checks": [
                        {
                            "name": "non_empty_output",
                            "passed": bool(result.output.strip()),
                            "detail": "",
                        }
                    ],
                },
                judge_scores=[],
                outcome="sufficient" if verified else "insufficient",
                failure_reason=result.error,
                metadata={
                    "contract_schema": contract.schema_version,
                    "alternatives": decision.alternatives,
                },
            )
        )
        self.memory_store.record_message(
            user_id,
            thread_id,
            "assistant",
            result.output or result.error or "",
            metadata={
                "request_id": request.request_id,
                "tool_id": decision.tool_id,
                "ok": result.ok,
            },
        )
        return result

    def handle_voice(
        self,
        audio_path: Path,
        request: TaskRequest,
        contract: RequestContract,
    ) -> OrchestratorResult:
        transcription_started = time.monotonic()
        text = self.voice.transcribe_audio_file(audio_path)
        result = self.handle(request.model_copy(update={"text": text}), contract)
        if result.timings:
            result.timings.transcription_seconds = (
                time.monotonic() - transcription_started
            )
            result.timings.total_seconds += result.timings.transcription_seconds
        return result
