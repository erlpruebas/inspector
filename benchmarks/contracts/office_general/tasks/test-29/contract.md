# Task Contract

## Id
test-29

## Title
Informe mensual combinado operaciones-finanzas

## Profession
Ofimatica transversal para asistente ejecutivo

## Category
assistant_digital

## Level
L5

## Difficulty
5

## Objective

Resolver una tarea transversal de ofimatica con archivos locales y salida verificable.

## Prompt

# Informe mensual combinado operaciones-finanzas

Elabora un informe mensual combinado de operaciones y finanzas cruzando contactos, emails, notas y gastos. Debe separar hechos locales, riesgos e inferencias.

## Required Files

- assistant_synthetic/notas_voz.jsonl
- assistant_synthetic/emails_hilos.md
- assistant_synthetic/contactos_50.csv
- assistant_synthetic/gastos_2026_01.csv
- assistant_synthetic/gastos_2026_02.csv
- assistant_synthetic/gastos_2026_03.csv
- assistant_synthetic/gastos_2026_04.csv
- assistant_synthetic/gastos_2026_05.csv

## Expected Output Shape

- informe sintetico con acciones

## Expected Keys

- gastos
- tareas pendientes
- clientes prioritarios
- riesgos

## Skills

- multi_file_analysis
- executive_report
- risk_synthesis

## Rubric

- correctness: 4
- expected_keys: 3
- format: 2
- traceability: 1

## Evaluation Notes

- No inventar datos.
- Mantener trazabilidad con el contexto local.
- Priorizar claridad sobre floritura.
