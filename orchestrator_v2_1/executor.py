from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

from benchmarks.engines.engine_factory import create_engine

from .desktop_adapter import execute_desktop
from .models import MemoryContext, OrchestratorResult, RouteDecision, TaskRequest
from .privacy import apply_privacy, copy_input_files
from .tool_registry import get_tool


RUN_ROOT = Path("orchestrator_v2_1/runtime/runs")


def execute_request(request: TaskRequest, decision: RouteDecision) -> OrchestratorResult:
    tool = get_tool(decision.tool_id)
    run_id = request.request_id or datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    workdir = (RUN_ROOT / run_id / tool.id).resolve()
    workdir.mkdir(parents=True, exist_ok=True)

    if tool.channel == "desktop":
        return execute_desktop(request, decision, workdir)
    if tool.channel == "local":
        return execute_local(request, decision, workdir)

    copied = copy_input_files(request.files, workdir)
    privacy_report = apply_privacy(workdir, str(decision.privacy_mode))
    prompt = build_prompt(request, decision, copied, privacy_report)
    prompt_path = workdir / "prompt.md"
    prompt_path.write_text(prompt, encoding="utf-8")

    started = time.monotonic()
    try:
        engine = create_engine(tool.engine)
        engine_result = engine.run("orchestrator-v2-1-task", prompt, workdir, ["resultado.md"])
    except Exception as exc:
        return OrchestratorResult(
            ok=False,
            tool_id=tool.id,
            tier=tool.tier,
            engine=tool.engine,
            output="",
            workdir=workdir,
            elapsed_seconds=round(time.monotonic() - started, 3),
            privacy_mode=str(decision.privacy_mode),
            error=f"{type(exc).__name__}: {exc}",
        )

    output = read_output(engine_result.output_files, engine_result.stdout)
    return OrchestratorResult(
        ok=engine_result.ok,
        tool_id=tool.id,
        tier=tool.tier,
        engine=tool.engine,
        output=output,
        workdir=workdir,
        elapsed_seconds=round(time.monotonic() - started, 3),
        privacy_mode=str(decision.privacy_mode),
        error=engine_result.stderr if not engine_result.ok else "",
    )


def execute_local(request: TaskRequest, decision: RouteDecision, workdir: Path) -> OrchestratorResult:
    tool = get_tool(decision.tool_id)
    return OrchestratorResult(
        ok=True,
        tool_id=tool.id,
        tier=tool.tier,
        engine=tool.engine,
        output=f"Local route ready. Request: {request.text}",
        workdir=workdir,
        elapsed_seconds=0,
        privacy_mode=str(decision.privacy_mode),
    )


def build_prompt(request: TaskRequest, decision: RouteDecision, files: list[Path], privacy_report: dict) -> str:
    file_lines = "\n".join(f"- {path.name}" for path in files) or "- none"
    memory_block = format_memory_context(request.memory_context)
    system_context = json.dumps(request.metadata.get("system_context", {}), ensure_ascii=False, indent=2)
    return f"""
Solve the user task.

Task:
{request.text}

Routing context:
- tool: {decision.tool_id}
- tier: {decision.tier}
- reason: {decision.reason}
- privacy: {decision.privacy_mode}
- files:
{file_lines}

Memory context:
{memory_block}

Orchestrator runtime context:
{system_context}

Privacy report:
{privacy_report}

Answer the request naturally. Use runtime context only when it is relevant, such as a system-status question.
Start with the answer itself. Do not begin with acknowledgements, praise, conversational filler, or a paraphrase of the request.
Avoid openings such as "Claro", "Entiendo", "Parece que", or "Te interesa".
Do not add a closing question unless essential information is missing and the task cannot be completed without it.
Do not invent provider health, current facts, or actions that were not actually performed.
`providers_configured_not_health_checked` means only that credentials are present. It does not mean those providers are healthy or available.
For a status request, distinguish clearly between configured components and verified operational components.
Return the final answer in `resultado.md`.
""".strip()


def format_memory_context(memory_context: MemoryContext) -> str:
    if not memory_context.facts and not memory_context.thread_summary:
        return "- none"
    lines: list[str] = []
    if memory_context.retrieval_query:
        lines.append(f"- query: {memory_context.retrieval_query}")
    if memory_context.thread_summary:
        lines.append(f"- thread: {memory_context.thread_summary}")
    for fact in memory_context.facts:
        lines.append(f"- {fact.label}: {fact.value} (kind={fact.kind})")
    return "\n".join(lines) or "- none"


def read_output(paths: list[str], fallback: str) -> str:
    chunks: list[str] = []
    for raw in paths:
        path = Path(raw)
        if path.exists() and path.is_file():
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n\n".join(chunks).strip() or fallback.strip()
