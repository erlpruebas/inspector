from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


CONTRACT_SCHEMA_VERSION = "1.0"


class PrepareActionType(str, Enum):
    MEMORY_LOOKUP = "memory_lookup"
    CONVERSATION_LOOKUP = "conversation_lookup"
    FIND_FILES = "find_files"
    READ_FILE_PART = "read_file_part"
    PREPARE_FILES = "prepare_files"
    EXTRACT_IMAGE_TEXT = "extract_image_text"
    TRANSCRIBE_AUDIO = "transcribe_audio"
    UNPACK_ARCHIVE = "unpack_archive"
    WEB_LOOKUP = "web_lookup"
    WEB_RESEARCH = "web_research"
    GET_CALENDAR_DATA = "get_calendar_data"
    GET_CONTACT_DATA = "get_contact_data"


class Operation(str, Enum):
    ANSWER = "answer"
    EXTRACT = "extract"
    CLASSIFY = "classify"
    REWRITE = "rewrite"
    SUMMARIZE = "summarize"
    COMPARE = "compare"
    CALCULATE = "calculate"
    RECONCILE = "reconcile"
    DIAGNOSE = "diagnose"
    PLAN = "plan"
    DRAFT = "draft"
    TRANSFORM = "transform"
    CREATE_ARTIFACT = "create_artifact"
    MODIFY_ARTIFACT = "modify_artifact"
    VERIFY_ARTIFACT = "verify_artifact"


class CognitiveLevel(str, Enum):
    NONE = "none"
    LIGHT = "light"
    GENERAL = "general"
    REASONING = "reasoning"


class CognitiveRequirement(str, Enum):
    EXACT_RETRIEVAL = "exact_retrieval"
    INSTRUCTION_FOLLOWING = "instruction_following"
    FIELD_EXTRACTION = "field_extraction"
    CLASSIFICATION = "classification"
    CONTROLLED_REWRITING = "controlled_rewriting"
    MULTI_ITEM_SYNTHESIS = "multi_item_synthesis"
    COMPARISON = "comparison"
    CONSTRAINT_SATISFACTION = "constraint_satisfaction"
    MULTI_STEP_CALCULATION = "multi_step_calculation"
    CAUSAL_DIAGNOSIS = "causal_diagnosis"
    SOURCE_EVALUATION = "source_evaluation"
    AMBIGUITY_DETECTION = "ambiguity_detection"
    ARTIFACT_PLANNING = "artifact_planning"
    SELF_VERIFICATION = "self_verification"


class InstrumentalCapability(str, Enum):
    PREPARED_TEXT = "prepared_text"
    CURRENT_WEB_LOOKUP = "current_web_lookup"
    MULTI_SOURCE_WEB_RESEARCH = "multi_source_web_research"
    READ_TEXT_FILE = "read_text_file"
    READ_BINARY_DOCUMENT = "read_binary_document"
    READ_SPREADSHEET = "read_spreadsheet"
    READ_IMAGE = "read_image"
    READ_AUDIO = "read_audio"
    READ_ARCHIVE = "read_archive"
    DISCOVER_FILES = "discover_files"
    READ_MULTIPLE_FILES = "read_multiple_files"
    STRUCTURED_CALCULATION = "structured_calculation"
    CODE_EXECUTION = "code_execution"
    WRITE_FILE = "write_file"
    PRESERVE_DOCUMENT_FORMAT = "preserve_document_format"
    LONG_CONTEXT = "long_context"


class Guarantee(str, Enum):
    EXACT_VALUES = "exact_values"
    FRESH_INFORMATION = "fresh_information"
    SOURCE_CITATIONS = "source_citations"
    ARTIFACT_EXISTS = "artifact_exists"
    ARTIFACT_VERIFIED = "artifact_verified"
    ASK_IF_MISSING = "ask_if_missing"
    HUMAN_CONFIRMATION = "human_confirmation"


class FileOperation(str, Enum):
    READ = "read"
    EXTRACT = "extract"
    CREATE = "create"
    MODIFY = "modify"
    PRESERVE = "preserve"
    VERIFY = "verify"


class FileFormat(str, Enum):
    TEXT = "text"
    MARKDOWN = "markdown"
    CSV = "csv"
    JSON = "json"
    XML = "xml"
    HTML = "html"
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    PPTX = "pptx"
    LEGACY_OFFICE = "legacy_office"
    OPEN_DOCUMENT = "open_document"
    IMAGE = "image"
    AUDIO = "audio"
    EMAIL = "email"
    ARCHIVE = "archive"
    CODE = "code"
    DIRECTORY = "directory"


class PrepareAction(BaseModel):
    action: PrepareActionType
    query: str = ""
    source_hint: str = ""
    output_key: str
    required: bool = True
    max_items: int = Field(default=5, ge=1, le=100)


class FileRequirement(BaseModel):
    format: FileFormat
    operations: List[FileOperation]
    count: int = Field(default=1, ge=1)
    preserve_format: bool = False

    @model_validator(mode="after")
    def validate_preservation(self) -> "FileRequirement":
        if self.preserve_format and FileOperation.PRESERVE not in self.operations:
            raise ValueError("preserve_format requires the preserve operation")
        return self


class ExecutionRequirements(BaseModel):
    operation: Operation
    cognitive_level: CognitiveLevel
    cognitive_requirements: List[CognitiveRequirement] = Field(default_factory=list)
    instrumental_capabilities: List[InstrumentalCapability] = Field(default_factory=list)
    file_requirements: List[FileRequirement] = Field(default_factory=list)
    guarantees: List[Guarantee] = Field(default_factory=list)
    expected_output: str = "text"


class RequestContract(BaseModel):
    schema_version: str = CONTRACT_SCHEMA_VERSION
    normalized_request: str
    prepare: List[PrepareAction] = Field(default_factory=list)
    execute: ExecutionRequirements
    ambiguity: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_contract(self) -> "RequestContract":
        if self.schema_version != CONTRACT_SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported request contract schema: {self.schema_version}"
            )

        output_keys = [action.output_key for action in self.prepare]
        if len(output_keys) != len(set(output_keys)):
            raise ValueError("Prepare action output_key values must be unique")

        actions = {action.action for action in self.prepare}
        capabilities = set(self.execute.instrumental_capabilities)
        guarantees = set(self.execute.guarantees)

        if PrepareActionType.WEB_RESEARCH in actions:
            if InstrumentalCapability.MULTI_SOURCE_WEB_RESEARCH not in capabilities:
                raise ValueError(
                    "web_research requires multi_source_web_research capability"
                )
        if PrepareActionType.WEB_LOOKUP in actions:
            if InstrumentalCapability.CURRENT_WEB_LOOKUP not in capabilities:
                raise ValueError("web_lookup requires current_web_lookup capability")
        if Guarantee.FRESH_INFORMATION in guarantees:
            if not actions.intersection(
                {PrepareActionType.WEB_LOOKUP, PrepareActionType.WEB_RESEARCH}
            ):
                raise ValueError(
                    "fresh_information requires a web lookup or web research action"
                )
        if self.ambiguity and Guarantee.ASK_IF_MISSING not in guarantees:
            raise ValueError("ambiguity requires the ask_if_missing guarantee")
        return self

    def required_accesses(self) -> set[str]:
        accesses = {
            capability.value
            for capability in self.execute.instrumental_capabilities
        }
        for requirement in self.execute.file_requirements:
            for operation in requirement.operations:
                accesses.add(f"{operation.value}:{requirement.format.value}")
        return accesses
