from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from .lab_contracts import TaskContract


@dataclass(frozen=True)
class EvaluationResult:
    task_id: str
    score: float
    found_keys: tuple[str, ...]
    missing_keys: tuple[str, ...]
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "score": self.score,
            "found_keys": list(self.found_keys),
            "missing_keys": list(self.missing_keys),
            "notes": self.notes,
        }


def evaluate_expected_keys(task: TaskContract, response_text: str) -> EvaluationResult:
    lower = response_text.casefold()
    found = []
    missing = []
    for key in task.expected_keys:
        if key.casefold() in lower:
            found.append(key)
        else:
            missing.append(key)
    score = 1.0 if not task.expected_keys else round(len(found) / len(task.expected_keys), 3)
    return EvaluationResult(task_id=task.id, score=score, found_keys=tuple(found), missing_keys=tuple(missing))


def write_evaluation(path: Path, result: EvaluationResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")


def build_excellence_judge_prompt(task: TaskContract, response_text: str) -> str:
    return f"""
Eres el juez de excelencia del laboratorio.

Evalua la respuesta del gestor para esta tarea. Puntua de 0 a 10 y explica brevemente fallos, riesgos y mejoras.

Tarea:
{task.prompt}

Respuesta esperada / referencia:
{task.reference or "No hay referencia textual; usa claves esperadas y rubrica."}

Claves esperadas:
{", ".join(task.expected_keys)}

Rubrica:
{task.rubric}

Respuesta del gestor:
{response_text}

Devuelve JSON con: score, verdict, missing, risks, improvement.
""".strip()
