from __future__ import annotations

from pathlib import Path
import json


def build_profession_generation_prompt(title: str, description: str, task_count: int = 20) -> str:
    return f"""
Disena una profesion para el laboratorio ciego del gestor.

Profesion: {title}
Descripcion: {description}

Genera:
1. Contrato de profesion.
2. {task_count} tareas realistas, de dificultad progresiva.
3. Archivos sinteticos necesarios para cada tarea.
4. Respuesta correcta o criterios verificables.
5. Claves esperadas para evaluacion automatica.

Formato de salida:
- Un JSON con `profession`, `tasks` y `assets`.
- Cada tarea debe tener id, title, prompt, required_files, expected_keys, rubric, difficulty.
- Los archivos sinteticos deben tener path relativo y contenido completo.
No uses datos personales reales.
""".strip()


def write_generated_catalog(base_dir: Path, payload: dict) -> None:
    profession = payload.get("profession", {})
    profession_id = profession.get("id", "generated_profession")
    root = base_dir / profession_id
    tasks_root = root / "tasks"
    assets_root = root / "assets"
    root.mkdir(parents=True, exist_ok=True)
    tasks_root.mkdir(parents=True, exist_ok=True)
    assets_root.mkdir(parents=True, exist_ok=True)

    profession_md = render_profession_markdown(profession)
    (root / "profession.md").write_text(profession_md, encoding="utf-8")

    manifest = {
        "profession": profession,
        "source": payload.get("source", "generated"),
        "tasks_root": str(tasks_root.relative_to(root)),
        "task_count": len(payload.get("tasks", [])),
        "tasks": [],
    }
    index = []

    for task in payload.get("tasks", []):
        task_dir = tasks_root / task["id"]
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "metadata.json").write_text(json.dumps(task, indent=2, ensure_ascii=False), encoding="utf-8")
        (task_dir / "contract.md").write_text(render_task_markdown(task), encoding="utf-8")
        if task.get("reference"):
            (task_dir / "reference.md").write_text(str(task["reference"]), encoding="utf-8")
        manifest["tasks"].append(
            {
                "id": task.get("id", ""),
                "title": task.get("title", ""),
                "difficulty": task.get("difficulty", 0),
                "level": task.get("level", ""),
                "category": task.get("category", ""),
                "folder": f"tasks/{task.get('id', '')}",
                "metadata": f"tasks/{task.get('id', '')}/metadata.json",
                "contract": f"tasks/{task.get('id', '')}/contract.md",
                "reference": f"tasks/{task.get('id', '')}/reference.md",
            }
        )
        index.append(
            {
                "id": task.get("id", ""),
                "title": task.get("title", ""),
                "difficulty": task.get("difficulty", 0),
                "level": task.get("level", ""),
            }
        )

    for asset in payload.get("assets", []):
        path = assets_root / asset["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(asset.get("content", "")), encoding="utf-8")

    (root / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (root / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")


def render_profession_markdown(profession: dict) -> str:
    scope = "\n".join(f"- {item}" for item in profession.get("scope", []))
    constraints = "\n".join(f"- {item}" for item in profession.get("constraints", []))
    dimensions = "\n".join(f"- {item}" for item in profession.get("evaluation_dimensions", []))
    return f"""# Profession Contract

## Id
{profession.get("id", "generated_profession")}

## Title
{profession.get("title", "")}

## Description
{profession.get("description", "")}

## Scope
{scope}

## Constraints
{constraints}

## Evaluation Dimensions
{dimensions}

## Output Standard
{profession.get("output_standard", "Respuesta util, trazable y verificable.")}
"""


def render_task_markdown(task: dict) -> str:
    files = "\n".join(f"- {item}" for item in task.get("required_files", []))
    keys = "\n".join(f"- {item}" for item in task.get("expected_keys", []))
    return f"""# Task Contract

## Id
{task.get("id", "")}

## Title
{task.get("title", "")}

## Prompt
{task.get("prompt", "")}

## Required Files
{files}

## Expected Keys
{keys}

## Rubric
{json.dumps(task.get("rubric", {}), indent=2, ensure_ascii=False)}
"""
