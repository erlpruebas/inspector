from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_TASKS = ROOT / "tasks" / "assistant_tasks.json"
SOURCE_INDEX = ROOT / "tasks" / "assistant_suite" / "index.json"
CONTRACT_ROOT = ROOT / "contracts" / "office_general"
TASKS_ROOT = CONTRACT_ROOT / "tasks"


PROFESSION = {
    "id": "office_general",
    "title": "Ofimatica transversal para asistente ejecutivo",
    "description": (
        "Conjunto de tareas de oficina y coordinacion que un ejecutivo o profesional "
        "puede delegar en un asistente: correo, agenda, documentos, tablas, seguimiento, "
        "priorizacion y reportes."
    ),
    "scope": [
        "emails",
        "agenda",
        "documentos",
        "tablas",
        "seguimiento",
        "priorizacion",
        "reportes",
        "archivo sintetico",
    ],
    "constraints": [
        "No inventar datos.",
        "Priorizar trazabilidad y claridad.",
        "Pedir aclaracion si falta un dato esencial.",
        "Mantener tono profesional y util.",
    ],
    "evaluation_dimensions": [
        "correctness",
        "format",
        "traceability",
        "tone",
        "completeness",
    ],
}


def main() -> int:
    tasks = load_source_tasks()
    CONTRACT_ROOT.mkdir(parents=True, exist_ok=True)
    TASKS_ROOT.mkdir(parents=True, exist_ok=True)

    write_readme(tasks)
    write_profession()
    write_manifest(tasks)
    write_index(tasks)
    write_tasks(tasks)

    print(f"contract_root={CONTRACT_ROOT}")
    print(f"tasks={len(tasks)}")
    return 0


def load_source_tasks() -> list[dict[str, object]]:
    tasks = json.loads(SOURCE_TASKS.read_text(encoding="utf-8"))
    if not isinstance(tasks, list):
        raise ValueError(f"{SOURCE_TASKS} must contain a JSON list")
    index = json.loads(SOURCE_INDEX.read_text(encoding="utf-8"))
    index_map = {str(item["id"]): item for item in index if isinstance(item, dict) and "id" in item}
    enriched: list[dict[str, object]] = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        task_id = str(task.get("id", ""))
        combined = dict(task)
        source = index_map.get(task_id, {})
        if "title" in source and isinstance(source.get("title"), str):
            combined["title"] = source["title"]
        if "difficulty" in source:
            combined["difficulty"] = source["difficulty"]
        enriched.append(combined)
    return enriched


def write_readme(tasks: list[dict[str, object]]) -> None:
    levels = sorted({str(task.get("level", "")) for task in tasks})
    text = "\n".join(
        [
            "# Office General Contracts",
            "",
            "Contratos formales para la profesion de ofimatica transversal.",
            "",
            "Este bloque se mantiene separado del benchmark general para que una maquina y un humano "
            "puedan revisar el contrato de cada tarea sin navegar por los resultados historicos.",
            "",
            "## Estructura",
            "",
            "- `profession.md`: contrato de la profesion.",
            "- `manifest.json`: indice maquina-legible del bloque.",
            "- `index.json`: lista simple de tareas.",
            "- `tasks/test-XX/contract.md`: contrato humano de cada tarea.",
            "- `tasks/test-XX/metadata.json`: metadatos maquina-legibles.",
            "- `tasks/test-XX/reference.md`: referencia de evaluacion y respuesta esperada.",
            "",
            "## Niveles",
            "",
            ", ".join(levels),
            "",
            "## Origen",
            "",
            "El contenido se deriva de `benchmarks/tasks/assistant_tasks.json` y de la suite `assistant_suite` existente.",
            "",
        ]
    )
    (CONTRACT_ROOT / "README.md").write_text(text, encoding="utf-8")


def write_profession() -> None:
    lines = [
        "# Profession Contract",
        "",
        f"## Id\n{PROFESSION['id']}",
        "",
        f"## Title\n{PROFESSION['title']}",
        "",
        f"## Description\n{PROFESSION['description']}",
        "",
        "## Scope",
        "",
    ]
    lines.extend(f"- {item}" for item in PROFESSION["scope"])
    lines.extend(["", "## Constraints", ""])
    lines.extend(f"- {item}" for item in PROFESSION["constraints"])
    lines.extend(["", "## Evaluation Dimensions", ""])
    lines.extend(f"- {item}" for item in PROFESSION["evaluation_dimensions"])
    lines.extend(["", "## Output Standard", "", "- Respuesta breve, util y verificable.", "- Tono profesional.", "- Trazabilidad con archivos locales cuando aplique.", ""])
    (CONTRACT_ROOT / "profession.md").write_text("\n".join(lines), encoding="utf-8")


def write_manifest(tasks: list[dict[str, object]]) -> None:
    manifest = {
        "profession": PROFESSION,
        "source": str(Path("benchmarks") / "tasks" / "assistant_tasks.json"),
        "tasks_root": str(Path("benchmarks") / "contracts" / "office_general" / "tasks"),
        "task_count": len(tasks),
        "tasks": [
            {
                "id": str(task["id"]),
                "title": task_title(task),
                "difficulty": int(task.get("difficulty", 0)),
                "level": str(task.get("level", "")),
                "category": str(task.get("category", "")),
                "folder": f"tasks/{task['id']}",
                "metadata": f"tasks/{task['id']}/metadata.json",
                "contract": f"tasks/{task['id']}/contract.md",
                "reference": f"tasks/{task['id']}/reference.md",
            }
            for task in tasks
        ],
    }
    (CONTRACT_ROOT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def write_index(tasks: list[dict[str, object]]) -> None:
    index = [
        {
            "id": str(task["id"]),
            "title": task_title(task),
            "difficulty": int(task.get("difficulty", 0)),
            "level": str(task.get("level", "")),
        }
        for task in tasks
    ]
    (CONTRACT_ROOT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


def response_shape(task: dict[str, object]) -> str:
    skills = {str(item) for item in task.get("skills", [])}
    title = str(task.get("title", "")).lower()

    if "web_search" in skills or "investigar" in title or "comparar" in title:
        return "informe con fuentes y conclusion operativa"
    if "email_drafting" in skills or "redactar" in title:
        return "email breve o borrador profesional"
    if "calendar_generation" in skills or "agenda" in title or "calendario" in title:
        return "tabla o calendario con fechas y horas"
    if "csv_generation" in skills or "crear csv" in title:
        return "csv o tabla limpia"
    if "expense_audit" in skills or "gasto" in title:
        return "tabla de auditoria con discrepancias y recomendacion"
    if "executive_report" in skills or "informe" in title:
        return "informe sintetico con acciones"
    if "summarization" in skills or "resumen" in title:
        return "resumen claro y corto"
    if "task_extraction" in skills or "extraer" in title:
        return "tabla de elementos extraidos"
    return "respuesta util y trazable"


def write_tasks(tasks: list[dict[str, object]]) -> None:
    for task in tasks:
        task_id = str(task["id"])
        folder = TASKS_ROOT / task_id
        folder.mkdir(parents=True, exist_ok=True)

        title = task_title(task)
        prompt = str(task["prompt"])
        required_files = [str(item) for item in task.get("required_files", [])]
        skills = [str(item) for item in task.get("skills", [])]
        expected_keys = [str(item) for item in task.get("expected_keys", [])]
        rubric = task.get("rubric") or {}

        task_contract = [
            "# Task Contract",
            "",
            f"## Id\n{task_id}",
            "",
            f"## Title\n{title}",
            "",
            f"## Profession\n{PROFESSION['title']}",
            "",
            f"## Category\n{task.get('category', '')}",
            "",
            f"## Level\n{task.get('level', '')}",
            "",
            f"## Difficulty\n{task.get('difficulty', '')}",
            "",
            "## Objective",
            "",
            "Resolver una tarea transversal de ofimatica con archivos locales y salida verificable.",
            "",
            "## Prompt",
            "",
            prompt,
            "",
            "## Required Files",
            "",
        ]
        task_contract.extend(f"- {item}" for item in required_files)
        task_contract.extend(["", "## Expected Output Shape", "", f"- {response_shape(task)}", "", "## Expected Keys", ""])
        task_contract.extend(f"- {item}" for item in expected_keys)
        task_contract.extend(["", "## Skills", ""])
        task_contract.extend(f"- {item}" for item in skills)
        task_contract.extend(["", "## Rubric", ""])
        task_contract.extend(f"- {key}: {value}" for key, value in rubric.items())
        task_contract.extend(["", "## Evaluation Notes", "", "- No inventar datos.", "- Mantener trazabilidad con el contexto local.", "- Priorizar claridad sobre floritura.", ""])
        (folder / "contract.md").write_text("\n".join(task_contract), encoding="utf-8")

        metadata = {
            "id": task_id,
            "title": title,
            "difficulty": int(task.get("difficulty", 0)),
            "level": str(task.get("level", "")),
            "category": str(task.get("category", "")),
            "skills": skills,
            "required_files": required_files,
            "expected_keys": expected_keys,
            "response_shape": response_shape(task),
            "prompt": prompt,
            "source_task_file": f"benchmarks/tasks/assistant_suite/{task_id}/task.md",
            "source_metadata_file": f"benchmarks/tasks/assistant_suite/{task_id}/metadata.json",
        }
        (folder / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

        reference = [
            "# Reference Answer",
            "",
            f"## Id\n{task_id}",
            "",
            "## What A Correct Answer Must Contain",
            "",
        ]
        reference.extend(f"- {item}" for item in expected_keys)
        reference.extend(
            [
                "",
                "## Output Guidance",
                "",
                f"- Formato esperado: {response_shape(task)}.",
                "- Debe ser utilizable sin lectura adicional.",
                "- No debe introducir datos no presentes en los archivos o en el enunciado.",
                "",
                "## Traceability",
                "",
                "- Citar o reflejar el archivo usado cuando sea posible.",
                "- Si falta informacion esencial, indicarlo con claridad.",
                "",
            ]
        )
        (folder / "reference.md").write_text("\n".join(reference), encoding="utf-8")


def task_title(task: dict[str, object]) -> str:
    title = task.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    prompt = str(task.get("prompt", "")).strip()
    if prompt.startswith("#"):
        first_line = prompt.splitlines()[0].lstrip("#").strip()
        if first_line:
            return first_line
    return str(task.get("id", "")).strip()


if __name__ == "__main__":
    raise SystemExit(main())
