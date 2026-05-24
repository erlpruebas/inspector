# Task Contract

## Id
test-14

## Title
Crear calendario ICS de cuatro compromisos

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

# Crear calendario ICS de cuatro compromisos

A partir de `notas_voz.jsonl` y `emails_hilos.md`, crea el contenido de un archivo ICS con cuatro compromisos claros. Si falta algun dato, indicalo en descripcion.

## Required Files

- assistant_synthetic/notas_voz.jsonl
- assistant_synthetic/emails_hilos.md

## Expected Output Shape

- tabla o calendario con fechas y horas

## Expected Keys

- Clinica Centro
- Barna Health
- sala
- viernes 09:30

## Skills

- calendar_generation
- data_extraction

## Rubric

- correctness: 4
- expected_keys: 3
- format: 2
- traceability: 1

## Evaluation Notes

- No inventar datos.
- Mantener trazabilidad con el contexto local.
- Priorizar claridad sobre floritura.
