from __future__ import annotations

from pathlib import Path

from .anonymizer import (
    AnonymizationResult,
    PrivacyRunResult,
    apply_privacy_to_path,
    apply_privacy_to_workdir,
    anonymize_text,
    hydrate_text,
)
from .detectors import DetectedEntity, detect_entities, is_private_path, should_process_text_file
from .entity_store import AliasRecord, EntityRecord, PrivacyEntityStore
from .mini_nano_review import MiniNanoPrivacyReviewer
from .verifier import VerificationResult, verify_redacted_text


DEFAULT_STORE_PATH = Path(__file__).resolve().parents[1] / "privacy_store" / "entity_map.jsonl"
PRIVACY_DIR_NAME = "privacy"

