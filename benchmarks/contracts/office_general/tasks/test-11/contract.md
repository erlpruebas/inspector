# Task Contract

## Id
test-11

## Title
Priorizar clientes de alta prioridad

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

# Priorizar clientes de alta prioridad

Lista los clientes con prioridad alta en `contactos_50.csv`. Agrupa por ciudad y recomienda tres acciones comerciales.

## Required Files

- assistant_synthetic/contactos_50.csv

## Expected Output Shape

- respuesta util y trazable

## Expected Keys

- alta
- cliente
- Nova Iberia
- Clinica Centro

## Skills

- data_filtering
- prioritization

## Rubric

- correctness: 4
- expected_keys: 3
- format: 2
- traceability: 1

## Evaluation Notes

- No inventar datos.
- Mantener trazabilidad con el contexto local.
- Priorizar claridad sobre floritura.
