from __future__ import annotations

import re
from pathlib import Path

from .models import RouteDecision, TaskRequest
from .tool_registry import TOOLS


SENSITIVE_PATTERNS = (
    r"\b\d{8}[A-Z]\b",
    r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b",
    r"\b[\w.+-]+@[\w.-]+\.\w+\b",
    r"\b(?:\+34\s*)?[6789]\d{2}[\s.-]?\d{3}[\s.-]?\d{3}\b",
)


def choose_tool(request: TaskRequest) -> RouteDecision:
    text = request.text.strip()
    lower = text.casefold()
    privacy_mode = request.privacy_mode
    needs_privacy = privacy_mode == "ask" and looks_sensitive(text)
    effective_privacy = "redacted" if needs_privacy else ("clear" if privacy_mode == "ask" else privacy_mode)

    if is_desktop_operator_task(lower):
        return RouteDecision(
            tool_id="desktop_codex_operator",
            reason="La tarea parece requerir navegador, login, Telegram/BotFather o una interfaz visual ya autenticada.",
            privacy_mode=effective_privacy,
            needs_privacy_confirmation=needs_privacy,
            alternatives=("premium_codex_55", "runtime_opencode_deepseek32"),
        )
    if is_very_long_context_task(lower, request):
        return RouteDecision(
            tool_id="gemini_pro_long_context",
            reason="La tarea parece requerir contexto muy largo o muchos archivos; Gemini Pro queda como herramienta especializada.",
            privacy_mode=effective_privacy,
            needs_privacy_confirmation=needs_privacy,
            alternatives=("gemini_flash_files", "premium_codex_55"),
        )
    if is_gemini_file_task(lower, request):
        return RouteDecision(
            tool_id="gemini_flash_files",
            reason="La tarea combina archivos y contexto amplio moderado; Gemini Flash es buen candidato operativo.",
            privacy_mode=effective_privacy,
            needs_privacy_confirmation=needs_privacy,
            alternatives=("worker_openrouter_gpt54mini", "worker_openrouter_deepseek32"),
        )
    if is_terminal_or_code_task(lower):
        return RouteDecision(
            tool_id="runtime_opencode_deepseek32",
            reason="La tarea parece requerir acciones de runtime/terminal o varios pasos operativos.",
            privacy_mode=effective_privacy,
            needs_privacy_confirmation=needs_privacy,
            alternatives=("premium_codex_55", "worker_groq_compound_mini"),
        )
    if is_deep_reasoning_task(lower):
        return RouteDecision(
            tool_id="worker_openrouter_gpt54mini",
            reason="La tarea requiere sintesis, criterio ejecutivo o razonamiento sobre varios documentos.",
            privacy_mode=effective_privacy,
            needs_privacy_confirmation=needs_privacy,
            alternatives=("worker_openrouter_deepseek32", "worker_groq_compound_mini"),
        )
    if is_research_or_tools_task(lower):
        return RouteDecision(
            tool_id="worker_groq_compound_mini",
            reason="La tarea sugiere busqueda, herramientas o investigacion externa.",
            privacy_mode=effective_privacy,
            needs_privacy_confirmation=needs_privacy,
            alternatives=("worker_openrouter_gpt54mini", "runtime_opencode_deepseek32"),
        )
    if is_file_task(lower, request):
        return RouteDecision(
            tool_id="worker_openrouter_deepseek32",
            reason="La tarea usa archivos y parece resoluble por API directa con contexto compacto.",
            privacy_mode=effective_privacy,
            needs_privacy_confirmation=needs_privacy,
            alternatives=("router_groq_qwen32", "worker_openrouter_gpt54mini"),
        )
    return RouteDecision(
        tool_id="router_groq_qwen32",
        reason="Tarea general corta; se prioriza baja latencia con calidad suficiente.",
        privacy_mode=effective_privacy,
        needs_privacy_confirmation=needs_privacy,
        alternatives=("router_groq_llama8", "worker_openrouter_deepseek32"),
    )


def force_tool(tool_id: str, request: TaskRequest) -> RouteDecision:
    if tool_id not in TOOLS:
        raise ValueError(f"Herramienta desconocida: {tool_id}")
    privacy_mode = "redacted" if request.privacy_mode == "ask" and looks_sensitive(request.text) else request.privacy_mode
    if privacy_mode == "ask":
        privacy_mode = "clear"
    return RouteDecision(tool_id=tool_id, reason="Herramienta forzada por el usuario.", privacy_mode=privacy_mode)


def looks_sensitive(text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in SENSITIVE_PATTERNS)


def is_terminal_or_code_task(lower: str) -> bool:
    return any(token in lower for token in ("terminal", "comando", "ejecuta", "test", "repo", "codigo", "código", "archivo python", "modifica", "implementa"))


def is_desktop_operator_task(lower: str) -> bool:
    return any(
        token in lower
        for token in (
            "botfather",
            "crear bot",
            "crear bots",
            "telegram desktop",
            "youtube studio",
            "descarga los videos",
            "descargar videos",
            "iniciar sesion",
            "login",
            "navegador",
            "chrome",
            "interfaz grafica",
            "interfaz gráfica",
            "raton",
            "ratón",
            "teclado",
        )
    )


def is_deep_reasoning_task(lower: str) -> bool:
    return any(token in lower for token in ("estrategia", "decision", "decisión", "auditoria completa", "informe ejecutivo", "recomendacion", "recomendación", "analiza todos"))


def is_research_or_tools_task(lower: str) -> bool:
    return any(token in lower for token in ("busca", "investiga", "web", "fuentes", "alternativas", "proveedor"))


def is_file_task(lower: str, request: TaskRequest) -> bool:
    return bool(request.files) or any(token in lower for token in ("csv", "excel", "documento", "archivo", "json", "ics", "tabla"))


def is_gemini_file_task(lower: str, request: TaskRequest) -> bool:
    return (
        len(request.files) >= 2
        or file_bytes(request.files) > 1_000_000
        or any(token in lower for token in ("pdf", "documento largo", "mucho contexto", "varios archivos", "adjuntos"))
    )


def is_very_long_context_task(lower: str, request: TaskRequest) -> bool:
    return (
        len(request.files) >= 6
        or file_bytes(request.files) > 8_000_000
        or any(token in lower for token in ("contexto enorme", "todos estos documentos", "carpeta completa", "expediente completo"))
    )


def file_bytes(files: tuple[Path, ...]) -> int:
    total = 0
    for path in files:
        try:
            total += path.stat().st_size
        except OSError:
            continue
    return total
