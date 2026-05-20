from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable

from .detectors import DetectedEntity, detect_entities, is_private_path, should_process_text_file
from .entity_store import PrivacyEntityStore
from .mini_nano_review import MiniNanoPrivacyReviewer
from .verifier import VerificationResult, verify_redacted_text


TEXT_MODE_CHOICES = {"clear", "mixed", "redacted"}


@dataclass
class AnonymizationResult:
    source_path: str
    mode: str
    original_text: str
    mixed_text: str
    redacted_text: str
    entities: list[dict[str, Any]]
    verification: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PrivacyRunResult:
    root: str
    mode: str
    files_processed: int
    files_skipped: int
    entities_found: int
    verification_passed: bool
    residual_findings: list[dict[str, Any]]
    reviewer_used: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def anonymize_text(
    text: str,
    store: PrivacyEntityStore,
    *,
    mode: str = "redacted",
    reviewer: MiniNanoPrivacyReviewer | None = None,
) -> AnonymizationResult:
    if mode not in TEXT_MODE_CHOICES:
        raise ValueError(f"Unsupported privacy mode: {mode}")
    entities = detect_entities(text, aliases=store.iter_aliases())
    if reviewer is not None:
        try:
            proposals = reviewer.review(text)
        except Exception:
            proposals = []
        entities = _merge_entity_lists(entities, proposals)
    mixed_text, redacted_text, resolved = _render_variants(text, entities, store)
    verification = verify_redacted_text(redacted_text, store)
    output_text = {"clear": text, "mixed": mixed_text, "redacted": redacted_text}[mode]
    return AnonymizationResult(
        source_path="",
        mode=mode,
        original_text=text,
        mixed_text=mixed_text,
        redacted_text=redacted_text,
        entities=[_entity_to_dict(entity, store) for entity in resolved],
        verification=verification.to_dict(),
    )


def hydrate_text(text: str, store: PrivacyEntityStore) -> str:
    return store.hydrate_text(text)


def apply_privacy_to_workdir(
    workdir: Path,
    *,
    mode: str = "redacted",
    store_path: str | Path | None = None,
    reviewer: MiniNanoPrivacyReviewer | None = None,
) -> PrivacyRunResult:
    if mode not in TEXT_MODE_CHOICES:
        raise ValueError(f"Unsupported privacy mode: {mode}")
    if mode == "clear":
        return PrivacyRunResult(
            root=str(workdir),
            mode=mode,
            files_processed=0,
            files_skipped=0,
            entities_found=0,
            verification_passed=True,
            residual_findings=[],
            reviewer_used=False,
        )

    store = PrivacyEntityStore(store_path or default_store_path())
    privacy_root = _privacy_root_for_workdir(workdir)
    original_root = privacy_root / "original"
    mixed_root = privacy_root / "mixed"
    redacted_root = privacy_root / "redacted"
    report_root = privacy_root / "reports"
    for root in (original_root, mixed_root, redacted_root, report_root):
        root.mkdir(parents=True, exist_ok=True)

    files_processed = 0
    files_skipped = 0
    entities_found = 0
    residual_findings: list[dict[str, Any]] = []

    for path in sorted(workdir.rglob("*")):
        if not path.is_file():
            continue
        if is_private_path(path) or path.name in {"resultado.md", "usage.json", "_benchmark_prompt.md"}:
            continue
        if not should_process_text_file(path):
            files_skipped += 1
            continue
        try:
            original_text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            files_skipped += 1
            continue

        result = anonymize_text(original_text, store, mode=mode, reviewer=reviewer)
        relative = path.relative_to(workdir)
        original_target = original_root / relative
        mixed_target = mixed_root / relative
        redacted_target = redacted_root / relative
        for target, content in (
            (original_target, original_text),
            (mixed_target, result.mixed_text),
            (redacted_target, result.redacted_text),
        ):
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

        chosen = {"clear": original_text, "mixed": result.mixed_text, "redacted": result.redacted_text}[mode]
        path.write_text(chosen, encoding="utf-8")
        report = report_root / Path(f"{relative}.privacy.json")
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        entities_found += len(result.entities)
        if not result.verification.get("passed", False):
            residual_findings.extend(result.verification.get("findings", []))
        files_processed += 1

    run_report = {
        "root": str(workdir),
        "mode": mode,
        "files_processed": files_processed,
        "files_skipped": files_skipped,
        "entities_found": entities_found,
        "verification_passed": not residual_findings,
        "residual_findings": residual_findings,
        "reviewer_used": reviewer is not None,
    }
    (privacy_root / "report.json").write_text(json.dumps(run_report, ensure_ascii=False, indent=2), encoding="utf-8")
    return PrivacyRunResult(**run_report)


def apply_privacy_to_path(
    source: Path,
    *,
    out_dir: Path,
    mode: str = "redacted",
    store_path: str | Path | None = None,
    reviewer: MiniNanoPrivacyReviewer | None = None,
) -> AnonymizationResult:
    store = PrivacyEntityStore(store_path or default_store_path())
    text = source.read_text(encoding="utf-8", errors="replace")
    result = anonymize_text(text, store, mode=mode, reviewer=reviewer)
    out_dir.mkdir(parents=True, exist_ok=True)
    original_target = out_dir / "original" / source.name
    mixed_target = out_dir / "mixed" / source.name
    redacted_target = out_dir / "redacted" / source.name
    report_target = out_dir / "reports" / f"{source.name}.privacy.json"
    for target, content in (
        (original_target, text),
        (mixed_target, result.mixed_text),
        (redacted_target, result.redacted_text),
    ):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    report_target.parent.mkdir(parents=True, exist_ok=True)
    report_target.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def default_store_path() -> Path:
    return Path(__file__).resolve().parents[1] / "privacy_store" / "entity_map.jsonl"


def _privacy_root_for_workdir(workdir: Path) -> Path:
    try:
        run_root = workdir.parents[2]
    except IndexError:
        run_root = workdir.parent
    engine_name = workdir.parent.name
    task_name = workdir.name
    return run_root / "privacy" / engine_name / task_name


def _merge_entity_lists(primary: list[DetectedEntity], secondary: list[DetectedEntity]) -> list[DetectedEntity]:
    combined = [*primary, *secondary]
    ordered = sorted(
        combined,
        key=lambda entity: (-(entity.end - entity.start), -entity.confidence, entity.start),
    )
    accepted: list[DetectedEntity] = []
    occupied: list[tuple[int, int]] = []
    for entity in ordered:
        if any(not (entity.end <= start or entity.start >= end) for start, end in occupied):
            continue
        accepted.append(entity)
        occupied.append((entity.start, entity.end))
    return sorted(accepted, key=lambda entity: entity.start)


def _render_variants(
    text: str,
    entities: list[DetectedEntity],
    store: PrivacyEntityStore,
) -> tuple[str, str, list[DetectedEntity]]:
    if not entities:
        return text, text, []
    mixed = text
    redacted = text
    resolved: list[DetectedEntity] = []
    for entity in sorted(entities, key=lambda item: item.start, reverse=True):
        record = store.ensure(
            entity.entity_type,
            entity.text,
            source=entity.source,
            confidence=entity.confidence,
            alias=entity.text,
        )
        mixed = _replace_span(mixed, entity.start, entity.end, f"{entity.text} [{record.entity_id}]")
        redacted = _replace_span(redacted, entity.start, entity.end, record.entity_id)
        resolved.append(entity)
    return mixed, redacted, list(reversed(resolved))


def _replace_span(text: str, start: int, end: int, replacement: str) -> str:
    return text[:start] + replacement + text[end:]


def _entity_to_dict(entity: DetectedEntity, store: PrivacyEntityStore) -> dict[str, Any]:
    record = store.get(entity.entity_type, entity.text)
    token = record.entity_id if record is not None else ""
    return {
        "start": entity.start,
        "end": entity.end,
        "text": entity.text,
        "entity_type": entity.entity_type,
        "confidence": entity.confidence,
        "source": entity.source,
        "token": token,
    }
