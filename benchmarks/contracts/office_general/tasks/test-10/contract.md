# Task Contract

## Id
test-10

## Title
Crear CSV de proveedores

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

# Crear CSV de proveedores

Desde `contactos_50.csv`, crea un CSV de proveedores con columnas Nombre, Empresa, Rol, Email, Ciudad y Prioridad.

## Required Files

- assistant_synthetic/contactos_50.csv

## Expected Output Shape

- csv o tabla limpia

## Expected Keys

- proveedor
- IberLegal
- Tecnoria
- SerConta

## Skills

- data_filtering
- csv_generation

## Rubric

- correctness: 4
- expected_keys: 3
- format: 2
- traceability: 1

## Evaluation Notes

- No inventar datos.
- Mantener trazabilidad con el contexto local.
- Priorizar claridad sobre floritura.
