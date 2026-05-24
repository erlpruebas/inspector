# Task Contract

## Id
test-07

## Title
Conciliar preferencias de informe de Nova Iberia

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

# Conciliar preferencias de informe de Nova Iberia

Extrae la preferencia de formato de informes de Nova Iberia usando `emails_hilos.md` y confirma el contacto correcto en `contactos_50.csv`.

## Required Files

- assistant_synthetic/emails_hilos.md
- assistant_synthetic/contactos_50.csv

## Expected Output Shape

- informe sintetico con acciones

## Expected Keys

- Ana Lopez
- PDF
- resumen ejecutivo
- anexos

## Skills

- preference_extraction
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
