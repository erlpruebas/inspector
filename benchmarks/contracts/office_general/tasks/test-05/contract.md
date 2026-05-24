# Task Contract

## Id
test-05

## Title
Detectar gasto discrepante de febrero

## Profession
Ofimatica transversal para asistente ejecutivo

## Category
assistant_digital

## Level
L1

## Difficulty
1

## Objective

Resolver una tarea transversal de ofimatica con archivos locales y salida verificable.

## Prompt

# Detectar gasto discrepante de febrero

Audita `benchmarks/assets/assistant_synthetic/gastos_2026_02.csv` e identifica la discrepancia de importe. Devuelve concepto, importe declarado, importe esperado y recomendacion.

## Required Files

- assistant_synthetic/gastos_2026_02.csv

## Expected Output Shape

- tabla de auditoria con discrepancias y recomendacion

## Expected Keys

- Licencia PDF
- 19.90
- 29.90
- importe_discrepante

## Skills

- expense_audit
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
