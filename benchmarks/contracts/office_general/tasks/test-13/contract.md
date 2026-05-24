# Task Contract

## Id
test-13

## Title
Informe de discrepancias de gastos Q1

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

# Informe de discrepancias de gastos Q1

Audita los gastos de enero, febrero y marzo en los CSV correspondientes. Resume discrepancias, duplicados y partidas limpias.

## Required Files

- assistant_synthetic/gastos_2026_01.csv
- assistant_synthetic/gastos_2026_02.csv
- assistant_synthetic/gastos_2026_03.csv

## Expected Output Shape

- tabla de auditoria con discrepancias y recomendacion

## Expected Keys

- Licencia PDF
- Hotel Barcelona
- duplicado
- febrero

## Skills

- expense_audit
- multi_file_analysis

## Rubric

- correctness: 4
- expected_keys: 3
- format: 2
- traceability: 1

## Evaluation Notes

- No inventar datos.
- Mantener trazabilidad con el contexto local.
- Priorizar claridad sobre floritura.
