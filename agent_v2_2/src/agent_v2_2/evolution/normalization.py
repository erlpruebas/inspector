from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from ..capabilities.catalog import ToolEntry, create_default_catalog
from ..models import Attachment
from ..routing.builder import ContractBuilder
from ..routing.contract import RequestContract
from ..routing.selector import CapabilitySelector
from .audit import TaskAuditReport, TaskAuditor, TaskRecord


SKILL_TO_CAPABILITY: Dict[str, str] = {
    "agenda": "cap_extract_short",
    "contacts": "cap_extract_short",
    "data_extraction": "cap_extract_long",
    "read_files": "cap_extract_long",
    "task_extraction": "cap_extract_long",
    "summarization": "cap_synth_long",
    "summary": "cap_synth_long",
    "reporting": "cap_synth_multi",
    "compare": "cap_compare",
    "compare_full_files_and_calculate": "cap_compare",
    "data_filtering": "cap_calc_filter",
    "calculation": "cap_calc_filter",
    "draft": "cap_transform_redact",
    "email": "cap_transform_redact",
    "ask_for_missing_information": "cap_transform_redact",
    "web_research": "cap_web_multi",
    "web_search": "cap_investigate",
    "single_web_lookup": "cap_web_punctual",
    "web": "cap_web_punctual",
    "audio": "cap_extract_long",
    "ocr": "cap_read_visual",
    "zip": "cap_inspect_zip",
    "code": "cap_exec_tech",
    "verify": "cap_verify",
}


FILE_TO_CAPABILITY: Dict[str, str] = {
    "pdf": "cap_read_pdf_bin",
    "docx": "cap_read_pdf_bin",
    "pptx": "cap_read_pdf_bin",
    "legacy_office": "cap_read_pdf_bin",
    "open_document": "cap_read_pdf_bin",
    "xlsx": "cap_calc_filter",
    "csv": "cap_calc_filter",
    "image": "cap_read_visual",
    "audio": "cap_extract_long",
    "zip": "cap_inspect_zip",
    "code": "cap_exec_tech",
    "email": "cap_transform_redact",
    "web": "cap_web_multi",
}


@dataclass
class NormalizedTask:
    task_id: str
    title: str
    source_path: Path
    prompt: str
    primary_capability: str
    secondary_capabilities: List[str] = field(default_factory=list)
    compatible_tools: List[str] = field(default_factory=list)
    objective_checks: List[str] = field(default_factory=list)
    judge_rubric: Dict[str, Any] = field(default_factory=dict)
    task_shape: str = ""
    route_hypothesis: str = ""
    required_files: List[str] = field(default_factory=list)
    expected_outputs: List[str] = field(default_factory=list)
    requires_network: bool = False
    dimensions: Dict[str, Any] = field(default_factory=dict)
    contract: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedTaskReport:
    total_tasks: int
    primary_capabilities: Dict[str, int]
    compatible_tools: Dict[str, int]
    missing_rubrics: int
    network_tasks: int
    missing_capabilities: List[str] = field(default_factory=list)
    records: List[NormalizedTask] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = [f"# Normalized task model ({self.total_tasks} tasks)", ""]
        lines.append("## Primary capabilities")
        for key, count in sorted(self.primary_capabilities.items()):
            lines.append(f"- {key}: {count}")
        lines.append("")
        lines.append("## Compatible tools")
        for key, count in sorted(self.compatible_tools.items()):
            lines.append(f"- {key}: {count}")
        lines.append("")
        lines.append(f"- missing rubrics: {self.missing_rubrics}")
        lines.append(f"- network tasks: {self.network_tasks}")
        lines.append("- missing capabilities:")
        if self.missing_capabilities:
            for capability in self.missing_capabilities:
                lines.append(f"  - {capability}")
        else:
            lines.append("  - none")
        lines.append("")
        lines.append("## Sample tasks")
        for task in self.records[:10]:
            tools = ", ".join(task.compatible_tools[:4]) or "none"
            secondary = ", ".join(task.secondary_capabilities) or "none"
            lines.append(f"- {task.task_id}: {task.primary_capability} | {secondary} | {tools}")
        return "\n".join(lines)


class TaskNormalizer:
    def __init__(
        self,
        *,
        selector: Optional[CapabilitySelector] = None,
        builder: Optional[ContractBuilder] = None,
    ) -> None:
        self.selector = selector or CapabilitySelector()
        self.builder = builder or ContractBuilder()

    def normalize_record(self, record: TaskRecord) -> NormalizedTask:
        prompt = self._prompt_for_record(record)
        attachments = self._attachments_for_record(record)
        contract = self.builder.build(
            prompt,
            attachments=attachments,
            metadata={
                "task_id": record.task_id,
                "source_path": str(record.source_path),
                "expected_operation": record.expected_operation,
                "route_hypothesis": record.route_hypothesis,
            },
        )
        primary = self._primary_capability(record, contract)
        contract = self._enrich_contract_for_capability(
            contract,
            primary,
            expected_operation=record.expected_operation,
        )
        compatible_tools = [tool.tool_id for tool in self.selector.compatible_tools(contract)]
        secondary = self._secondary_capabilities(record, contract, primary)
        objective_checks = self._objective_checks(record)
        rubric = record.rubric or self._default_rubric(record, contract)
        task_shape = contract.execute.operation.value
        return NormalizedTask(
            task_id=record.task_id,
            title=record.title,
            source_path=record.source_path,
            prompt=prompt,
            expected_outputs=list(record.expected_outputs),
            primary_capability=primary,
            secondary_capabilities=secondary,
            compatible_tools=compatible_tools,
            objective_checks=objective_checks,
            judge_rubric=rubric,
            task_shape=task_shape,
            route_hypothesis=record.route_hypothesis,
            required_files=list(record.required_files),
            requires_network=record.requires_network,
            dimensions=dict(record.dimensions),
            contract=contract.model_dump(mode="json"),
        )

    def _enrich_contract_for_capability(
        self,
        contract: RequestContract,
        primary: str,
        *,
        expected_operation: str = "",
    ) -> RequestContract:
        from ..routing.contract import (
            CognitiveRequirement,
            Guarantee,
            InstrumentalCapability,
            PrepareAction,
            PrepareActionType,
        )

        execute = contract.execute
        capabilities = list(execute.instrumental_capabilities)
        requirements = list(execute.cognitive_requirements)
        guarantees = list(execute.guarantees)
        prepare = list(contract.prepare)
        prepared_input = expected_operation.casefold() in {
            "memory_field_lookup",
            "memory_record_lookup",
            "retrieve_and_draft",
            "retrieve_style_and_draft",
            "multi_source_email_draft",
        }

        if prepared_input:
            capabilities = self._prepared_web_capabilities(capabilities)
            if InstrumentalCapability.PREPARED_TEXT not in capabilities:
                capabilities.append(InstrumentalCapability.PREPARED_TEXT)

        if primary in {"cap_web_multi", "cap_investigate"}:
            capabilities = self._prepared_web_capabilities(capabilities)
            capabilities = [
                capability
                for capability in capabilities
                if capability
                not in {
                    InstrumentalCapability.STRUCTURED_CALCULATION,
                    InstrumentalCapability.CODE_EXECUTION,
                    InstrumentalCapability.WRITE_FILE,
                }
            ]
            requirements = [
                requirement
                for requirement in requirements
                if requirement
                not in {
                    CognitiveRequirement.CAUSAL_DIAGNOSIS,
                    CognitiveRequirement.ARTIFACT_PLANNING,
                    CognitiveRequirement.MULTI_STEP_CALCULATION,
                }
            ]
            if InstrumentalCapability.MULTI_SOURCE_WEB_RESEARCH not in capabilities:
                capabilities.append(InstrumentalCapability.MULTI_SOURCE_WEB_RESEARCH)
            if InstrumentalCapability.LONG_CONTEXT not in capabilities:
                capabilities.append(InstrumentalCapability.LONG_CONTEXT)
            if CognitiveRequirement.SOURCE_EVALUATION not in requirements:
                requirements.append(CognitiveRequirement.SOURCE_EVALUATION)
            if not any(item.action == PrepareActionType.WEB_RESEARCH for item in prepare):
                prepare.append(
                    PrepareAction(
                        action=PrepareActionType.WEB_RESEARCH,
                        query=contract.normalized_request,
                        source_hint="web",
                        output_key="web_research_context",
                    )
                )
            for guarantee in (Guarantee.FRESH_INFORMATION, Guarantee.SOURCE_CITATIONS):
                if guarantee not in guarantees:
                    guarantees.append(guarantee)
        elif primary == "cap_web_punctual":
            capabilities = self._prepared_web_capabilities(capabilities)
            if InstrumentalCapability.CURRENT_WEB_LOOKUP not in capabilities:
                capabilities.append(InstrumentalCapability.CURRENT_WEB_LOOKUP)
            if not any(item.action == PrepareActionType.WEB_LOOKUP for item in prepare):
                prepare.append(
                    PrepareAction(
                        action=PrepareActionType.WEB_LOOKUP,
                        query=contract.normalized_request,
                        source_hint="web",
                        output_key="web_lookup_context",
                    )
                )
            if Guarantee.FRESH_INFORMATION not in guarantees:
                guarantees.append(Guarantee.FRESH_INFORMATION)

        updated_execute = execute.model_copy(
            update={
                "instrumental_capabilities": capabilities,
                "cognitive_requirements": requirements,
                "guarantees": guarantees,
                "file_requirements": (
                    []
                    if primary
                    in {"cap_web_multi", "cap_investigate", "cap_web_punctual"}
                    or prepared_input
                    else execute.file_requirements
                ),
            }
        )
        metadata = dict(contract.metadata)
        metadata["primary_capability"] = primary
        metadata["prepared_input"] = prepared_input
        return contract.model_copy(
            update={
                "prepare": prepare,
                "execute": updated_execute,
                "metadata": metadata,
            }
        )

    def _prepared_web_capabilities(self, capabilities):
        from ..routing.contract import InstrumentalCapability

        file_capabilities = {
            InstrumentalCapability.DISCOVER_FILES,
            InstrumentalCapability.READ_MULTIPLE_FILES,
            InstrumentalCapability.READ_TEXT_FILE,
            InstrumentalCapability.READ_BINARY_DOCUMENT,
            InstrumentalCapability.READ_SPREADSHEET,
            InstrumentalCapability.READ_IMAGE,
            InstrumentalCapability.READ_AUDIO,
            InstrumentalCapability.READ_ARCHIVE,
            InstrumentalCapability.PRESERVE_DOCUMENT_FORMAT,
        }
        return [
            capability
            for capability in capabilities
            if capability not in file_capabilities
        ]

    def normalize_records(self, records: Iterable[TaskRecord]) -> NormalizedTaskReport:
        normalized = [self.normalize_record(record) for record in records]
        return self._build_report(normalized)

    def normalize_audit(self, audit: TaskAuditReport) -> NormalizedTaskReport:
        return self.normalize_records(audit.records)

    def normalize_path(self, path: Path) -> NormalizedTaskReport:
        auditor = TaskAuditor()
        return self.normalize_records(auditor.load_records(auditor.collect_paths(path)))

    def _build_report(self, records: List[NormalizedTask]) -> NormalizedTaskReport:
        primary_capabilities = Counter(task.primary_capability for task in records)
        compatible_tools = Counter(tool for task in records for tool in task.compatible_tools)
        missing_rubrics = sum(1 for task in records if not task.judge_rubric)
        network_tasks = sum(1 for task in records if task.requires_network)
        declared_capabilities = {capability.id for capability in create_default_catalog().capabilities}
        missing_capabilities = sorted(declared_capabilities - set(primary_capabilities))
        return NormalizedTaskReport(
            total_tasks=len(records),
            primary_capabilities=dict(primary_capabilities),
            compatible_tools=dict(compatible_tools),
            missing_rubrics=missing_rubrics,
            network_tasks=network_tasks,
            missing_capabilities=missing_capabilities,
            records=records,
        )

    def _prompt_for_record(self, record: TaskRecord) -> str:
        return record.prompt or record.user_request or record.title

    def _attachments_for_record(self, record: TaskRecord) -> List[Attachment]:
        attachments: List[Attachment] = []
        for file_name in record.required_files:
            path = Path(file_name)
            attachments.append(
                Attachment(
                    kind=self._attachment_kind(path),
                    path=path,
                    label=path.name or file_name,
                    source="benchmark",
                )
            )
        return attachments

    def _attachment_kind(self, path: Path) -> str:
        suffix = path.suffix.casefold()
        if suffix in {".pdf", ".doc", ".docx", ".odt", ".rtf"}:
            return "document"
        if suffix in {".xls", ".xlsx", ".ods", ".csv"}:
            return "spreadsheet"
        if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".tif", ".tiff", ".heic"}:
            return "image"
        if suffix in {".mp3", ".wav", ".ogg", ".m4a"}:
            return "audio"
        if suffix in {".zip", ".rar", ".7z", ".tar", ".gz"}:
            return "archive"
        if suffix in {".eml", ".msg", ".mbox"}:
            return "email"
        if suffix in {".py", ".js", ".ts", ".html", ".css", ".sh", ".ps1", ".bat"}:
            return "code"
        return "text"

    def _primary_capability(self, record: TaskRecord, contract: RequestContract) -> str:
        if record.expected_operation:
            mapped = self._capability_from_operation(record.expected_operation)
            if mapped:
                return mapped
        if record.requires_network:
            prompt = f"{record.prompt} {record.user_request} {record.title}".casefold()
            if any(marker in prompt for marker in ("research", "investiga", "fuentes", "compila", "estado del arte")):
                return "cap_investigate"
            return "cap_web_punctual"
        if len(record.required_files) >= 2:
            prompt = f"{record.prompt} {record.user_request} {record.title}".casefold()
            if any(marker in prompt for marker in ("resume", "sintetiza", "sumariza", "report", "informe", "correo", "email", "draft")):
                return "cap_synth_multi"
            if any(marker in prompt for marker in ("compara", "diferencia", "mas caro", "mas barato")):
                return "cap_compare"
            if any(marker in prompt for marker in ("cruza", "relaciona", "consolida", "combina")):
                return "cap_extract_cross"
            return "cap_extract_cross"
        attachment_capability = self._attachment_primary_capability(record)
        if attachment_capability:
            return attachment_capability
        if record.skills:
            for skill in record.skills:
                mapped = SKILL_TO_CAPABILITY.get(skill.casefold())
                if mapped:
                    return mapped
        return str(contract.metadata.get("primary_capability") or "cap_extract_short")

    def _secondary_capabilities(
        self,
        record: TaskRecord,
        contract: RequestContract,
        primary: str,
    ) -> List[str]:
        candidates: List[str] = []
        for skill in record.skills:
            mapped = SKILL_TO_CAPABILITY.get(skill.casefold())
            if mapped:
                candidates.append(mapped)
        for requirement in contract.execute.file_requirements:
            mapped = FILE_TO_CAPABILITY.get(requirement.format.value)
            if mapped:
                candidates.append(mapped)
        seen = {primary}
        secondary: List[str] = []
        for capability in candidates:
            if capability in seen:
                continue
            seen.add(capability)
            secondary.append(capability)
        return secondary

    def _objective_checks(self, record: TaskRecord) -> List[str]:
        checks: List[str] = []
        if record.expected_operation:
            checks.append(f"operation:{record.expected_operation}")
        if record.expected_keys:
            checks.extend(f"contains:{key}" for key in record.expected_keys[:8])
        if record.expected_outputs:
            checks.extend(f"artifact:{output}" for output in record.expected_outputs[:8])
        if record.route_hypothesis:
            checks.append(f"route:{record.route_hypothesis}")
        return checks

    def _default_rubric(self, record: TaskRecord, contract: RequestContract) -> Dict[str, Any]:
        rubric: Dict[str, Any] = {
            "correctness": 4,
            "traceability": 2,
            "format": 2,
            "actionability": 2,
        }
        if record.requires_network or any(
            capability.value in {"current_web_lookup", "multi_source_web_research"}
            for capability in contract.execute.instrumental_capabilities
        ):
            rubric["source_quality"] = 2
        if contract.execute.file_requirements:
            rubric["file_fidelity"] = 2
        return rubric

    def _capability_from_operation(self, expected_operation: str) -> Optional[str]:
        normalized = expected_operation.casefold()
        mapping = {
            "memory_field_lookup": "cap_extract_short",
            "memory_record_lookup": "cap_extract_long",
            "retrieve_and_draft": "cap_transform_redact",
            "compare_documents": "cap_compare",
            "compare_spreadsheet": "cap_compare",
            "web_research": "cap_investigate",
            "web_lookup": "cap_web_punctual",
            "single_web_lookup": "cap_web_punctual",
            "url_lookup": "cap_web_punctual",
            "calculate_report": "cap_calc_filter",
            "structured_calculation": "cap_calc_filter",
            "ocr_extraction": "cap_read_visual",
            "extract_from_image": "cap_read_visual",
            "code_execution": "cap_exec_tech",
            "artifact_modification": "cap_create_modify",
            "artifact_verification": "cap_verify",
            "ask_for_missing_information": "cap_transform_redact",
            "long_text_synthesis": "cap_synth_long",
            "multi_document_synthesis": "cap_synth_multi",
        }
        if normalized in mapping:
            return mapping[normalized]
        if "memory" in normalized:
            return "cap_extract_short"
        if "research" in normalized or "investigate" in normalized:
            return "cap_investigate"
        if "draft" in normalized or "redact" in normalized:
            return "cap_transform_redact"
        if "compare" in normalized:
            return "cap_compare"
        if "calculate" in normalized or "calc" in normalized or "reconcile" in normalized:
            return "cap_calc_filter"
        if "web" in normalized or "search" in normalized:
            return "cap_web_multi" if "research" in normalized or "multi" in normalized else "cap_web_punctual"
        if "ocr" in normalized or "image" in normalized or "visual" in normalized:
            return "cap_read_visual"
        if "verify" in normalized:
            return "cap_verify"
        return None

    def _attachment_primary_capability(self, record: TaskRecord) -> Optional[str]:
        bucket_counts = Counter(self._attachment_kind(Path(file)) for file in record.required_files)
        if not bucket_counts:
            return None
        bucket = bucket_counts.most_common(1)[0][0]
        mapping = {
            "spreadsheet": "cap_calc_filter",
            "document": "cap_read_pdf_bin",
            "image": "cap_read_visual",
            "audio": "cap_extract_long",
            "archive": "cap_inspect_zip",
            "email": "cap_transform_redact",
            "code": "cap_exec_tech",
            "text": "cap_extract_long",
        }
        if bucket == "document":
            prompt = f"{record.prompt} {record.user_request} {record.title}".casefold()
            if any(marker in prompt for marker in ("web", "internet", "buscar", "busca", "buscar", "fuente", "investiga")):
                return "cap_web_multi"
            if any(marker in prompt for marker in ("resumen", "resume", "sintetiza", "consolida", "combina")):
                return "cap_synth_multi"
        return mapping.get(bucket)
