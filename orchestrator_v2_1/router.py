from __future__ import annotations

import re

from .llm_router import route_with_model
from .models import PrivacyMode, RouteDecision, TaskRequest
from .tool_registry import TOOLS


SENSITIVE_PATTERNS = (
    r"\b\d{8}[A-Z]\b",
    r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b",
    r"\b[\w.+-]+@[\w.-]+\.\w+\b",
    r"\b(?:\+34\s*)?[6789]\d{2}[\s.-]?\d{3}[\s.-]?\d{3}\b",
)


def choose_tool(request: TaskRequest) -> RouteDecision:
    privacy_mode, needs_privacy = privacy_for(request.text, request.privacy_mode)
    explicit_tool = explicit_tool_id(request.text.strip().casefold())
    if explicit_tool:
        return decision_for(
            explicit_tool,
            reason="Explicit user route.",
            privacy_mode=privacy_mode,
            needs_privacy_confirmation=needs_privacy,
        )
    return route_with_model(
        request,
        privacy_mode=privacy_mode,
        needs_privacy_confirmation=needs_privacy,
    )


def force_tool(tool_id: str, request: TaskRequest) -> RouteDecision:
    if tool_id not in TOOLS:
        raise ValueError(f"Unknown tool: {tool_id}")
    privacy_mode, needs_privacy = privacy_for(request.text, request.privacy_mode)
    return decision_for(
        tool_id,
        reason="Forced by caller.",
        privacy_mode=privacy_mode,
        needs_privacy_confirmation=needs_privacy,
    )


def decision_for(
    tool_id: str,
    *,
    reason: str,
    privacy_mode: PrivacyMode,
    needs_privacy_confirmation: bool,
    alternatives: tuple[str, ...] = (),
) -> RouteDecision:
    tool = TOOLS[tool_id]
    return RouteDecision(
        tool_id=tool.id,
        tier=tool.tier,
        reason=reason,
        privacy_mode=privacy_mode,
        needs_privacy_confirmation=needs_privacy_confirmation,
        alternatives=alternatives,
    )


def privacy_for(text: str, requested: PrivacyMode) -> tuple[PrivacyMode, bool]:
    if requested != "ask":
        return requested, False
    needs_confirmation = looks_sensitive(text)
    return ("redacted" if needs_confirmation else "clear"), needs_confirmation


def explicit_tool_id(lower: str) -> str:
    commands = {
        "/desktop ": "desktop_codex_operator",
        "desktop:": "desktop_codex_operator",
        "cd ": "desktop_codex_operator",
        "/codex ": "premium_codex_55",
        "codex:": "premium_codex_55",
        "/gemini ": "gemini_flash_files",
        "gemini:": "gemini_flash_files",
        "/research ": "gemini_grounded_search",
        "research:": "gemini_grounded_search",
        "/local ": "local_direct",
    }
    for prefix, tool_id in commands.items():
        if lower.startswith(prefix):
            return tool_id
    return ""


def looks_sensitive(text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in SENSITIVE_PATTERNS)
