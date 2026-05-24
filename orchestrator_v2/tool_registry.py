from __future__ import annotations

from .models import Herramienta


TOOLS: dict[str, Herramienta] = {
    "router_groq_qwen32": Herramienta(
        id="router_groq_qwen32",
        engine="groq:qwen/qwen3-32b",
        kind="api_directa",
        role="router_fast_or_worker",
        description="Groq Qwen 32B. Mejor candidato Groq equilibrado para router util y tareas cortas.",
        strengths=("rapido", "buena calidad relativa", "api estable"),
        weaknesses=("no es agente de terminal",),
        cost_level="low",
        reliability="strong_candidate",
    ),
    "router_groq_llama8": Herramienta(
        id="router_groq_llama8",
        engine="groq:llama-3.1-8b-instant",
        kind="api_directa",
        role="router_fast",
        description="Groq Llama 8B Instant. Muy rapido para clasificacion y decisiones sencillas.",
        strengths=("muy rapido", "barato", "estable"),
        weaknesses=("calidad mas baja en tareas de contenido"),
        cost_level="very_low",
        reliability="candidate",
    ),
    "worker_openrouter_gpt54mini": Herramienta(
        id="worker_openrouter_gpt54mini",
        engine="openrouter:openai/gpt-5.4-mini",
        kind="api_directa",
        role="worker_reasoning",
        description="GPT-5.4 mini via OpenRouter. Mejor media del run final en tareas duras.",
        strengths=("buena calidad", "latencia razonable", "api directa"),
        weaknesses=("no ejecuta terminal por si mismo"),
        cost_level="medium",
        reliability="strong_candidate",
    ),
    "worker_openrouter_deepseek32": Herramienta(
        id="worker_openrouter_deepseek32",
        engine="openrouter:deepseek/deepseek-v3.2",
        kind="api_directa",
        role="worker_cheap",
        description="DeepSeek V3.2 via OpenRouter. Worker barato y razonable.",
        strengths=("coste bajo", "usable en API directa"),
        weaknesses=("mas lento que Groq",),
        cost_level="low",
        reliability="strong_candidate",
    ),
    "worker_groq_compound_mini": Herramienta(
        id="worker_groq_compound_mini",
        engine="groq:groq/compound-mini",
        kind="runtime_agentico",
        role="agentic_cloud",
        description="Groq Compound Mini. Runtime cloud con herramientas; ya funciona mejor con contexto compacto.",
        strengths=("runtime con herramientas", "sin CLI local"),
        weaknesses=("calidad irregular", "vigilar limites de contexto"),
        cost_level="medium",
        reliability="candidate",
    ),
    "runtime_opencode_deepseek32": Herramienta(
        id="runtime_opencode_deepseek32",
        engine="opencode:openrouter/deepseek/deepseek-v3.2",
        kind="runtime_agentico",
        role="agentic_cli_external",
        description="OpenCode con DeepSeek V3.2 via OpenRouter. Runtime externo para tareas agenticas.",
        strengths=("puede trabajar como agente CLI", "proveedor OpenRouter operativo"),
        weaknesses=("lento", "fallo parcial en test-17"),
        cost_level="medium",
        reliability="candidate",
    ),
    "gemini_flash_files": Herramienta(
        id="gemini_flash_files",
        engine="gemini:gemini-2.5-flash",
        kind="cli_agentico",
        role="long_context_files",
        description="Gemini CLI con Flash para archivos y contexto amplio moderado.",
        strengths=("contexto grande", "bueno con archivos", "latencia razonable"),
        weaknesses=("la salud de la clave/API debe vigilarse", "no sustituye al experto premium"),
        cost_level="medium",
        reliability="candidate",
    ),
    "gemini_pro_long_context": Herramienta(
        id="gemini_pro_long_context",
        engine="gemini:gemini-2.5-pro",
        kind="cli_agentico",
        role="very_long_context",
        description="Gemini Pro para cargas largas, muchos documentos o contexto muy grande.",
        strengths=("contexto muy grande", "bueno para documentos extensos", "subida de archivos"),
        weaknesses=("mas lento/caro que Flash", "validar disponibilidad segun cuenta"),
        cost_level="high",
        reliability="candidate",
    ),
    "premium_codex_55": Herramienta(
        id="premium_codex_55",
        engine="codex:gpt-5.5",
        kind="cli_agentico",
        role="judge_or_escalation",
        description="Codex CLI con GPT-5.5. Juez y escalado premium, no dependencia unica.",
        strengths=("mejor calidad observada", "agente de terminal completo"),
        weaknesses=("no debe ser el unico pilar del sistema"),
        cost_level="high",
        reliability="reference",
    ),
    "desktop_codex_operator": Herramienta(
        id="desktop_codex_operator",
        engine="desktop_codex:operator",
        kind="desktop_operator",
        role="visual_browser_last_resort",
        description="Codex Desktop operado por raton/teclado para navegador, logins, apps visuales y BotFather.",
        strengths=("usa sesiones reales", "puede operar navegador", "sirve para tareas autenticadas"),
        weaknesses=("requiere escritorio visible", "fragil ante cambios de UI", "debe tratar credenciales con mucho cuidado"),
        cost_level="high",
        reliability="experimental",
    ),
}


def get_tool(tool_id: str) -> Herramienta:
    try:
        return TOOLS[tool_id]
    except KeyError as exc:
        raise ValueError(f"Herramienta desconocida: {tool_id}") from exc
