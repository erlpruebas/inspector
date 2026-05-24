from __future__ import annotations

import itertools
import random

from .lab_contracts import LabActivation, LabPersona, ScheduledLabMessage, TaskContract


def build_schedule(
    activation: LabActivation,
    personas: list[LabPersona],
    tasks: list[TaskContract],
    *,
    seed: int = 42,
) -> list[ScheduledLabMessage]:
    selected_personas = filter_personas(personas, activation.persona_ids)
    selected_tasks = filter_tasks(tasks, activation.task_ids)
    if activation.max_tasks is not None:
        selected_tasks = selected_tasks[: activation.max_tasks]
    if not selected_personas:
        raise ValueError("No hay personas seleccionadas para el laboratorio.")
    if not selected_tasks:
        raise ValueError("No hay tareas seleccionadas para el laboratorio.")

    rng = random.Random(seed)
    schedule: list[ScheduledLabMessage] = []
    persona_cycle = itertools.cycle(selected_personas)
    for sequence, task in enumerate(selected_tasks, start=1):
        delay = compute_delay(activation.speed_seconds, activation.speed_mode, rng, sequence)
        schedule.append(
            ScheduledLabMessage(
                activation_id=activation.id,
                sequence=sequence,
                persona=next(persona_cycle),
                task=task,
                delay_seconds=delay,
                transport=activation.transport,
            )
        )
    return schedule


def filter_personas(personas: list[LabPersona], ids: tuple[str, ...]) -> list[LabPersona]:
    if not ids:
        return personas
    wanted = set(ids)
    return [persona for persona in personas if persona.id in wanted]


def filter_tasks(tasks: list[TaskContract], ids: tuple[str, ...]) -> list[TaskContract]:
    if not ids:
        return tasks
    wanted = set(ids)
    return [task for task in tasks if task.id in wanted]


def compute_delay(base: float, mode: str, rng: random.Random, sequence: int) -> float:
    if sequence == 1:
        return 0.0
    if mode == "jitter":
        return round(rng.uniform(base * 0.5, base * 1.5), 3)
    if mode == "burst":
        return round(base * 0.2 if sequence % 4 else base * 2, 3)
    return base
