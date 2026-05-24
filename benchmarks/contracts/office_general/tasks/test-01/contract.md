# Task Contract

## Id
test-01

## Title
Recordar cita de Clinica Centro

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

# Recordar cita de Clinica Centro

Revisa `benchmarks/assets/assistant_synthetic/emails_hilos.md` y `benchmarks/assets/assistant_synthetic/contactos_50.csv`. Crea una nota breve con la cita de Clinica Centro: persona, empresa, fecha, hora y objetivo. No inventes datos.

## Required Files

- assistant_synthetic/emails_hilos.md
- assistant_synthetic/contactos_50.csv

## Expected Output Shape

- respuesta util y trazable

## Expected Keys

- Noelia Castro
- Clinica Centro
- 14 de mayo
- 11:30

## Skills

- agenda
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
