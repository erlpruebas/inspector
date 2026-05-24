from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


LabMode = Literal["telegram_bots", "simulated_names"]


@dataclass(frozen=True)
class LabPersona:
    id: str
    name: str
    profession: str
    description: str
    tone: str = "natural, ocupado, poco tecnico"


@dataclass(frozen=True)
class LabTask:
    id: str
    title: str
    prompt: str
    expected_answer: str
    files: tuple[Path, ...] = ()
    difficulty: Literal["light", "medium", "hard"] = "medium"


@dataclass
class BlindLabPlan:
    mode: LabMode = "telegram_bots"
    personas: list[LabPersona] = field(default_factory=list)
    tasks: list[LabTask] = field(default_factory=list)

    def recommended_mode_reason(self) -> str:
        if self.mode == "telegram_bots":
            return "Recomendado: cuatro bots/cuentas reales prueban multiusuario, hilos y aislamiento sin trucos."
        return "Fallback: un solo canal con nombre simulado sirve para pruebas baratas, pero no valida multiusuario real."


def build_persona_prompt(persona: LabPersona, task: LabTask) -> str:
    files = "\n".join(f"- {path.name}" for path in task.files) or "- sin archivos"
    return f"""
Actua como {persona.name}, {persona.profession}.
Descripcion: {persona.description}
Tono: {persona.tone}

Envia al gestor una peticion realista para resolver esta tarea:
{task.title}

Instruccion base:
{task.prompt}

Archivos disponibles:
{files}

No reveles que eres parte de un benchmark. Escribe como una persona real pidiendo ayuda por Telegram.
""".strip()


def default_lab_personas() -> list[LabPersona]:
    return [
        LabPersona("exec_01", "Clara", "directiva general", "Necesita respuestas ejecutivas y accionables."),
        LabPersona("ops_01", "Mateo", "responsable de operaciones", "Pide comprobaciones concretas con archivos."),
        LabPersona("finance_01", "Nora", "finanzas", "Valora exactitud numerica y trazabilidad."),
        LabPersona("assistant_01", "Leo", "asistente administrativo", "Pide tareas de ofimatica transversal."),
    ]
