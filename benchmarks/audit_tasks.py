from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from task_loader import ASSETS_DIR


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit benchmark task design and architecture consistency.")
    parser.add_argument("--tasks-file", default="benchmarks/tasks/assistant_tasks.json")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    tasks_file = Path(args.tasks_file)
    report = audit_tasks(tasks_file)
    text = format_report(tasks_file, report)
    output = Path(args.output) if args.output else tasks_file.with_name(tasks_file.stem + "_audit.md")
    output.write_text(text, encoding="utf-8")
    print(text)
    print(f"saved={output}")
    return 0 if not report["errors"] else 1


def audit_tasks(tasks_file: Path) -> dict[str, Any]:
    raw = json.loads(tasks_file.read_text(encoding="utf-8"))
    errors: list[str] = []
    warnings: list[str] = []
    info: list[str] = []

    if not isinstance(raw, list):
        return {"errors": ["tasks file must contain a JSON list"], "warnings": [], "info": [], "stats": {}}

    ids = [str(task.get("id", "")) for task in raw if isinstance(task, dict)]
    duplicate_ids = [task_id for task_id, count in Counter(ids).items() if count > 1]
    for task_id in duplicate_ids:
        errors.append(f"{task_id}: id duplicado")

    levels = Counter()
    network_count = 0
    skills = Counter()
    for index, task in enumerate(raw, start=1):
        if not isinstance(task, dict):
            errors.append(f"item {index}: no es un objeto JSON")
            continue
        task_id = str(task.get("id", f"item-{index}"))
        prompt = str(task.get("prompt", ""))
        required_files = [str(item) for item in task.get("required_files", [])]
        expected_outputs = [str(item) for item in task.get("expected_outputs", [])]
        expected_keys = [str(item) for item in task.get("expected_keys", [])]
        task_skills = [str(item) for item in task.get("skills", [])]
        level = str(task.get("level", ""))
        requires_network = bool(task.get("requires_network", False))

        if not re.fullmatch(r"test-\d{2}|[a-z0-9_-]+", task_id):
            warnings.append(f"{task_id}: id con formato poco estable")
        if not prompt.strip():
            errors.append(f"{task_id}: falta prompt")
        if not level:
            warnings.append(f"{task_id}: falta level")
        else:
            levels[level] += 1
        if not expected_outputs:
            warnings.append(f"{task_id}: falta expected_outputs")
        if len(expected_keys) < 3:
            warnings.append(f"{task_id}: expected_keys tiene menos de 3 elementos")
        if requires_network:
            network_count += 1
        if requires_network and "web_search" not in task_skills:
            warnings.append(f"{task_id}: requires_network=true pero skills no incluye web_search")
        if "web_search" in task_skills and not requires_network:
            warnings.append(f"{task_id}: skills incluye web_search pero requires_network=false")
        for skill in task_skills:
            skills[skill] += 1

        for filename in required_files:
            source = ASSETS_DIR / filename
            if not source.exists():
                errors.append(f"{task_id}: asset no existe: {filename}")
            basename = Path(filename).name
            if basename not in prompt and filename not in prompt:
                warnings.append(f"{task_id}: el prompt no menciona explicitamente `{filename}`")

    stats = {
        "total_tasks": len(raw),
        "levels": dict(sorted(levels.items())),
        "network_tasks": network_count,
        "top_skills": skills.most_common(12),
    }
    if len(raw) == 30:
        info.append("dataset principal tiene 30 tareas")
    else:
        warnings.append(f"dataset tiene {len(raw)} tareas, no 30")
    return {"errors": errors, "warnings": warnings, "info": info, "stats": stats}


def format_report(tasks_file: Path, report: dict[str, Any]) -> str:
    lines = [
        "# Task Audit",
        "",
        f"Archivo: `{tasks_file}`",
        "",
        "## Resumen",
        "",
        f"- Tareas: {report['stats'].get('total_tasks', 0)}",
        f"- Tareas con web: {report['stats'].get('network_tasks', 0)}",
        f"- Errores: {len(report['errors'])}",
        f"- Avisos: {len(report['warnings'])}",
        "",
        "## Niveles",
        "",
    ]
    levels = report["stats"].get("levels", {})
    for level, count in levels.items():
        lines.append(f"- {level}: {count}")
    lines.extend(["", "## Habilidades mas frecuentes", ""])
    for skill, count in report["stats"].get("top_skills", []):
        lines.append(f"- {skill}: {count}")
    lines.extend(["", "## Errores", ""])
    lines.extend(f"- {item}" for item in report["errors"]) if report["errors"] else lines.append("- Ninguno")
    lines.extend(["", "## Avisos", ""])
    lines.extend(f"- {item}" for item in report["warnings"]) if report["warnings"] else lines.append("- Ninguno")
    lines.extend(["", "## Notas", ""])
    lines.extend(f"- {item}" for item in report["info"]) if report["info"] else lines.append("- Sin notas adicionales")
    return "\n".join(lines).strip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
