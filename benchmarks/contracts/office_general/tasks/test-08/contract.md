# Task Contract

## Id
test-08

## Title
Resumen semanal de tareas pendientes

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

# Resumen semanal de tareas pendientes

Genera un resumen semanal de tareas pendientes a partir de `notas_voz.jsonl` y `emails_hilos.md`, priorizando compromisos con fecha o cliente concreto.

## Required Files

- assistant_synthetic/notas_voz.jsonl
- assistant_synthetic/emails_hilos.md

## Expected Output Shape

- resumen claro y corto

## Expected Keys

- IberLegal
- Clinica Centro
- Delta Equipos
- SSL

## Skills

- summarization
- prioritization

## Rubric

- correctness: 4
- expected_keys: 3
- format: 2
- traceability: 1

## Evaluation Notes

- No inventar datos.
- Mantener trazabilidad con el contexto local.
- Priorizar claridad sobre floritura.
