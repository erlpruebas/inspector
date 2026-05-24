# Task Contract

## Id
test-09

## Title
Auditar duplicados de marzo

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

# Auditar duplicados de marzo

Analiza `gastos_2026_03.csv` y detecta cargos duplicados. Calcula el impacto economico y la accion recomendada.

## Required Files

- assistant_synthetic/gastos_2026_03.csv

## Expected Output Shape

- tabla de auditoria con discrepancias y recomendacion

## Expected Keys

- Hotel Barcelona
- duplicado
- 420.00
- 210.00

## Skills

- expense_audit
- duplicate_detection

## Rubric

- correctness: 4
- expected_keys: 3
- format: 2
- traceability: 1

## Evaluation Notes

- No inventar datos.
- Mantener trazabilidad con el contexto local.
- Priorizar claridad sobre floritura.
