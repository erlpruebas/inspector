from __future__ import annotations

import time
from pathlib import Path

from .models import OrchestratorResult, ResultAttachment, RouteDecision, TaskRequest
from .tool_registry import get_tool


def execute_desktop(request: TaskRequest, decision: RouteDecision, workdir: Path) -> OrchestratorResult:
    """The only v2.1 module allowed to call the visual Codex Desktop operator."""

    tool = get_tool(decision.tool_id)
    started = time.monotonic()
    try:
        from orchestrator_v2.desktop_codex_operator import run_desktop_codex_operator
    except Exception as exc:
        return OrchestratorResult(
            ok=False,
            tool_id=tool.id,
            tier=tool.tier,
            engine=tool.engine,
            output="Codex Desktop adapter could not import the legacy operator.",
            workdir=workdir,
            elapsed_seconds=round(time.monotonic() - started, 3),
            privacy_mode=str(decision.privacy_mode),
            error=f"{type(exc).__name__}: {exc}",
        )

    send = bool(request.metadata.get("desktop_send", False))
    prompt = build_desktop_prompt(request, decision)
    result = run_desktop_codex_operator(
        prompt,
        send=send,
        new_chat=bool(request.metadata.get("desktop_new_chat", True)),
        wait_seconds=int(request.metadata.get("desktop_wait_seconds", 1800)),
    )

    attachments: list[ResultAttachment] = []
    if result.run_dir:
        attachments.append(ResultAttachment(kind="directory", path=Path(result.run_dir), label="Desktop run directory", source=tool.id))
    if result.screenshot_path:
        attachments.append(ResultAttachment(kind="image", path=Path(result.screenshot_path), label="Codex Desktop screenshot", source=tool.id))
    if result.extracted_tokens_path:
        attachments.append(ResultAttachment(kind="json", path=Path(result.extracted_tokens_path), label="Vision extraction", source=tool.id))
    if result.result_path:
        attachments.append(ResultAttachment(kind="markdown", path=Path(result.result_path), label="Desktop result note", source=tool.id))

    status = result.status or ("sent" if send else "prepared")
    output = (
        f"Codex Desktop status: {status}\n"
        f"Prompt: {result.prompt_path}\n"
        f"Evidences: {result.run_dir}"
    )
    return OrchestratorResult(
        ok=result.ok,
        tool_id=tool.id,
        tier=tool.tier,
        engine=tool.engine,
        output=output,
        workdir=workdir,
        elapsed_seconds=round(time.monotonic() - started, 3),
        privacy_mode=str(decision.privacy_mode),
        attachments=tuple(attachments),
        error=result.error,
    )


def build_desktop_prompt(request: TaskRequest, decision: RouteDecision) -> str:
    memory_block = format_memory_context(request.memory_context)
    return f"""
Execute this task using Codex Desktop as a visual operator.

User request:
{request.text}

Route:
- tool: {decision.tool_id}
- tier: {decision.tier}
- reason: {decision.reason}
- privacy: {decision.privacy_mode}

Memory context:
{memory_block}

Rules:
- Stop and ask for human help on login, 2FA, captcha, payment, or credential screens.
- Do not expose secrets in external websites.
- Finish with a concise final summary visible in Codex Desktop.
""".strip()


def format_memory_context(memory_context) -> str:
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
