# Task Contract

## Id
test-15

## Title
Cruzar notas de voz con contactos

## Profession
Ofimatica transversal para asistente ejecutivo

## Category
assistant_digital

## Level
L3

## Difficulty
3

## Objective

Resolver una tarea transversal de ofimatica con archivos locales y salida verificable.

## Prompt

# Cruzar notas de voz con contactos

Cruza notas de voz con contactos para identificar personas mencionadas y sus empresas. Devuelve una tabla con tarea, persona, empresa y email.

## Required Files

- assistant_synthetic/notas_voz.jsonl
- assistant_synthetic/contactos_50.csv

## Expected Output Shape

- respuesta util y trazable

## Expected Keys

- Noelia Castro
- Luis Martin
- Tomas Vega
- Laura Marin

## Skills

- entity_resolution
- contacts

## Rubric

- correctness: 4
- expected_keys: 3
- format: 2
- traceability: 1

## Evaluation Notes

- No inventar datos.
- Mantener trazabilidad con el contexto local.
- Priorizar claridad sobre floritura.
