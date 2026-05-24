# Task Contract

## Id
test-27

## Title
Preparar tablero de acciones por responsable

## Profession
Ofimatica transversal para asistente ejecutivo

## Category
assistant_digital

## Level
L4

## Difficulty
4

## Objective

Resolver una tarea transversal de ofimatica con archivos locales y salida verificable.

## Prompt

# Preparar tablero de acciones por responsable

Crea un tablero de acciones por responsable combinando notas de voz, correos y contactos. Incluye prioridad y fecha limite cuando exista.

## Required Files

- assistant_synthetic/notas_voz.jsonl
- assistant_synthetic/contactos_50.csv
- assistant_synthetic/emails_hilos.md

## Expected Output Shape

- tabla de elementos extraidos

## Expected Keys

- responsable
- fecha limite
- cliente
- prioridad

## Skills

- task_extraction
- entity_resolution
- planning

## Rubric

- correctness: 4
- expected_keys: 3
- format: 2
- traceability: 1

## Evaluation Notes

- No inventar datos.
- Mantener trazabilidad con el contexto local.
- Priorizar claridad sobre floritura.
