# Task Contract

## Id
test-03

## Title
Extraer tareas de notas de voz

## Profession
Ofimatica transversal para asistente ejecutivo

## Category
assistant_digital

## Level
L1

## Difficulty
1

## Objective

Resolver una tarea transversal de ofimatica con archivos locales y salida verificable.

## Prompt

# Extraer tareas de notas de voz

Lee `benchmarks/assets/assistant_synthetic/notas_voz.jsonl` y extrae las tareas pendientes en una tabla con id de nota, accion, entidad relacionada y posible fecha limite.

## Required Files

- assistant_synthetic/notas_voz.jsonl

## Expected Output Shape

- resumen claro y corto

## Expected Keys

- llamar
- enviar
- agendar
- reservar

## Skills

- task_extraction
- summarization

## Rubric

- correctness: 4
- expected_keys: 3
- format: 2
- traceability: 1

## Evaluation Notes

- No inventar datos.
- Mantener trazabilidad con el contexto local.
- Priorizar claridad sobre floritura.
