from __future__ import annotations

import re
import json
import time
from datetime import datetime
from pathlib import Path

from benchmarks.engines.engine_factory import create_engine
from benchmarks.token_accounting import record_usage

from .models import OrchestratorResult, RouteDecision, TaskRequest
from .privacy import apply_optional_privacy, copy_input_files
from .tool_registry import get_tool
from .desktop_codex_operator import run_desktop_codex_operator


RUN_ROOT = Path("orchestrator_v2/runtime/runs")


def execute_request(request: TaskRequest, decision: RouteDecision) -> OrchestratorResult:
    tool = get_tool(decision.tool_id)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    workdir = (RUN_ROOT / run_id / decision.tool_id).resolve()
    workdir.mkdir(parents=True, exist_ok=True)

    if tool.engine.startswith("desktop_codex:"):
        return execute_desktop_codex(request, decision, workdir)

    copied = copy_input_files(request.files, workdir)
    privacy_report = apply_optional_privacy(workdir, str(decision.privacy_mode))

    prompt = build_prompt(request, decision, copied, privacy_report)
    started = time.monotonic()
    try:
        engine = create_engine(tool.engine)
        result = engine.run("telegram-task", prompt, workdir, ["resultado.md"])
    except Exception as exc:
        return OrchestratorResult(
            ok=False,
            tool_id=tool.id,
            engine=tool.engine,
            output="",
            workdir=workdir,
            elapsed_seconds=round(time.monotonic() - started, 3),
            privacy_mode=str(decision.privacy_mode),
            error=f"{type(exc).__name__}: {exc}",
        )

    output = read_output(result.output_files, result.stdout)
    record_usage(
        workdir.parent / "token_usage.jsonl",
        source="orchestrator_v2",
        component=tool.id,
        provider=tool.engine.split(":", 1)[0],
        model=tool.engine.split(":", 1)[1] if ":" in tool.engine else tool.engine,
        operation="task_execution",
        usage=result.usage,
        prompt_text=prompt,
        completion_text=output,
        task_id=request.metadata.get("task_id", ""),
        user_id=request.user_id,
        thread_id=request.thread_id,
        metadata={"privacy_mode": decision.privacy_mode, "tool_id": tool.id, "engine": tool.engine},
    )
    return OrchestratorResult(
        ok=result.ok,
        tool_id=tool.id,
        engine=tool.engine,
        output=output,
        workdir=workdir,
        elapsed_seconds=round(time.monotonic() - started, 3),
        privacy_mode=str(decision.privacy_mode),
        error=result.stderr if not result.ok else "",
    )


def execute_desktop_codex(request: TaskRequest, decision: RouteDecision, workdir: Path) -> OrchestratorResult:
    tool = get_tool(decision.tool_id)
    started = time.monotonic()
    send = bool(request.metadata.get("desktop_send", False))
    prompt = build_desktop_prompt(request, decision)
    result = run_desktop_codex_operator(
        prompt,
        send=send,
        new_chat=bool(request.metadata.get("desktop_new_chat", True)),
        wait_seconds=int(request.metadata.get("desktop_wait_seconds", 1800)),
    )
    marker = workdir / "desktop_codex_result.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    status = "Prompt preparado para Codex Desktop."
    if send:
        status = "Prompt enviado a Codex Desktop y captura final registrada."
    if result.error:
        status = result.error
    return OrchestratorResult(
        ok=result.ok,
        tool_id=tool.id,
        engine=tool.engine,
        output=(
            f"{status}\n\n"
            f"Prompt: {result.prompt_path}\n"
            f"Evidencias: {result.run_dir}\n"
            f"Captura: {result.screenshot_path or '-'}\n"
            f"Tokens extraidos: {result.extracted_tokens_path or '-'}"
        ),
        workdir=workdir,
        elapsed_seconds=round(time.monotonic() - started, 3),
        privacy_mode=str(decision.privacy_mode),
        error=result.error,
    )


def build_desktop_prompt(request: TaskRequest, decision: RouteDecision) -> str:
    return f"""
Ejecuta esta tarea usando Codex Desktop como operador visual.

Peticion del usuario:
{request.text}

Contexto del gestor:
- usuario: {request.user_id}
- hilo: {request.thread_id}
- herramienta elegida: {decision.tool_id}
- motivo de ruta: {decision.reason}
- privacidad: {decision.privacy_mode}

Reglas:
- Si necesitas login, 2FA, captcha o confirmacion sensible, detente y pide intervencion humana.
- No expongas credenciales en lugares externos.
- Al terminar, escribe un resumen final con que has conseguido, que queda pendiente, archivos o tokens generados, y si la tarea esta completada.
""".strip()


def build_prompt(request: TaskRequest, decision: RouteDecision, files: list[Path], privacy_report: dict) -> str:
    file_lines = "\n".join(f"- {path.name}" for path in files) or "- Ninguno"
    return f"""
Resuelve la tarea del usuario.

Tarea:
{request.text}

Contexto:
- usuario: {request.user_id}
- hilo: {request.thread_id}
- herramienta elegida: {decision.tool_id}
- motivo de ruta: {decision.reason}
- modo privacidad: {decision.privacy_mode}
- archivos en directorio de trabajo:
{file_lines}

Reporte privacidad:
{privacy_report}

Devuelve la respuesta final en `resultado.md`.
""".strip()


def read_output(paths: list[str], fallback: str) -> str:
    chunks: list[str] = []
    for raw in paths:
        path = Path(raw)
        if path.exists() and path.is_file():
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return strip_visible_reasoning("\n\n".join(chunks).strip() or fallback.strip())


def strip_visible_reasoning(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    return text.strip()
