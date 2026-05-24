from __future__ import annotations

import json
from pathlib import Path
import re

from .lab_contracts import LabPersona, ProfessionContract, TaskContract


ROOT = Path(".")
BENCHMARKS_ROOT = Path("benchmarks")
ASSETS_ROOT = BENCHMARKS_ROOT / "assets"


def load_profession_contract(profession_root: Path) -> ProfessionContract:
    path = profession_root / "profession.md"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    sections = parse_markdown_sections(text)
    return ProfessionContract(
        id=section_value(sections, "Id", profession_root.name),
        title=section_value(sections, "Title", profession_root.name),
        description=section_value(sections, "Description", ""),
        scope=tuple(section_list(sections, "Scope")),
        constraints=tuple(section_list(sections, "Constraints")),
        evaluation_dimensions=tuple(section_list(sections, "Evaluation Dimensions")),
        output_standard=section_value(sections, "Output Standard", ""),
        root=profession_root,
    )


def load_task_contracts(profession: ProfessionContract) -> list[TaskContract]:
    if not profession.root:
        return []
    tasks_root = profession.root / "tasks"
    tasks: list[TaskContract] = []
    for meta_path in sorted(tasks_root.glob("*/metadata.json")):
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        reference_path = meta_path.with_name("reference.md")
        reference = reference_path.read_text(encoding="utf-8") if reference_path.exists() else ""
        tasks.append(task_from_metadata(metadata, profession.id, reference))
    return tasks


def task_from_metadata(metadata: dict, profession_id: str, reference: str = "") -> TaskContract:
    required = tuple(resolve_asset_path(item) for item in metadata.get("required_files", []))
    return TaskContract(
        id=metadata["id"],
        title=metadata.get("title", metadata["id"]),
        prompt=metadata.get("prompt", ""),
        profession_id=profession_id,
        difficulty=int(metadata.get("difficulty", 2)),
        level=metadata.get("level", "L2"),
        category=metadata.get("category", ""),
        skills=tuple(metadata.get("skills", [])),
        required_files=required,
        expected_keys=tuple(metadata.get("expected_keys", [])),
        response_shape=metadata.get("response_shape", "respuesta util y trazable"),
        rubric=metadata.get("rubric", {}),
        reference=reference,
        metadata=metadata,
    )


def load_personas(path: Path = Path("benchmarks/assets/persona_daily_simulation/personas.json")) -> list[LabPersona]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        LabPersona(
            id=item["id"],
            name=item.get("name", item["id"]),
            profession=item.get("profession", ""),
            description=", ".join(item.get("daily_tools", [])),
            tone=item.get("tone", ""),
            risk=item.get("risk", ""),
            metadata=item,
        )
        for item in raw
    ]


def discover_profession_roots(base_dir: Path = Path("benchmarks/contracts")) -> list[Path]:
    roots: list[Path] = []
    if not base_dir.exists():
        return roots
    for path in sorted(base_dir.iterdir()):
        if path.is_dir() and (path / "profession.md").exists():
            roots.append(path)
    return roots


def discover_professions(base_dir: Path = Path("benchmarks/contracts")) -> list[ProfessionContract]:
    return [load_profession_contract(path) for path in discover_profession_roots(base_dir)]


def load_catalog(profession_id: str = "office_general") -> tuple[ProfessionContract, list[TaskContract], list[LabPersona]]:
    roots = {profession.id: profession for profession in discover_professions()}
    if profession_id not in roots:
        raise ValueError(f"Unknown profession id: {profession_id}")
    profession = roots[profession_id]
    return profession, load_task_contracts(profession), load_personas()


def load_office_catalog() -> tuple[ProfessionContract, list[TaskContract], list[LabPersona]]:
    return load_catalog("office_general")


def resolve_asset_path(raw: str) -> Path:
    path = Path(raw)
    if path.exists():
        return path
    candidate = ASSETS_ROOT / raw
    if candidate.exists():
        return candidate
    return candidate


def validate_task_files(tasks: list[TaskContract]) -> dict[str, list[str]]:
    missing: dict[str, list[str]] = {}
    for task in tasks:
        absent = [str(path) for path in task.required_files if not path.exists()]
        if absent:
            missing[task.id] = absent
    return missing


def profession_to_dict(profession: ProfessionContract) -> dict:
    return {
        "id": profession.id,
        "title": profession.title,
        "description": profession.description,
        "scope": list(profession.scope),
        "constraints": list(profession.constraints),
        "evaluation_dimensions": list(profession.evaluation_dimensions),
        "output_standard": profession.output_standard,
        "root": str(profession.root) if profession.root else "",
    }


def task_to_dict(task: TaskContract) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "prompt": task.prompt,
        "profession_id": task.profession_id,
        "difficulty": task.difficulty,
        "level": task.level,
        "category": task.category,
        "skills": list(task.skills),
        "required_files": [str(path) for path in task.required_files],
        "expected_keys": list(task.expected_keys),
        "response_shape": task.response_shape,
        "rubric": task.rubric,
        "reference": task.reference,
        "metadata": task.metadata,
    }


def parse_markdown_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current = ""
    for line in text.splitlines():
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            current = match.group(1).strip()
            sections[current] = []
            continue
        if current:
            sections[current].append(line)
    return {key: "\n".join(value).strip() for key, value in sections.items()}


def section_value(sections: dict[str, str], key: str, default: str) -> str:
    value = sections.get(key, "").strip()
    if not value:
        return default
    lines = [line.strip() for line in value.splitlines() if line.strip() and not line.strip().startswith("-")]
    return lines[0] if lines else default


def section_list(sections: dict[str, str], key: str) -> list[str]:
    lines = sections.get(key, "").splitlines()
    values = []
    for line in lines:
        clean = line.strip()
        if clean.startswith("-"):
            values.append(clean[1:].strip())
    return values
