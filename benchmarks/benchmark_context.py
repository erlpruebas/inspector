from __future__ import annotations

from pathlib import Path

from task_loader import BenchmarkTask
from web_context import build_web_context


def prompt_for_execution(task: BenchmarkTask, workdir: Path) -> str:
    prompt = task.prompt + local_files_section(task)
    if not task.requires_network:
        return prompt
    web_context = build_web_context(prompt)
    (workdir / "web_context.md").write_text(web_context, encoding="utf-8")
    return (
        prompt
        + "\n\nContexto web preparado por el benchmark: `web_context.md`."
        + "\nLee ese archivo antes de responder. Si usas datos del contexto web, incluye las fuentes relevantes en la respuesta."
    )


def local_files_section(task: BenchmarkTask) -> str:
    if not task.required_files:
        return ""
    lines = [
        "",
        "",
        "Archivos locales preparados en el directorio de trabajo:",
        *[f"- `{filename}`" for filename in task.required_files],
        "",
        "Usa esas rutas relativas cuando necesites leer datos locales.",
    ]
    return "\n".join(lines)
