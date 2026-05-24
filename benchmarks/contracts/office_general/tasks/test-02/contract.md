# Task Contract

## Id
test-02

## Title
Crear lista de contactos prioritarios de Madrid

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

# Crear lista de contactos prioritarios de Madrid

Usa `benchmarks/assets/assistant_synthetic/contactos_50.csv` para generar una lista de contactos ubicados en Madrid con prioridad alta. Incluye nombre, empresa, rol y email.

## Required Files

- assistant_synthetic/contactos_50.csv

## Expected Output Shape

- respuesta util y trazable

## Expected Keys

- Madrid
- prioridad alta
- Ana Lopez
- Sergio Campos

## Skills

- data_filtering
- contacts

## Rubric

- correctness: 4
- expected_keys: 3
- format: 2
- traceability: 1

## Evaluation Notes

- No inventar datos.
- Mantener trazabilidad con el contexto local.
- Priorizar claridad sobre floritura.
