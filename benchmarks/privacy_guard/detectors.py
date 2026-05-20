from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Sequence

from .entity_store import AliasRecord, normalize_entity_type


@dataclass(frozen=True)
class DetectedEntity:
    start: int
    end: int
    text: str
    entity_type: str
    confidence: float = 1.0
    source: str = "regex"


EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b")
ID_RE = re.compile(r"\b(?:\d{8}[A-Z]|[XYZ]\d{7}[A-Z])\b", re.IGNORECASE)
URL_RE = re.compile(r"\b(?:https?://|www\.)[^\s<>()\"']+")
DATE_RE = re.compile(
    r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|"
    r"\d{1,2}\s+(?:de\s+)?(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|"
    r"octubre|noviembre|diciembre)\s+(?:de\s+)?\d{2,4})\b",
    re.IGNORECASE,
)
MONEY_RE = re.compile(r"(?:€\s?\d[\d.,]*|\d[\d.,]*\s?€)")
ADDRESS_RE = re.compile(
    r"\b(?:Calle|C/|Avda\.?|Avenida|Plaza|Paseo|Ronda|Camino|Via)\s+[A-ZÁÉÍÓÚÑ][^,\n]{0,80}?\d{1,5}\b",
    re.IGNORECASE,
)
PERSON_RE = re.compile(
    r"\b(?:[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+(?:[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+|de|del|la|las|los|y)){1,3})\b"
)
ORG_RE = re.compile(
    r"\b[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑ&.-]*(?:\s+[A-Z0-9][\wÁÉÍÓÚÑ&.-]*){0,4}\s+(?:SL|S\.L\.|SA|S\.A\.|LTD|INC|GROUP|CORP|CORPORATION)\b",
    re.IGNORECASE,
)

PERSON_STOPWORDS = {
    "Lunes",
    "Martes",
    "Miercoles",
    "Jueves",
    "Viernes",
    "Sabado",
    "Domingo",
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
}

ORG_KEYWORDS = {
    "SL",
    "S.L.",
    "SA",
    "S.A.",
    "CLINICA",
    "CENTRO",
    "CLINIC",
    "HEALTH",
    "LEGAL",
    "TECH",
    "SOLUTIONS",
    "GROUP",
    "LAB",
    "LABS",
    "CONSULTING",
    "CONSULTORIA",
    "CONSULTORIA",
    "INVERSIONES",
    "SERVICIOS",
    "CONSULTA",
    "CONSULTORIO",
    "HOSPITAL",
    "UNIVERSIDAD",
    "INSTITUTO",
    "EMPRESA",
}

ORG_SUFFIXES = {
    "SL",
    "S.L.",
    "SA",
    "S.A.",
    "LTD",
    "INC",
    "GMBH",
    "LLC",
    "SCOOP",
    "COOP",
    "CORP",
    "CORPORATION",
}

ORG_HINT_WORDS = {
    "CLINICA",
    "CENTRO",
    "HOSPITAL",
    "UNIVERSIDAD",
    "INSTITUTO",
    "CONSULTA",
    "CONSULTORIO",
    "LAB",
    "LABS",
    "LEGAL",
    "TECH",
    "SOLUTIONS",
    "SERVICIOS",
    "EMPRESA",
    "GROUP",
    "HEALTH",
    "CONSULTING",
    "CONSULTORIA",
    "FINANCE",
    "FINANZAS",
    "BANK",
    "BANCO",
    "GESTION",
    "GESTIÓN",
    "PROYECTOS",
    "STUDIO",
    "STUDIOS",
}

TEXT_PATTERNS = (
    ("EMAIL", EMAIL_RE, 0.99),
    ("PHONE", PHONE_RE, 0.95),
    ("BANK", IBAN_RE, 0.98),
    ("ID_NUMBER", ID_RE, 0.97),
    ("URL", URL_RE, 0.94),
    ("DATE", DATE_RE, 0.88),
    ("ADDRESS", ADDRESS_RE, 0.92),
    ("AMOUNT", MONEY_RE, 0.75),
)


def detect_entities(text: str, aliases: Sequence[AliasRecord] | None = None) -> list[DetectedEntity]:
    entities: list[DetectedEntity] = []
    if aliases:
        for alias in aliases:
            if not alias.alias.strip():
                continue
            regex = re.compile(re.escape(alias.alias), re.IGNORECASE)
            for match in regex.finditer(text):
                entities.append(
                    DetectedEntity(
                        start=match.start(),
                        end=match.end(),
                        text=match.group(0),
                        entity_type=normalize_entity_type(alias.entity_type),
                        confidence=max(0.8, float(alias.confidence)),
                        source="alias",
                    )
                )

    for entity_type, regex, confidence in TEXT_PATTERNS:
        for match in regex.finditer(text):
            entities.append(
                DetectedEntity(
                    start=match.start(),
                    end=match.end(),
                    text=match.group(0),
                    entity_type=entity_type,
                    confidence=confidence,
                    source="regex",
                )
            )

    for match in PERSON_RE.finditer(text):
        candidate = match.group(0).strip()
        if _looks_like_person(candidate):
            entities.append(
                DetectedEntity(
                    start=match.start(),
                    end=match.end(),
                    text=candidate,
                    entity_type="PERSON",
                    confidence=0.78,
                    source="heuristic",
                )
            )

    entities.extend(_scan_org_phrases(text))

    for match in ORG_RE.finditer(text):
        candidate = match.group(0).strip()
        if _looks_like_org(candidate):
            entities.append(
                DetectedEntity(
                    start=match.start(),
                    end=match.end(),
                    text=candidate,
                    entity_type="ORG",
                    confidence=0.82,
                    source="heuristic",
                )
            )

    return merge_entities(entities)


def merge_entities(entities: Iterable[DetectedEntity]) -> list[DetectedEntity]:
    ordered = sorted(
        list(entities),
        key=lambda entity: (-(entity.end - entity.start), -entity.confidence, entity.start),
    )
    accepted: list[DetectedEntity] = []
    occupied: list[tuple[int, int]] = []
    for entity in ordered:
        if any(_overlaps(entity.start, entity.end, start, end) for start, end in occupied):
            continue
        accepted.append(entity)
        occupied.append((entity.start, entity.end))
    return sorted(accepted, key=lambda entity: entity.start)


def is_private_path(path) -> bool:
    return "privacy" in getattr(path, "parts", [])


def should_process_text_file(path) -> bool:
    suffix = getattr(path, "suffix", "").lower()
    return suffix in {
        ".txt",
        ".md",
        ".markdown",
        ".csv",
        ".tsv",
        ".json",
        ".jsonl",
        ".yaml",
        ".yml",
        ".html",
        ".htm",
        ".xml",
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".ini",
        ".cfg",
        ".toml",
        ".log",
    }


def _looks_like_person(candidate: str) -> bool:
    if candidate in PERSON_STOPWORDS:
        return False
    if _contains_org_hints(candidate):
        return False
    if len(candidate.split()) < 2:
        return False
    if candidate.isupper():
        return False
    return True


def _looks_like_org(candidate: str) -> bool:
    upper = candidate.upper()
    words = [word.strip(".,;:()[]{}") for word in upper.split() if word.strip(".,;:()[]{}")]
    if len(words) < 2:
        return False
    if any(word in ORG_SUFFIXES for word in words):
        return True
    if any(word in ORG_HINT_WORDS for word in words):
        return True
    if any(keyword in upper for keyword in ORG_KEYWORDS) and len(words) >= 2:
        return True
    return False


def _contains_org_hints(candidate: str) -> bool:
    upper = candidate.upper()
    words = [word.strip(".,;:()[]{}") for word in upper.split() if word.strip(".,;:()[]{}")]
    return any(word in ORG_HINT_WORDS or word in ORG_SUFFIXES for word in words)


def _scan_org_phrases(text: str) -> list[DetectedEntity]:
    words: list[tuple[str, int, int]] = [
        (match.group(0), match.start(), match.end())
        for match in re.finditer(r"\b[\wÁÉÍÓÚÑáéíóúñ.-]+\b", text)
    ]
    detected: list[DetectedEntity] = []
    if len(words) < 2:
        return detected

    for start_index in range(len(words)):
        for length in range(2, 5):
            end_index = start_index + length
            if end_index > len(words):
                continue
            span_words = words[start_index:end_index]
            if not _looks_like_org_phrase(span_words):
                continue
            detected.append(
                DetectedEntity(
                    start=span_words[0][1],
                    end=span_words[-1][2],
                    text=" ".join(word for word, _, _ in span_words).strip(),
                    entity_type="ORG",
                    confidence=0.81,
                    source="heuristic",
                )
            )
    return detected


def _looks_like_org_phrase(span_words: list[tuple[str, int, int]]) -> bool:
    normalized = [word.upper().strip(".,;:()[]{}") for word, _, _ in span_words]
    if len(normalized) < 2:
        return False
    if not all(_is_allowed_org_word(word, index, len(normalized)) for index, word in enumerate(normalized)):
        return False
    if any(word in ORG_SUFFIXES for word in normalized):
        return True
    if normalized[0] in ORG_HINT_WORDS:
        return True
    if len(normalized) >= 2 and normalized[1] in ORG_HINT_WORDS and _looks_like_title_word(span_words[0][0]):
        return True
    return False


def _looks_like_title_word(word: str) -> bool:
    cleaned = word.strip(".,;:()[]{}")
    return bool(cleaned) and cleaned[0].isalpha() and cleaned[0].upper() == cleaned[0] and cleaned[1:].lower() == cleaned[1:]


def _is_allowed_org_word(word: str, index: int, total: int) -> bool:
    if word in ORG_HINT_WORDS or word in ORG_SUFFIXES:
        return True
    if _looks_like_title_word(word):
        return True
    if index not in {0, total - 1} and word in {"DE", "DEL", "LA", "LAS", "LOS", "Y", "E"}:
        return True
    return False


def _overlaps(start_a: int, end_a: int, start_b: int, end_b: int) -> bool:
    return not (end_a <= start_b or start_a >= end_b)
