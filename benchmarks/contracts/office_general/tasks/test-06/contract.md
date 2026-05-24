# Task Contract

## Id
test-06

## Title
Preparar agenda de viaje a Barcelona

## Profession
Ofimatica transversal para asistente ejecutivo

## Category
assistant_digital

## Level
L2

## Difficulty
2

## Objective

Resolver una tarea transversal de ofimatica con archivos locales y salida verificable.

## Prompt

# Preparar agenda de viaje a Barcelona

Cruza `emails_hilos.md` y `notas_voz.jsonl` para preparar una agenda de viaje a Barcelona relacionada con Barna Health. Incluye motivo, fecha, hora y contacto.

## Required Files

- assistant_synthetic/emails_hilos.md
- assistant_synthetic/notas_voz.jsonl

## Expected Output Shape

- tabla o calendario con fechas y horas

## Expected Keys

- Xavier Puig
- Barna Health
- 18 de mayo
- 10:00

## Skills

- agenda
- synthesis

## Rubric

- correctness: 4
- expected_keys: 3
- format: 2
- traceability: 1

## Evaluation Notes

- No inventar datos.
- Mantener trazabilidad con el contexto local.
- Priorizar claridad sobre floritura.
