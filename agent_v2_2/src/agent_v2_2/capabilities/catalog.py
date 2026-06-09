from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class AccessMethod(BaseModel):
    operation: str
    format: str
    support: str = "direct"


class Capability(BaseModel):
    id: str
    name: str
    description: str = ""


class CapabilityEvidence(BaseModel):
    mean_score: float
    samples: int
    pass_rate: float
    latency_median_seconds: float
    source: str


class ToolEntry(BaseModel):
    tool_id: str
    display_name: str
    invocation_type: str
    provider: str
    model: str = ""
    status: str = "active"
    selection_eligible: bool = True
    cognitive_max: str = "general"
    instrumental_capabilities: List[str] = Field(default_factory=list)
    cognitive_strengths: List[str] = Field(default_factory=list)
    best_for: List[str] = Field(default_factory=list)
    limits: List[str] = Field(default_factory=list)
    access_methods: List[AccessMethod] = Field(default_factory=list)
    observed_latency_seconds: Dict[str, Any] = Field(default_factory=dict)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    capability_scores: Dict[str, CapabilityEvidence] = Field(default_factory=dict)

    @property
    def tool_name(self) -> str:
        return self.tool_id

    @property
    def capabilities(self) -> List[str]:
        return self.instrumental_capabilities


class CapabilityCatalog(BaseModel):
    version: str = "2.2.0"
    source_of_truth: str = "orchestrator_v2_1/capability_catalog.json"
    capabilities: List[Capability]
    tools: List[ToolEntry]

    def get_tool(self, tool_id: str) -> ToolEntry | None:
        normalized = tool_id.casefold()
        return next(
            (tool for tool in self.tools if tool.tool_id.casefold() == normalized),
            None,
        )


def create_default_catalog() -> CapabilityCatalog:
    capabilities = [
        Capability(id="cap_extract_short", name="point extraction from short text"),
        Capability(id="cap_extract_long", name="point extraction from long document"),
        Capability(id="cap_extract_cross", name="cross-document extraction"),
        Capability(id="cap_synth_long", name="long-text synthesis"),
        Capability(id="cap_synth_multi", name="multi-document synthesis"),
        Capability(id="cap_compare", name="data or document comparison"),
        Capability(id="cap_calc_filter", name="structured calculation and filtering"),
        Capability(id="cap_transform_redact", name="data-grounded transformation and drafting"),
        Capability(id="cap_web_punctual", name="punctual web lookup"),
        Capability(id="cap_web_multi", name="multifactor web search"),
        Capability(id="cap_investigate", name="multi-source research and judgment"),
        Capability(id="cap_read_pdf_bin", name="PDF and binary-document reading"),
        Capability(id="cap_read_visual", name="visual reading and OCR"),
        Capability(id="cap_inspect_zip", name="folder and archive inspection"),
        Capability(id="cap_create_modify", name="file creation or modification"),
        Capability(id="cap_exec_tech", name="technical execution and diagnosis"),
        Capability(id="cap_verify", name="result verification"),
    ]
    tools = [
        _tool(
            "local_direct",
            "Local direct commands",
            "local",
            "local",
            cognitive_max="none",
            strengths=["exact_retrieval", "instruction_following"],
            best_for=["answer"],
            limits=["registered_commands_only"],
            latency={"median": 0.05, "mean": 0.05},
        ),
        _tool(
            "router_groq_qwen32",
            "Groq Qwen3 32B",
            "api",
            "groq",
            model="qwen/qwen3-32b",
            capabilities=["prepared_text", "structured_calculation"],
            strengths=[
                "field_extraction",
                "classification",
                "comparison",
                "constraint_satisfaction",
                "multi_step_calculation",
                "causal_diagnosis",
            ],
            best_for=["extract", "classify", "rewrite", "compare", "calculate", "draft"],
            latency={"median": 1.67, "mean": 1.95},
        ),
        _tool(
            "worker_openrouter_deepseek32",
            "OpenRouter DeepSeek V3.2",
            "api",
            "openrouter",
            model="deepseek/deepseek-v3.2",
            capabilities=["prepared_text", "structured_calculation", "long_context"],
            strengths=[
                "instruction_following",
                "multi_item_synthesis",
                "comparison",
                "controlled_rewriting",
                "artifact_planning",
            ],
            best_for=["summarize", "compare", "diagnose", "plan", "draft"],
            latency={"median": 3.8, "mean": 4.91},
        ),
        _tool(
            "worker_openrouter_gpt54mini",
            "OpenRouter GPT-5.4 mini",
            "api",
            "openrouter",
            model="openai/gpt-5.4-mini",
            status="experimental",
            eligible=False,
            cognitive_max="reasoning",
            capabilities=["prepared_text", "structured_calculation", "long_context"],
            strengths=[
                "multi_item_synthesis",
                "comparison",
                "constraint_satisfaction",
                "causal_diagnosis",
                "artifact_planning",
            ],
            best_for=["compare", "diagnose", "plan", "draft"],
            latency={"median": 5.82},
            evidence={"mean_score": 6.67, "passes": 3, "attempts": 6},
        ),
        _tool(
            "worker_groq_compound_mini",
            "Groq Compound Mini",
            "api",
            "groq",
            model="groq/compound-mini",
            capabilities=["prepared_text", "current_web_lookup", "code_execution"],
            strengths=["exact_retrieval", "field_extraction", "instruction_following"],
            best_for=["answer", "extract", "calculate"],
            limits=["one_tool_call"],
            latency={"median": 2.05, "mean": 2.26},
        ),
        _tool(
            "worker_groq_compound",
            "Groq Compound",
            "api",
            "groq",
            model="groq/compound",
            cognitive_max="reasoning",
            capabilities=[
                "prepared_text",
                "current_web_lookup",
                "multi_source_web_research",
                "code_execution",
            ],
            strengths=[
                "multi_item_synthesis",
                "comparison",
                "source_evaluation",
                "causal_diagnosis",
            ],
            best_for=["compare", "calculate", "diagnose", "plan"],
            latency={"median": 6.86, "mean": 8.72},
        ),
        _tool(
            "gemini_grounded_search",
            "Gemini grounded search",
            "api",
            "google",
            capabilities=[
                "prepared_text",
                "current_web_lookup",
                "multi_source_web_research",
                "long_context",
            ],
            strengths=[
                "exact_retrieval",
                "multi_item_synthesis",
                "comparison",
                "source_evaluation",
            ],
            best_for=["answer", "summarize", "compare", "draft"],
            latency={"median": 2.41, "mean": 2.98},
            evidence={"note": "Captured-web synthetic battery; live web can be slower."},
        ),
        _tool(
            "gemini_flash_files",
            "Gemini Flash files",
            "api",
            "google",
            capabilities=[
                "prepared_text",
                "read_text_file",
                "read_multiple_files",
                "long_context",
            ],
            strengths=[
                "field_extraction",
                "multi_item_synthesis",
                "comparison",
                "controlled_rewriting",
            ],
            best_for=["extract", "summarize", "compare", "draft"],
            latency={"median": 2.84, "mean": 3.58},
        ),
        _tool(
            "gemini_flash_35",
            "Gemini 3.5 Flash",
            "api",
            "google",
            model="gemini-3.5-flash",
            status="sampled",
            capabilities=[
                "prepared_text",
                "read_text_file",
                "read_binary_document",
                "read_image",
                "read_multiple_files",
                "write_file",
                "long_context",
            ],
            strengths=[
                "field_extraction",
                "multi_item_synthesis",
                "comparison",
                "controlled_rewriting",
                "instruction_following",
            ],
            best_for=["answer", "extract", "summarize", "compare", "draft"],
            latency={"median": 24.33, "mean": 23.51},
        ),
        _tool(
            "gemini_pro_long_context",
            "Gemini 3.1 Pro CLI",
            "cli",
            "google",
            model="gemini-3.1-pro-preview",
            status="demonstrated",
            cognitive_max="reasoning",
            capabilities=[
                "prepared_text",
                "read_text_file",
                "read_binary_document",
                "read_spreadsheet",
                "read_image",
                "read_audio",
                "read_archive",
                "discover_files",
                "read_multiple_files",
                "structured_calculation",
                "code_execution",
                "write_file",
                "preserve_document_format",
                "long_context",
            ],
            strengths=[
                "field_extraction",
                "multi_item_synthesis",
                "comparison",
                "constraint_satisfaction",
                "multi_step_calculation",
                "causal_diagnosis",
                "artifact_planning",
                "self_verification",
            ],
            best_for=[
                "summarize",
                "compare",
                "calculate",
                "reconcile",
                "diagnose",
                "plan",
                "draft",
                "create_artifact",
                "modify_artifact",
                "verify_artifact",
            ],
            latency={"median": 24.44, "mean": 27.95},
            evidence={
                "judge": "gemini-2.5-pro",
                "passed": 21,
                "attempts": 25,
                "mean_score": 8.42,
            },
        ),
        _tool(
            "runtime_opencode_deepseek32",
            "OpenCode DeepSeek V3.2",
            "opencode",
            "openrouter",
            model="deepseek/deepseek-v3.2",
            status="experimental",
            eligible=False,
            capabilities=[
                "prepared_text",
                "read_text_file",
                "discover_files",
                "read_multiple_files",
                "code_execution",
                "write_file",
                "long_context",
            ],
            strengths=[
                "multi_item_synthesis",
                "comparison",
                "causal_diagnosis",
                "artifact_planning",
            ],
            best_for=["diagnose", "plan", "create_artifact", "modify_artifact"],
            limits=["high_latency", "tool_support_varies_by_upstream_model"],
            latency={"typical_range": [92, 170]},
        ),
        _tool(
            "premium_codex_55",
            "Codex CLI GPT-5.5",
            "cli",
            "openai",
            model="gpt-5.5",
            status="demonstrated",
            cognitive_max="reasoning",
            capabilities=[
                "prepared_text",
                "read_text_file",
                "read_binary_document",
                "read_spreadsheet",
                "discover_files",
                "read_multiple_files",
                "structured_calculation",
                "code_execution",
                "write_file",
                "preserve_document_format",
                "long_context",
            ],
            strengths=[
                "multi_item_synthesis",
                "comparison",
                "constraint_satisfaction",
                "multi_step_calculation",
                "causal_diagnosis",
                "artifact_planning",
                "self_verification",
            ],
            best_for=[
                "calculate",
                "reconcile",
                "diagnose",
                "plan",
                "create_artifact",
                "modify_artifact",
                "verify_artifact",
            ],
            latency={"median": 51.88, "mean": 64.73},
            evidence={
                "judge": "gemini-2.5-pro",
                "passed": 23,
                "attempts": 25,
                "mean_score": 9.18,
            },
        ),
        _tool(
            "desktop_codex_operator",
            "Codex Desktop operator",
            "desktop",
            "openai",
            model="desktop_codex:operator",
            status="deferred",
            eligible=False,
            cognitive_max="reasoning",
            capabilities=["read_image", "write_file", "preserve_document_format"],
            strengths=["instruction_following", "artifact_planning", "self_verification"],
            best_for=["modify_artifact", "verify_artifact"],
            limits=["requires_human_confirmation", "visual_desktop_tasks_deferred"],
        ),
    ]
    return CapabilityCatalog(capabilities=capabilities, tools=tools)


def _tool(
    tool_id: str,
    display_name: str,
    invocation_type: str,
    provider: str,
    *,
    model: str = "",
    status: str = "active",
    eligible: bool = True,
    cognitive_max: str = "general",
    capabilities: List[str] | None = None,
    strengths: List[str] | None = None,
    best_for: List[str] | None = None,
    limits: List[str] | None = None,
    latency: Dict[str, Any] | None = None,
    evidence: Dict[str, Any] | None = None,
) -> ToolEntry:
    capability_list = capabilities or []
    return ToolEntry(
        tool_id=tool_id,
        display_name=display_name,
        invocation_type=invocation_type,
        provider=provider,
        model=model,
        status=status,
        selection_eligible=eligible,
        cognitive_max=cognitive_max,
        instrumental_capabilities=capability_list,
        cognitive_strengths=strengths or [],
        best_for=best_for or [],
        limits=limits or [],
        access_methods=_derive_access_methods(capability_list),
        observed_latency_seconds=latency or {},
        evidence=evidence or {},
    )


def _derive_access_methods(capabilities: List[str]) -> List[AccessMethod]:
    methods: set[tuple[str, str, str]] = set()

    def add(operation: str, formats: List[str], support: str = "direct") -> None:
        for file_format in formats:
            methods.add((operation, file_format, support))

    if "prepared_text" in capabilities:
        add("read", ["prepared_text"])
    if "read_text_file" in capabilities:
        add("read", ["text", "markdown", "csv", "json", "xml", "html", "code", "email"])
        add("extract", ["text", "markdown", "csv", "json", "xml", "html", "code", "email"])
    if "read_binary_document" in capabilities:
        add("read", ["pdf", "docx", "pptx", "legacy_office", "open_document"])
        add("extract", ["pdf", "docx", "pptx", "legacy_office", "open_document"])
    if "read_spreadsheet" in capabilities:
        add("read", ["xlsx", "csv"])
        add("extract", ["xlsx", "csv"])
    if "read_image" in capabilities:
        add("read", ["image"])
        add("extract", ["image"])
    if "read_audio" in capabilities:
        add("read", ["audio"])
        add("extract", ["audio"])
    if "read_archive" in capabilities:
        add("read", ["archive"])
        add("extract", ["archive"])
    if "discover_files" in capabilities:
        add("read", ["directory"])
    if "write_file" in capabilities:
        add(
            "create",
            [
                "text",
                "markdown",
                "csv",
                "json",
                "html",
                "pdf",
                "docx",
                "xlsx",
                "pptx",
                "code",
            ],
        )
        add(
            "modify",
            ["text", "markdown", "csv", "json", "html", "docx", "xlsx", "pptx", "code"],
        )
    if "preserve_document_format" in capabilities:
        add("preserve", ["docx", "xlsx", "pptx", "pdf"])
    if "code_execution" in capabilities:
        add("verify", ["code"])
    return [
        AccessMethod(operation=operation, format=file_format, support=support)
        for operation, file_format, support in sorted(methods)
    ]


def save_catalog(path: Path, catalog: CapabilityCatalog) -> None:
    path.write_text(catalog.model_dump_json(indent=2), encoding="utf-8")


def load_catalog(path: Path) -> CapabilityCatalog:
    return CapabilityCatalog.model_validate_json(path.read_text(encoding="utf-8"))
