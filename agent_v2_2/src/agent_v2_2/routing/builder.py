from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from ..models import Attachment
from .contract import (
    CognitiveLevel,
    CognitiveRequirement,
    ExecutionRequirements,
    FileFormat,
    FileOperation,
    FileRequirement,
    Guarantee,
    InstrumentalCapability,
    Operation,
    PrepareAction,
    PrepareActionType,
    RequestContract,
)


@dataclass(frozen=True)
class AttachmentDescriptor:
    kind: str
    path: Path
    label: str


class ContractBuilder:
    """Builds a canonical request contract from a user-facing message."""

    def build(
        self,
        text: str,
        *,
        attachments: Sequence[Attachment] | Sequence[AttachmentDescriptor] | None = None,
        metadata: Optional[dict] = None,
    ) -> RequestContract:
        normalized = self._normalize_text(text)
        attachment_descriptors = self._normalize_attachments(attachments or [])

        prepare = self._build_prepare_actions(normalized, attachment_descriptors)
        operation = self._infer_operation(normalized, attachment_descriptors)
        cognitive_level = self._infer_cognitive_level(normalized, operation, attachment_descriptors)
        instrumental_capabilities = self._infer_capabilities(normalized, operation, attachment_descriptors)
        file_requirements = self._build_file_requirements(
            normalized,
            operation,
            attachment_descriptors,
            instrumental_capabilities,
        )
        guarantees = self._infer_guarantees(normalized, operation, prepare, file_requirements)
        cognitive_requirements = self._infer_cognitive_requirements(
            normalized,
            operation,
            attachment_descriptors,
            guarantees,
        )
        ambiguity = self._infer_ambiguity(normalized, prepare, attachment_descriptors)
        confidence = self._infer_confidence(normalized, prepare, attachment_descriptors)
        primary_capability = self._primary_capability(operation, attachment_descriptors)

        contract_metadata = dict(metadata or {})
        contract_metadata.update(
            {
                "primary_capability": primary_capability,
                "attachment_count": len(attachment_descriptors),
            }
        )

        return RequestContract(
            normalized_request=normalized,
            prepare=prepare,
            execute=ExecutionRequirements(
                operation=operation,
                cognitive_level=cognitive_level,
                cognitive_requirements=cognitive_requirements,
                instrumental_capabilities=instrumental_capabilities,
                file_requirements=file_requirements,
                guarantees=guarantees,
                expected_output="text",
            ),
            ambiguity=ambiguity,
            confidence=confidence,
            metadata=contract_metadata,
        )

    def _normalize_text(self, text: str) -> str:
        return " ".join((text or "").split()).strip()

    def _normalize_attachments(
        self,
        attachments: Sequence[Attachment] | Sequence[AttachmentDescriptor],
    ) -> List[AttachmentDescriptor]:
        normalized: List[AttachmentDescriptor] = []
        for index, attachment in enumerate(attachments):
            if isinstance(attachment, AttachmentDescriptor):
                normalized.append(attachment)
                continue
            normalized.append(
                AttachmentDescriptor(
                    kind=str(attachment.kind),
                    path=Path(attachment.path),
                    label=str(attachment.label or f"attachment-{index + 1}"),
                )
            )
        return normalized

    def _build_prepare_actions(
        self,
        text: str,
        attachments: Sequence[AttachmentDescriptor],
    ) -> List[PrepareAction]:
        actions: List[PrepareAction] = []
        lower = text.casefold()

        if self._mentions_memory(lower):
            actions.append(
                PrepareAction(
                    action=PrepareActionType.MEMORY_LOOKUP,
                    query=text,
                    source_hint="memory",
                    output_key="memory_context",
                )
            )

        if self._mentions_files(lower) or attachments:
            actions.append(
                PrepareAction(
                    action=PrepareActionType.FIND_FILES,
                    query=text,
                    source_hint="workspace",
                    output_key="located_files",
                )
            )

        for index, attachment in enumerate(attachments, start=1):
            action = self._prepare_action_for_attachment(attachment)
            if action is None:
                continue
            actions.append(
                PrepareAction(
                    action=action,
                    query=attachment.label,
                    source_hint=str(attachment.path),
                    output_key=f"attachment_{index}",
                )
            )

        if self._mentions_web(lower):
            action = (
                PrepareActionType.WEB_RESEARCH
                if self._mentions_multi_source_web(lower)
                else PrepareActionType.WEB_LOOKUP
            )
            actions.append(
                PrepareAction(
                    action=action,
                    query=text,
                    source_hint="web",
                    output_key="web_context",
                )
            )

        return self._unique_actions(actions)

    def _prepare_action_for_attachment(
        self,
        attachment: AttachmentDescriptor,
    ) -> Optional[PrepareActionType]:
        kind = attachment.kind.casefold()
        suffix = attachment.path.suffix.casefold()
        if kind in {"voice", "audio"} or suffix in {".wav", ".mp3", ".m4a", ".ogg"}:
            return PrepareActionType.TRANSCRIBE_AUDIO
        if kind in {"photo", "image"} or suffix in {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".heic"}:
            return PrepareActionType.EXTRACT_IMAGE_TEXT
        if kind in {"document", "file"} or suffix in {".zip", ".7z", ".rar", ".tar"}:
            return PrepareActionType.UNPACK_ARCHIVE
        if suffix:
            return PrepareActionType.READ_FILE_PART
        return None

    def _infer_operation(
        self,
        text: str,
        attachments: Sequence[AttachmentDescriptor],
    ) -> Operation:
        lower = text.casefold()
        if self._contains_any(lower, ("verifica", "comprueba", "testea", "valida")):
            return Operation.VERIFY_ARTIFACT
        if self._contains_any(lower, ("modifica", "edita", "actualiza", "corrige", "cambia")):
            if self._contains_any(lower, ("informe", "resumen", "texto", "correo", "mensaje")):
                return Operation.DRAFT
            return Operation.MODIFY_ARTIFACT
        if self._contains_any(lower, ("crea", "genera", "redacta", "escribe", "prepara")):
            return Operation.CREATE_ARTIFACT
        if self._contains_any(lower, ("compara", "diferencia", "contrasta")):
            return Operation.COMPARE
        if self._contains_any(lower, ("calcula", "media", "suma", "resta", "beneficio", "gasto", "ventas")):
            return Operation.CALCULATE
        if self._contains_any(lower, ("reconcilia", "cuadra", "balancea")):
            return Operation.RECONCILE
        if self._contains_any(lower, ("diagnostica", "depura", "investiga", "causa", "fallo", "error")):
            return Operation.DIAGNOSE
        if self._contains_any(lower, ("resume", "sintetiza", "condensa")):
            return Operation.SUMMARIZE
        if self._contains_any(lower, ("clasifica", "identifica", "extrae", "busca")):
            return Operation.EXTRACT
        if attachments and self._contains_any(lower, ("lee", "abri", "abre", "revisa", "inspecciona", "mira", "consulta")):
            return Operation.EXTRACT
        if attachments:
            return Operation.EXTRACT
        if self._contains_any(lower, ("planifica", "prepara", "organiza", "propone")):
            return Operation.PLAN
        return Operation.ANSWER

    def _infer_cognitive_level(
        self,
        text: str,
        operation: Operation,
        attachments: Sequence[AttachmentDescriptor],
    ) -> CognitiveLevel:
        lower = text.casefold()
        if self._contains_any(lower, ("investiga", "compara fuentes", "varias fuentes", "estado del arte")):
            return CognitiveLevel.REASONING
        if operation in {Operation.RECONCILE, Operation.DIAGNOSE, Operation.PLAN, Operation.MODIFY_ARTIFACT}:
            return CognitiveLevel.REASONING
        if operation in {Operation.COMPARE, Operation.CALCULATE, Operation.DRAFT, Operation.CREATE_ARTIFACT, Operation.SUMMARIZE}:
            return CognitiveLevel.GENERAL
        if attachments and any(att.path.suffix.casefold() in {".pdf", ".docx", ".xlsx", ".pptx"} for att in attachments):
            return CognitiveLevel.GENERAL
        if self._mentions_memory(lower) or self._contains_any(lower, ("dime", "recupera", "encuentra")):
            return CognitiveLevel.LIGHT
        return CognitiveLevel.LIGHT if operation == Operation.ANSWER else CognitiveLevel.GENERAL

    def _infer_capabilities(
        self,
        text: str,
        operation: Operation,
        attachments: Sequence[AttachmentDescriptor],
    ) -> List[InstrumentalCapability]:
        lower = text.casefold()
        capabilities: List[InstrumentalCapability] = [InstrumentalCapability.PREPARED_TEXT]

        if self._mentions_web(lower):
            capabilities.append(InstrumentalCapability.CURRENT_WEB_LOOKUP)
        if self._mentions_multi_source_web(lower):
            capabilities.append(InstrumentalCapability.MULTI_SOURCE_WEB_RESEARCH)
        if self._mentions_files(lower) or attachments:
            capabilities.extend(
                [
                    InstrumentalCapability.DISCOVER_FILES,
                    InstrumentalCapability.READ_MULTIPLE_FILES,
                ]
            )
        if any(self._attachment_is_text(attachment) for attachment in attachments):
            capabilities.append(InstrumentalCapability.READ_TEXT_FILE)
        if any(self._attachment_is_binary_document(attachment) for attachment in attachments):
            capabilities.append(InstrumentalCapability.READ_BINARY_DOCUMENT)
        if any(self._attachment_is_spreadsheet(attachment) for attachment in attachments):
            capabilities.append(InstrumentalCapability.READ_SPREADSHEET)
            capabilities.append(InstrumentalCapability.STRUCTURED_CALCULATION)
        if any(self._attachment_is_image(attachment) for attachment in attachments):
            capabilities.append(InstrumentalCapability.READ_IMAGE)
        if any(self._attachment_is_audio(attachment) for attachment in attachments):
            capabilities.append(InstrumentalCapability.READ_AUDIO)
        if any(self._attachment_is_archive(attachment) for attachment in attachments):
            capabilities.append(InstrumentalCapability.READ_ARCHIVE)

        if operation in {Operation.CREATE_ARTIFACT, Operation.MODIFY_ARTIFACT, Operation.VERIFY_ARTIFACT}:
            capabilities.extend(
                [
                    InstrumentalCapability.WRITE_FILE,
                    InstrumentalCapability.CODE_EXECUTION,
                ]
            )
        if operation in {Operation.COMPARE, Operation.CALCULATE, Operation.RECONCILE, Operation.DIAGNOSE}:
            capabilities.append(InstrumentalCapability.STRUCTURED_CALCULATION)
        if operation in {Operation.CREATE_ARTIFACT, Operation.MODIFY_ARTIFACT} and any(
            attachment.path.suffix.casefold() in {".docx", ".xlsx", ".pptx", ".pdf"}
            for attachment in attachments
        ):
            capabilities.append(InstrumentalCapability.PRESERVE_DOCUMENT_FORMAT)
        if operation in {Operation.SUMMARIZE, Operation.DRAFT, Operation.PLAN, Operation.COMPARE, Operation.RECONCILE, Operation.DIAGNOSE}:
            capabilities.append(InstrumentalCapability.LONG_CONTEXT)
        return self._unique_capabilities(capabilities)

    def _build_file_requirements(
        self,
        text: str,
        operation: Operation,
        attachments: Sequence[AttachmentDescriptor],
        capabilities: Sequence[InstrumentalCapability],
    ) -> List[FileRequirement]:
        file_requirements: List[FileRequirement] = []
        for attachment in attachments:
            file_format = self._infer_file_format(attachment)
            operations = [FileOperation.READ]
            if operation in {Operation.EXTRACT, Operation.SUMMARIZE, Operation.COMPARE, Operation.CALCULATE, Operation.RECONCILE, Operation.DIAGNOSE}:
                operations.append(FileOperation.EXTRACT)
            if operation in {Operation.CREATE_ARTIFACT, Operation.MODIFY_ARTIFACT, Operation.DRAFT}:
                operations.append(FileOperation.MODIFY)
            if operation in {Operation.CREATE_ARTIFACT, Operation.MODIFY_ARTIFACT, Operation.VERIFY_ARTIFACT}:
                operations.append(FileOperation.VERIFY)
            preserve_format = file_format in {
                FileFormat.DOCX,
                FileFormat.XLSX,
                FileFormat.PPTX,
                FileFormat.LEGACY_OFFICE,
                FileFormat.OPEN_DOCUMENT,
                FileFormat.PDF,
            } and operation in {Operation.CREATE_ARTIFACT, Operation.MODIFY_ARTIFACT}
            if preserve_format:
                operations.append(FileOperation.PRESERVE)
            file_requirements.append(
                FileRequirement(
                    format=file_format,
                    operations=self._unique_file_operations(operations),
                    count=1,
                    preserve_format=preserve_format,
                )
            )

        if not file_requirements and self._mentions_files(text.casefold()):
            file_requirements.append(
                FileRequirement(
                    format=FileFormat.DIRECTORY,
                    operations=[FileOperation.READ, FileOperation.EXTRACT],
                    count=1,
                )
            )

        if any(capability == InstrumentalCapability.PRESERVE_DOCUMENT_FORMAT for capability in capabilities):
            for requirement in file_requirements:
                if requirement.format in {
                    FileFormat.DOCX,
                    FileFormat.XLSX,
                    FileFormat.PPTX,
                    FileFormat.LEGACY_OFFICE,
                    FileFormat.OPEN_DOCUMENT,
                    FileFormat.PDF,
                }:
                    requirement.preserve_format = True
                    if FileOperation.PRESERVE not in requirement.operations:
                        requirement.operations.append(FileOperation.PRESERVE)

        return file_requirements

    def _infer_guarantees(
        self,
        text: str,
        operation: Operation,
        prepare: Sequence[PrepareAction],
        file_requirements: Sequence[FileRequirement],
    ) -> List[Guarantee]:
        lower = text.casefold()
        guarantees: List[Guarantee] = []
        if self._mentions_web(lower):
            guarantees.append(Guarantee.FRESH_INFORMATION)
            guarantees.append(Guarantee.SOURCE_CITATIONS)
        if operation in {Operation.CREATE_ARTIFACT, Operation.MODIFY_ARTIFACT}:
            guarantees.append(Guarantee.ARTIFACT_EXISTS)
        if operation == Operation.VERIFY_ARTIFACT:
            guarantees.append(Guarantee.ARTIFACT_VERIFIED)
        if self._is_ambiguous(lower, prepare, file_requirements):
            guarantees.append(Guarantee.ASK_IF_MISSING)
        return self._unique_guarantees(guarantees)

    def _infer_cognitive_requirements(
        self,
        text: str,
        operation: Operation,
        attachments: Sequence[AttachmentDescriptor],
        guarantees: Sequence[Guarantee],
    ) -> List[CognitiveRequirement]:
        lower = text.casefold()
        requirements: List[CognitiveRequirement] = [CognitiveRequirement.INSTRUCTION_FOLLOWING]
        if self._mentions_memory(lower):
            requirements.append(CognitiveRequirement.EXACT_RETRIEVAL)
        if operation in {Operation.EXTRACT, Operation.SUMMARIZE}:
            requirements.append(CognitiveRequirement.FIELD_EXTRACTION)
        if operation in {Operation.COMPARE, Operation.RECONCILE}:
            requirements.append(CognitiveRequirement.COMPARISON)
        if operation in {Operation.CALCULATE, Operation.RECONCILE}:
            requirements.append(CognitiveRequirement.MULTI_STEP_CALCULATION)
        if operation == Operation.DIAGNOSE:
            requirements.append(CognitiveRequirement.CAUSAL_DIAGNOSIS)
        if operation in {Operation.CREATE_ARTIFACT, Operation.MODIFY_ARTIFACT, Operation.PLAN, Operation.DRAFT}:
            requirements.append(CognitiveRequirement.ARTIFACT_PLANNING)
        if any(guess in guarantees for guess in (Guarantee.FRESH_INFORMATION, Guarantee.SOURCE_CITATIONS)):
            requirements.append(CognitiveRequirement.SOURCE_EVALUATION)
        if any(att.path.suffix.casefold() in {".pdf", ".docx", ".xlsx", ".pptx"} for att in attachments):
            requirements.append(CognitiveRequirement.MULTI_ITEM_SYNTHESIS)
        if operation == Operation.VERIFY_ARTIFACT:
            requirements.append(CognitiveRequirement.SELF_VERIFICATION)
        return self._unique_cognitive_requirements(requirements)

    def _infer_ambiguity(
        self,
        text: str,
        prepare: Sequence[PrepareAction],
        file_requirements: Sequence[FileRequirement],
    ) -> Optional[str]:
        if self._is_ambiguous(text, prepare, file_requirements):
            return "La peticion necesita una confirmacion minima antes de ejecutar la tarea."
        return None

    def _infer_confidence(
        self,
        text: str,
        prepare: Sequence[PrepareAction],
        attachments: Sequence[AttachmentDescriptor],
    ) -> float:
        score = 1.0
        if self._is_ambiguous(text, prepare, []):
            score -= 0.25
        if attachments:
            score -= 0.1
        if self._mentions_web(text):
            score -= 0.05
        return max(0.25, min(1.0, score))

    def _primary_capability(
        self,
        operation: Operation,
        attachments: Sequence[AttachmentDescriptor],
    ) -> str:
        if any(self._attachment_is_spreadsheet(attachment) for attachment in attachments):
            return "cap_calc_filter"
        if any(self._attachment_is_image(attachment) for attachment in attachments):
            return "cap_read_visual"
        if any(self._attachment_is_audio(attachment) for attachment in attachments):
            return "cap_read_audio"
        if any(self._attachment_is_archive(attachment) for attachment in attachments):
            return "cap_inspect_zip"
        mapping = {
            Operation.EXTRACT: "cap_extract_long",
            Operation.SUMMARIZE: "cap_synth_long",
            Operation.COMPARE: "cap_compare",
            Operation.CALCULATE: "cap_calc_filter",
            Operation.RECONCILE: "cap_calc_filter",
            Operation.DIAGNOSE: "cap_exec_tech",
            Operation.PLAN: "cap_transform_redact",
            Operation.DRAFT: "cap_transform_redact",
            Operation.CREATE_ARTIFACT: "cap_create_modify",
            Operation.MODIFY_ARTIFACT: "cap_create_modify",
            Operation.VERIFY_ARTIFACT: "cap_verify",
        }
        return mapping.get(operation, "cap_extract_short")

    def _infer_file_format(self, attachment: AttachmentDescriptor) -> FileFormat:
        kind = attachment.kind.casefold()
        suffix = attachment.path.suffix.casefold()
        if kind in {"voice", "audio"} or suffix in {".wav", ".mp3", ".m4a", ".ogg"}:
            return FileFormat.AUDIO
        if kind in {"photo", "image"} or suffix in {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".heic"}:
            return FileFormat.IMAGE
        if suffix in {".pdf"}:
            return FileFormat.PDF
        if suffix in {".docx"}:
            return FileFormat.DOCX
        if suffix in {".xlsx"}:
            return FileFormat.XLSX
        if suffix in {".pptx"}:
            return FileFormat.PPTX
        if suffix in {".doc", ".xls", ".ppt"}:
            return FileFormat.LEGACY_OFFICE
        if suffix in {".odt", ".ods", ".odp"}:
            return FileFormat.OPEN_DOCUMENT
        if suffix in {".csv"}:
            return FileFormat.CSV
        if suffix in {".json"}:
            return FileFormat.JSON
        if suffix in {".xml"}:
            return FileFormat.XML
        if suffix in {".html", ".htm"}:
            return FileFormat.HTML
        if suffix in {".md", ".txt", ".log", ".py", ".js", ".ts", ".ps1", ".sh", ".yaml", ".yml"}:
            return FileFormat.TEXT
        if suffix in {".zip", ".7z", ".rar", ".tar", ".gz"}:
            return FileFormat.ARCHIVE
        return FileFormat.DIRECTORY

    def _mentions_memory(self, text: str) -> bool:
        return self._contains_any(
            text,
            (
                "memoria",
                "recuerda",
                "recorda",
                "apunte",
                "agenda",
                "cita",
                "telefono",
                "direccion",
                "dirección",
                "dato",
            ),
        )

    def _mentions_files(self, text: str) -> bool:
        return self._contains_any(
            text,
            (
                "archivo",
                "archivo",
                "documento",
                "pdf",
                "excel",
                "hoja",
                "carpeta",
                "zip",
                "foto",
                "imagen",
                "audio",
                "correo",
                "gmail",
            ),
        )

    def _mentions_web(self, text: str) -> bool:
        return self._contains_any(text, ("web", "internet", "busca", "buscar", "actual", "hoy", "online"))

    def _mentions_multi_source_web(self, text: str) -> bool:
        return self._contains_any(
            text,
            (
                "investiga",
                "varias fuentes",
                "fuentes",
                "compila",
                "compilar",
                "benchmark",
                "estado del arte",
            ),
        )

    def _is_ambiguous(
        self,
        text: str,
        prepare: Sequence[PrepareAction],
        file_requirements: Sequence[FileRequirement],
    ) -> bool:
        if len(text.split()) < 3:
            return True
        if not prepare and not file_requirements and self._contains_any(text, ("esto", "eso", "lo", "algo")):
            return True
        return False

    def _attachment_is_text(self, attachment: AttachmentDescriptor) -> bool:
        return attachment.path.suffix.casefold() in {".txt", ".md", ".csv", ".json", ".xml", ".html", ".htm", ".log", ".py", ".js", ".ts", ".ps1", ".sh", ".yaml", ".yml"}

    def _attachment_is_binary_document(self, attachment: AttachmentDescriptor) -> bool:
        return attachment.path.suffix.casefold() in {".pdf", ".docx", ".pptx", ".doc", ".xls", ".ppt", ".odt", ".ods", ".odp"}

    def _attachment_is_spreadsheet(self, attachment: AttachmentDescriptor) -> bool:
        return attachment.path.suffix.casefold() in {".xlsx", ".xls", ".csv", ".ods"}

    def _attachment_is_image(self, attachment: AttachmentDescriptor) -> bool:
        return attachment.path.suffix.casefold() in {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".heic"}

    def _attachment_is_audio(self, attachment: AttachmentDescriptor) -> bool:
        return attachment.path.suffix.casefold() in {".wav", ".mp3", ".m4a", ".ogg"}

    def _attachment_is_archive(self, attachment: AttachmentDescriptor) -> bool:
        return attachment.path.suffix.casefold() in {".zip", ".7z", ".rar", ".tar", ".gz"}

    def _contains_any(self, text: str, markers: Iterable[str]) -> bool:
        lower = text.casefold()
        return any(marker.casefold() in lower for marker in markers)

    def _unique_actions(self, actions: Sequence[PrepareAction]) -> List[PrepareAction]:
        seen: set[str] = set()
        unique: List[PrepareAction] = []
        for action in actions:
            key = action.output_key.casefold()
            if key in seen:
                continue
            seen.add(key)
            unique.append(action)
        return unique

    def _unique_capabilities(self, capabilities: Sequence[InstrumentalCapability]) -> List[InstrumentalCapability]:
        seen: set[InstrumentalCapability] = set()
        unique: List[InstrumentalCapability] = []
        for capability in capabilities:
            if capability in seen:
                continue
            seen.add(capability)
            unique.append(capability)
        return unique

    def _unique_file_operations(self, operations: Sequence[FileOperation]) -> List[FileOperation]:
        seen: set[FileOperation] = set()
        unique: List[FileOperation] = []
        for operation in operations:
            if operation in seen:
                continue
            seen.add(operation)
            unique.append(operation)
        return unique

    def _unique_guarantees(self, guarantees: Sequence[Guarantee]) -> List[Guarantee]:
        seen: set[Guarantee] = set()
        unique: List[Guarantee] = []
        for guarantee in guarantees:
            if guarantee in seen:
                continue
            seen.add(guarantee)
            unique.append(guarantee)
        return unique

    def _unique_cognitive_requirements(self, requirements: Sequence[CognitiveRequirement]) -> List[CognitiveRequirement]:
        seen: set[CognitiveRequirement] = set()
        unique: List[CognitiveRequirement] = []
        for requirement in requirements:
            if requirement in seen:
                continue
            seen.add(requirement)
            unique.append(requirement)
        return unique
