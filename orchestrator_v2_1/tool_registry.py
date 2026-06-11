from __future__ import annotations

from .models import ToolSpec


TOOLS: dict[str, ToolSpec] = {
    "local_direct": ToolSpec(
        id="local_direct",
        tier=1,
        channel="local",
        engine="local:direct",
        role="manual_smoke_test",
        description="Manual deterministic smoke-test route. It is not selected by the LLM router for normal user requests.",
    ),
    "router_groq_qwen32": ToolSpec(
        id="router_groq_qwen32",
        tier=2,
        channel="api",
        engine="groq:qwen/qwen3-32b",
        role="fast_general_worker",
        description="Fast Groq worker for short general tasks.",
    ),
    "worker_openrouter_deepseek32": ToolSpec(
        id="worker_openrouter_deepseek32",
        tier=2,
        channel="api",
        engine="openrouter:deepseek/deepseek-v3.2",
        role="cheap_api_worker",
        description="Cheap API worker for compact tasks and files.",
    ),
    "worker_openrouter_gpt54mini": ToolSpec(
        id="worker_openrouter_gpt54mini",
        tier=3,
        channel="api",
        engine="openrouter:openai/gpt-5.4-mini",
        role="reasoning_worker",
        description="Reasoning API worker for synthesis and executive analysis.",
    ),
    "worker_groq_compound_mini": ToolSpec(
        id="worker_groq_compound_mini",
        tier=3,
        channel="api",
        engine="groq:groq/compound-mini",
        role="web_research_worker",
        description="Tool-capable Groq runtime for web-style research tasks.",
    ),
    "gemini_grounded_search": ToolSpec(
        id="gemini_grounded_search",
        tier=3,
        channel="api",
        engine="gemini_grounded:gemini-2.5-flash",
        role="grounded_web_research_worker",
        description="Gemini API with Google Search grounding for weather, current facts, and sourced web research.",
    ),
    "gemini_flash_files": ToolSpec(
        id="gemini_flash_files",
        tier=3,
        channel="agentic_cli",
        engine="gemini:gemini-2.5-flash",
        role="file_context_worker",
        description="Gemini Flash for files and moderate long context.",
    ),
    "gemini_pro_long_context": ToolSpec(
        id="gemini_pro_long_context",
        tier=4,
        channel="agentic_cli",
        engine="gemini:gemini-2.5-pro",
        role="very_long_context_worker",
        description="Gemini Pro for very long context and large document sets.",
    ),
    "runtime_opencode_deepseek32": ToolSpec(
        id="runtime_opencode_deepseek32",
        tier=4,
        channel="agentic_cli",
        engine="opencode:openrouter/deepseek/deepseek-v3.2",
        role="runtime_agent",
        description="OpenCode runtime for multi-step code or terminal work.",
    ),
    "premium_codex_55": ToolSpec(
        id="premium_codex_55",
        tier=4,
        channel="agentic_cli",
        engine="codex:gpt-5.5",
        role="premium_closure",
        description="Premium Codex CLI escalation for high-value closure.",
    ),
    "desktop_codex_operator": ToolSpec(
        id="desktop_codex_operator",
        tier=5,
        channel="desktop",
        engine="desktop_codex:operator",
        role="visual_desktop_operator",
        description="Codex Desktop visual operator. The only tool allowed to create screenshots.",
        requires_confirmation=True,
    ),
}


def get_tool(tool_id: str) -> ToolSpec:
    try:
        return TOOLS[tool_id]
    except KeyError as exc:
        raise ValueError(f"Unknown tool: {tool_id}") from exc
