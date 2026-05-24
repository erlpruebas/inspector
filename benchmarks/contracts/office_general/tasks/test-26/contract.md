# Task Contract

## Id
test-26

## Title
Auditoria completa de gastos con recomendaciones

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

# Auditoria completa de gastos con recomendaciones

Audita todos los gastos de enero a mayo y genera recomendaciones de control interno para evitar duplicados, recibos faltantes y discrepancias.

## Required Files

- assistant_synthetic/gastos_2026_01.csv
- assistant_synthetic/gastos_2026_02.csv
- assistant_synthetic/gastos_2026_03.csv
- assistant_synthetic/gastos_2026_04.csv
- assistant_synthetic/gastos_2026_05.csv

## Expected Output Shape

- tabla de auditoria con discrepancias y recomendacion

## Expected Keys

- duplicado
- sin_recibo
- importe_discrepante
- revisar_proveedor

## Skills

- expense_audit
- multi_file_analysis
- recommendations

## Rubric

- correctness: 4
- expected_keys: 3
- format: 2
- traceability: 1

## Evaluation Notes

- No inventar datos.
- Mantener trazabilidad con el contexto local.
- Priorizar claridad sobre floritura.
