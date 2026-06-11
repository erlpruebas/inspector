from __future__ import annotations

import json
import shutil
import threading
import time
from pathlib import Path

from ..capabilities.catalog import CapabilityCatalog, ToolEntry, create_default_catalog
from ..models import OrchestratorResult, RouteDecision, TaskRequest
from .workspace import WorkspaceManager


class ExecutionEngine:
    """Executes Agent 2.2 routes through the real benchmark engine adapters."""

    def __init__(
        self,
        workspace_manager: WorkspaceManager,
        catalog: CapabilityCatalog | None = None,
    ) -> None:
        self.workspace_manager = workspace_manager
        self.catalog = catalog or create_default_catalog()
        self._active_lock = threading.RLock()
        self._active_engines: dict[str, object] = {}

    def execute_code(self, request: TaskRequest, decision: RouteDecision) -> OrchestratorResult:
        workdir = self.workspace_manager.create_isolated_workspace()
        tool = self.catalog.get_tool(decision.tool_id)
        if tool is None:
            return self._failure(decision, workdir, f"Unknown tool: {decision.tool_id}")

        engine_spec = self._engine_spec(tool)
        if engine_spec is None:
            return self._failure(
                decision,
                workdir,
                f"Tool {decision.tool_id} has no executable engine adapter",
            )

        copied_files = self._copy_attachments(request, workdir)
        prompt = self._build_prompt(request, decision, copied_files)
        (workdir / "prompt.md").write_text(prompt, encoding="utf-8")

        started = time.monotonic()
        try:
            from benchmarks.engines.engine_factory import create_engine

            engine = create_engine(engine_spec)
            with self._active_lock:
                self._active_engines[request.request_id] = engine
            try:
                engine_result = engine.run(
                    request.request_id,
                    prompt,
                    workdir,
                    ["resultado.md"],
                )
            finally:
                with self._active_lock:
                    self._active_engines.pop(request.request_id, None)
        except Exception as exc:
            return OrchestratorResult(
                ok=False,
                tool_id=decision.tool_id,
                tier=decision.tier,
                output="",
                error=f"{type(exc).__name__}: {exc}",
                elapsed_seconds=round(time.monotonic() - started, 3),
                privacy_mode=decision.privacy_mode,
                workdir=workdir,
                metadata={"evidence_kind": "live", "engine_spec": engine_spec},
            )

        output = self._read_output(engine_result.output_files, engine_result.stdout)
        return OrchestratorResult(
            ok=bool(engine_result.ok and output.strip()),
            tool_id=decision.tool_id,
            tier=decision.tier,
            output=output,
            error=engine_result.stderr if not engine_result.ok else None,
            elapsed_seconds=round(time.monotonic() - started, 3),
            privacy_mode=decision.privacy_mode,
            workdir=workdir,
            metadata={
                "evidence_kind": "live",
                "engine_spec": engine_spec,
                "engine": engine_result.engine,
                "model": engine_result.model,
                "timed_out": engine_result.timed_out,
                "error_type": engine_result.error_type,
                "output_files": list(engine_result.output_files),
            },
        )

    def cancel(self, request_id: str) -> bool:
        with self._active_lock:
            engine = self._active_engines.get(request_id)
        cancel = getattr(engine, "cancel", None)
        return bool(cancel(request_id)) if callable(cancel) else False

    def _copy_attachments(self, request: TaskRequest, workdir: Path) -> list[Path]:
        copied: list[Path] = []
        for attachment in request.attachments:
            source = Path(attachment.path)
            if not source.exists() or not source.is_file():
                continue
            destination = workdir / source.name
            if source.resolve() != destination.resolve():
                shutil.copy2(source, destination)
            copied.append(destination)
        return copied

    def _build_prompt(
        self,
        request: TaskRequest,
        decision: RouteDecision,
        copied_files: list[Path],
    ) -> str:
        file_lines = "\n".join(f"- {path.name}" for path in copied_files) or "- none"
        memory = request.metadata.get("memory_context") or {}
        memory_block = json.dumps(memory, ensure_ascii=False, indent=2) if memory else "- none"
        return f"""
Solve the user request using the available files when relevant.

User request:
{request.text}

Routing:
- tool: {decision.tool_id}
- tier: {decision.tier}
- reason: {decision.reason}

Files:
{file_lines}

Relevant memory context:
{memory_block}

Use memory silently. Do not mention memory storage or retrieval unless the user
explicitly asks about memory. Do not claim actions or fresh facts that were not
actually obtained. Return the final user-facing answer in `resultado.md`.
""".strip()

    def _engine_spec(self, tool: ToolEntry) -> str | None:
        provider = tool.provider.casefold()
        model = tool.model.strip()
        if tool.tool_id == "local_direct" or tool.invocation_type == "desktop":
            return None
        if provider == "openai":
            return f"codex={model}" if model else None
        if provider == "google":
            if "grounded" in tool.tool_id:
                return f"gemini_grounded={model or 'gemini-2.5-flash'}"
            if tool.invocation_type == "cli":
                return f"gemini={model}"
            return f"gemini_api={model or 'gemini-2.5-flash'}"
        if provider == "groq":
            return f"groq={model}"
        if provider == "openrouter":
            return f"openrouter={model}"
        if provider == "opencode":
            return f"opencode={model}"
        return None

    def _read_output(self, paths: list[str], fallback: str) -> str:
        chunks: list[str] = []
        for raw_path in paths:
            path = Path(raw_path)
            if path.exists() and path.is_file():
                chunks.append(path.read_text(encoding="utf-8", errors="replace"))
        return "\n\n".join(chunks).strip() or fallback.strip()

    def _failure(
        self,
        decision: RouteDecision,
        workdir: Path,
        message: str,
    ) -> OrchestratorResult:
        return OrchestratorResult(
            ok=False,
            tool_id=decision.tool_id,
            tier=decision.tier,
            error=message,
            privacy_mode=decision.privacy_mode,
            workdir=workdir,
            metadata={"evidence_kind": "unavailable"},
        )
