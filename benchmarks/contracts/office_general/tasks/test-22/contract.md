# Task Contract

## Id
test-22

## Title
Comparar Apple y Microsoft seis meses

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

# Comparar Apple y Microsoft seis meses

Usa busqueda web para comparar el rendimiento de Apple y Microsoft en los ultimos seis meses. Cruza el resultado con la nota de voz que lo solicita.

## Required Files

- assistant_synthetic/notas_voz.jsonl

## Expected Output Shape

- informe con fuentes y conclusion operativa

## Expected Keys

- Apple
- Microsoft
- seis meses
- fecha de consulta

## Skills

- web_search
- financial_analysis
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
