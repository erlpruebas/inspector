from __future__ import annotations

from dataclasses import dataclass, asdict

from .detectors import detect_entities
from .entity_store import PrivacyEntityStore


@dataclass
class VerificationResult:
    passed: bool
    findings: list[dict[str, object]]
    entity_count: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def verify_redacted_text(text: str, store: PrivacyEntityStore | None = None) -> VerificationResult:
    aliases = store.iter_aliases() if store is not None else None
    entities = detect_entities(text, aliases=aliases)
    findings = [
        {
            "start": entity.start,
            "end": entity.end,
            "text": entity.text,
            "entity_type": entity.entity_type,
            "source": entity.source,
        }
        for entity in entities
    ]
    return VerificationResult(passed=not findings, findings=findings, entity_count=len(findings))

