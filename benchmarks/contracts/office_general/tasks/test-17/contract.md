# Task Contract

## Id
test-17

## Title
Resumen financiero de gastos enero-mayo

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

# Resumen financiero de gastos enero-mayo

Agrega los gastos de enero a mayo. Calcula total por mes, categorias principales y lista de anomalias.

## Required Files

- assistant_synthetic/gastos_2026_01.csv
- assistant_synthetic/gastos_2026_02.csv
- assistant_synthetic/gastos_2026_03.csv
- assistant_synthetic/gastos_2026_04.csv
- assistant_synthetic/gastos_2026_05.csv

## Expected Output Shape

- tabla de auditoria con discrepancias y recomendacion

## Expected Keys

- total mensual
- discrepancias
- sin_recibo
- revisar_proveedor

## Skills

- expense_audit
- aggregation

## Rubric

- correctness: 4
- expected_keys: 3
- format: 2
- traceability: 1

## Evaluation Notes

- No inventar datos.
- Mantener trazabilidad con el contexto local.
- Priorizar claridad sobre floritura.
