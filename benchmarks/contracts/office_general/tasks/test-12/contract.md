# Task Contract

## Id
test-12

## Title
Preparar minuta de contrato IberLegal

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

# Preparar minuta de contrato IberLegal

Prepara una minuta de revision del contrato de IberLegal usando `emails_hilos.md` y `notas_voz.jsonl`. Incluye fecha limite y puntos de riesgo.

## Required Files

- assistant_synthetic/emails_hilos.md
- assistant_synthetic/notas_voz.jsonl

## Expected Output Shape

- respuesta util y trazable

## Expected Keys

- clausula 8
- responsabilidad
- renovacion automatica
- 12 de mayo

## Skills

- email_analysis
- risk_extraction

## Rubric

- correctness: 4
- expected_keys: 3
- format: 2
- traceability: 1

## Evaluation Notes

- No inventar datos.
- Mantener trazabilidad con el contexto local.
- Priorizar claridad sobre floritura.
