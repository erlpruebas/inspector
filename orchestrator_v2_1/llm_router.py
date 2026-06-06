from __future__ import annotations

import json
import os
from typing import Any

import requests
from benchmarks.env_utils import load_env_files

from .models import RouteDecision, TaskRequest
from .tool_registry import TOOLS


ROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
ROUTABLE_TOOL_IDS = tuple(tool_id for tool_id in TOOLS if tool_id != "local_direct")


def route_with_model(
    request: TaskRequest,
    *,
    privacy_mode: str,
    needs_privacy_confirmation: bool,
) -> RouteDecision:
    load_env_files()
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        return default_decision(privacy_mode, needs_privacy_confirmation, "Router model unavailable: missing API key.")

    model = os.getenv("ORCH_ROUTER_MODEL", "openai/gpt-4o-mini").strip() or "openai/gpt-4o-mini"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": router_system_prompt(),
            },
            {
                "role": "user",
                "content": router_user_prompt(request),
            },
        ],
        "temperature": 0,
        "max_tokens": 350,
        "response_format": {"type": "json_object"},
    }
    try:
        response = requests.post(
            ROUTER_ENDPOINT,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "HTTP-Referer": "http://localhost/orchestrator-v2-1",
                "X-Title": "Orchestrator v2.1 Router",
            },
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        content = (((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
        parsed = json.loads(content)
        return decision_from_payload(parsed, privacy_mode, needs_privacy_confirmation)
    except Exception as exc:
        return default_decision(
            privacy_mode,
            needs_privacy_confirmation,
            f"Router model unavailable: {type(exc).__name__}.",
        )


def router_system_prompt() -> str:
    catalog = "\n".join(
        f"- {tool.id}: tier {tool.tier}, channel {tool.channel}, role {tool.role}. {tool.description}"
        for tool in TOOLS.values()
        if tool.id in ROUTABLE_TOOL_IDS
    )
    return f"""
You are the routing model for a personal assistant. Choose exactly one tool for the user's natural-language request.

Tool catalog:
{catalog}

Routing principles:
- Use the lowest tier that can genuinely solve the request.
- Short conversation, orchestrator status questions, memory acknowledgements, rewriting and ordinary reasoning go to worker_openrouter_deepseek32.
- Current information, weather, live facts and source-backed web research go to gemini_grounded_search.
- Files and moderate document context go to gemini_flash_files.
- Large document sets go to gemini_pro_long_context.
- Code, repository and terminal work go to runtime_opencode_deepseek32.
- Visual interfaces, authenticated browser sessions, maps, login, images and screen inspection go to desktop_codex_operator.
- A mere mention of an address, home, client, image, login or map does not require Desktop. Choose Desktop only when the requested action itself needs visual interaction, navigation, an authenticated session, or screen inspection.
- Deep strategic synthesis goes to worker_openrouter_gpt54mini.
- Do not choose Desktop for ordinary text research, writing, analysis or code.
- Memory context can change the route. For example, navigation from a remembered home address normally needs Desktop/maps.

Canonical examples:
- "estado" -> worker_openrouter_deepseek32
- "recuerda que mi casa está en Calle Luna 12" -> worker_openrouter_deepseek32
- "qué recuerdas de mi casa" -> worker_openrouter_deepseek32
- "qué tiempo hace hoy en Madrid" -> gemini_grounded_search
- "cómo llego desde mi casa al cliente" -> desktop_codex_operator
- "redacta un mensaje amable" -> worker_openrouter_deepseek32
- "implementa esta mejora en el repo" -> runtime_opencode_deepseek32

Return one JSON object only:
{{
  "tool_id": "one catalog id",
  "reason": "brief concrete reason",
  "alternatives": ["zero to two fallback tool ids"]
}}
""".strip()


def router_user_prompt(request: TaskRequest) -> str:
    facts = "\n".join(f"- {fact.label}: {fact.value}" for fact in request.memory_context.facts) or "- none"
    files = "\n".join(f"- {path.name}" for path in request.files) or "- none"
    return f"""
User request:
{request.text}

Relevant memory:
{facts}

Thread summary:
{request.memory_context.thread_summary or "none"}

Files:
{files}

Source:
{request.metadata.get("source", "unknown")}
""".strip()


def decision_from_payload(
    payload: dict[str, Any],
    privacy_mode: str,
    needs_privacy_confirmation: bool,
) -> RouteDecision:
    tool_id = str(payload.get("tool_id", "")).strip()
    if tool_id not in ROUTABLE_TOOL_IDS:
        return default_decision(privacy_mode, needs_privacy_confirmation, "Router returned an invalid tool.")
    tool = TOOLS[tool_id]
    alternatives = tuple(
        item
        for item in payload.get("alternatives", [])
        if isinstance(item, str) and item in ROUTABLE_TOOL_IDS and item != tool_id
    )[:2]
    return RouteDecision(
        tool_id=tool_id,
        tier=tool.tier,
        reason=str(payload.get("reason", "")).strip() or "Selected by routing model.",
        privacy_mode=privacy_mode,
        needs_privacy_confirmation=needs_privacy_confirmation,
        alternatives=alternatives,
    )


def default_decision(
    privacy_mode: str,
    needs_privacy_confirmation: bool,
    reason: str,
) -> RouteDecision:
    tool = TOOLS["worker_openrouter_deepseek32"]
    return RouteDecision(
        tool_id=tool.id,
        tier=tool.tier,
        reason=reason,
        privacy_mode=privacy_mode,
        needs_privacy_confirmation=needs_privacy_confirmation,
        alternatives=("worker_openrouter_gpt54mini",),
    )
