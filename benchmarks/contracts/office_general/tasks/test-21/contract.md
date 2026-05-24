# Task Contract

## Id
test-21

## Title
Buscar alternativa a herramienta de encuestas

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

# Buscar alternativa a herramienta de encuestas

Usa busqueda web y `notas_voz.jsonl` para proponer alternativas economicas a una herramienta de encuestas para GreenBox. Incluye fuentes.

## Required Files

- assistant_synthetic/notas_voz.jsonl

## Expected Output Shape

- informe con fuentes y conclusion operativa

## Expected Keys

- GreenBox
- encuestas
- precio
- fuentes

## Skills

- web_search
- comparison
- reporting

## Rubric

- correctness: 4
- expected_keys: 3
- format: 2
- traceability: 1

## Evaluation Notes

- No inventar datos.
- Mantener trazabilidad con el contexto local.
- Priorizar claridad sobre floritura.
