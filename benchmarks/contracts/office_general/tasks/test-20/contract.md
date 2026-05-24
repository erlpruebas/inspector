# Task Contract

## Id
test-20

## Title
Informe de incidencias de Clinica Centro

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

# Informe de incidencias de Clinica Centro

Elabora un informe de incidencias y oportunidades para Clinica Centro usando notas, emails y contactos.

## Required Files

- assistant_synthetic/notas_voz.jsonl
- assistant_synthetic/emails_hilos.md
- assistant_synthetic/contactos_50.csv

## Expected Output Shape

- informe sintetico con acciones

## Expected Keys

- Clinica Centro
- Noelia Castro
- modulo de pagos
- facturacion

## Skills

- synthesis
- client_context

## Rubric

- correctness: 4
- expected_keys: 3
- format: 2
- traceability: 1

## Evaluation Notes

- No inventar datos.
- Mantener trazabilidad con el contexto local.
- Priorizar claridad sobre floritura.
