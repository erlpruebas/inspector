from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from ..capabilities.catalog import ToolEntry
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
    "compare": "cap_compare",
    "data_filtering": "cap_calc_filter",
    "calculation": "cap_calc_filter",
    "draft": "cap_transform_redact",
    "email": "cap_transform_redact",
    "web_research": "cap_web_multi",
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
        compatible_tools = [tool.tool_id for tool in self.selector.compatible_tools(contract)]
        primary = self._primary_capability(record, contract)
        secondary = self._secondary_capabilities(record, contract, primary)
        objective_checks = self._objective_checks(record)
        rubric = record.rubric or self._default_rubric(record, contract)
        task_shape = contract.execute.operation.value
        return NormalizedTask(
            task_id=record.task_id,
            title=record.title,
            source_path=record.source_path,
            prompt=prompt,
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
        return NormalizedTaskReport(
            total_tasks=len(records),
            primary_capabilities=dict(primary_capabilities),
            compatible_tools=dict(compatible_tools),
            missing_rubrics=missing_rubrics,
            network_tasks=network_tasks,
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
            "calculate_report": "cap_calc_filter",
            "structured_calculation": "cap_calc_filter",
            "ocr_extraction": "cap_read_visual",
            "extract_from_image": "cap_read_visual",
            "code_execution": "cap_exec_tech",
            "artifact_modification": "cap_create_modify",
            "artifact_verification": "cap_verify",
        }
        if normalized in mapping:
            return mapping[normalized]
        if "memory" in normalized:
            return "cap_extract_short"
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
