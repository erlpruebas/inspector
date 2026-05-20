from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TOKEN_PREFIXES = {
    "PERSON": "PERSON",
    "ORG": "ORG",
    "ORGANIZATION": "ORG",
    "EMAIL": "EMAIL",
    "PHONE": "PHONE",
    "ADDRESS": "ADDRESS",
    "ID_NUMBER": "ID_NUMBER",
    "BANK": "BANK",
    "IBAN": "BANK",
    "DATE": "DATE",
    "URL": "URL",
    "LICENSE_PLATE": "LICENSE_PLATE",
    "CASE": "CASE",
    "CONTRACT": "CONTRACT",
    "OTHER": "ENTITY",
}


@dataclass(frozen=True)
class AliasRecord:
    entity_type: str
    alias: str
    token: str
    canonical_value: str
    confidence: float = 1.0


@dataclass
class EntityRecord:
    entity_id: str
    entity_type: str
    canonical_value: str
    normalized_value: str
    aliases: list[str] = field(default_factory=list)
    first_seen: str = ""
    last_seen: str = ""
    source: str = "detector"
    confidence: float = 1.0

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


class PrivacyEntityStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._records: list[EntityRecord] = []
        self._by_key: dict[tuple[str, str], EntityRecord] = {}
        self._by_token: dict[str, EntityRecord] = {}
        self._counters: dict[str, int] = {}
        self.load()

    def load(self) -> None:
        self._records = []
        self._by_key = {}
        self._by_token = {}
        self._counters = {}
        if not self.path.exists():
            return
        for raw_line in self.path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(raw, dict):
                continue
            record = EntityRecord(
                entity_id=str(raw.get("entity_id", "")),
                entity_type=str(raw.get("entity_type", "ENTITY")).upper(),
                canonical_value=str(raw.get("canonical_value", "")),
                normalized_value=str(raw.get("normalized_value", "")),
                aliases=[str(item) for item in raw.get("aliases", []) if str(item).strip()],
                first_seen=str(raw.get("first_seen", "")),
                last_seen=str(raw.get("last_seen", "")),
                source=str(raw.get("source", "detector")),
                confidence=float(raw.get("confidence", 1.0) or 1.0),
            )
            self._register_loaded(record)
        self._recompute_counters()

    def _register_loaded(self, record: EntityRecord) -> None:
        key = (record.entity_type, record.normalized_value)
        if key in self._by_key or record.entity_id in self._by_token:
            return
        self._records.append(record)
        self._by_key[key] = record
        self._by_token[record.entity_id] = record

    def _recompute_counters(self) -> None:
        self._counters = {}
        for record in self._records:
            prefix, number = _split_token(record.entity_id)
            if not prefix or number <= 0:
                continue
            current = self._counters.get(prefix, 0)
            if number > current:
                self._counters[prefix] = number

    def ensure(
        self,
        entity_type: str,
        value: str,
        *,
        source: str = "detector",
        confidence: float = 1.0,
        alias: str | None = None,
    ) -> EntityRecord:
        entity_type = normalize_entity_type(entity_type)
        canonical_value = value.strip()
        normalized_value = normalize_value(entity_type, canonical_value)
        key = (entity_type, normalized_value)
        now = _utc_now()
        existing = self._by_key.get(key)
        if existing is not None:
            updated = False
            if alias and alias not in existing.aliases:
                existing.aliases.append(alias)
                updated = True
            if confidence > existing.confidence:
                existing.confidence = confidence
                updated = True
            existing.last_seen = now
            if source and source != existing.source:
                existing.source = source
                updated = True
            if updated:
                self.save()
            return existing

        prefix = token_prefix(entity_type)
        next_index = self._counters.get(prefix, 0) + 1
        self._counters[prefix] = next_index
        entity_id = f"{prefix}_{next_index:04d}"
        record = EntityRecord(
            entity_id=entity_id,
            entity_type=entity_type,
            canonical_value=canonical_value,
            normalized_value=normalized_value,
            aliases=[alias] if alias and alias != canonical_value else [],
            first_seen=now,
            last_seen=now,
            source=source,
            confidence=float(confidence),
        )
        self._records.append(record)
        self._by_key[key] = record
        self._by_token[record.entity_id] = record
        self.save()
        return record

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps(record.to_json(), ensure_ascii=False) for record in self._records]
        self.path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    def get(self, entity_type: str, value: str) -> EntityRecord | None:
        key = (normalize_entity_type(entity_type), normalize_value(entity_type, value))
        return self._by_key.get(key)

    def get_by_token(self, token: str) -> EntityRecord | None:
        return self._by_token.get(token)

    def iter_aliases(self) -> list[AliasRecord]:
        aliases: list[AliasRecord] = []
        for record in self._records:
            aliases.append(
                AliasRecord(
                    entity_type=record.entity_type,
                    alias=record.canonical_value,
                    token=record.entity_id,
                    canonical_value=record.canonical_value,
                    confidence=record.confidence,
                )
            )
            for alias in record.aliases:
                aliases.append(
                    AliasRecord(
                        entity_type=record.entity_type,
                        alias=alias,
                        token=record.entity_id,
                        canonical_value=record.canonical_value,
                        confidence=record.confidence,
                    )
                )
        aliases.sort(key=lambda item: len(item.alias), reverse=True)
        return aliases

    def hydrate_text(self, text: str) -> str:
        if not text:
            return text
        ordered = sorted(self._records, key=lambda record: len(record.entity_id), reverse=True)
        result = text
        for record in ordered:
            result = result.replace(record.entity_id, record.canonical_value)
        return result


def token_prefix(entity_type: str) -> str:
    normalized = normalize_entity_type(entity_type)
    return TOKEN_PREFIXES.get(normalized, normalized or "ENTITY")


def normalize_entity_type(entity_type: str) -> str:
    cleaned = entity_type.strip().upper().replace("-", "_").replace(" ", "_")
    return TOKEN_PREFIXES.get(cleaned, cleaned)


def normalize_value(entity_type: str, value: str) -> str:
    cleaned = " ".join(value.strip().split())
    normalized = unicodedata.normalize("NFKD", cleaned)
    stripped = "".join(char for char in normalized if not unicodedata.combining(char))
    stripped = stripped.casefold()
    if normalize_entity_type(entity_type) in {"EMAIL", "URL"}:
        stripped = stripped.lower()
    if normalize_entity_type(entity_type) in {"PHONE", "BANK"}:
        stripped = "".join(char for char in stripped if char.isalnum() or char == "+")
    return stripped


def _split_token(token: str) -> tuple[str, int]:
    if "_" not in token:
        return "", 0
    prefix, number_text = token.rsplit("_", 1)
    try:
        return prefix, int(number_text)
    except ValueError:
        return "", 0


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

