# Task Contract

## Id
test-25

## Title
Informe ejecutivo de cuentas prioritarias

## Profession
Ofimatica transversal para asistente ejecutivo

## Category
assistant_digital

## Level
L4

## Difficulty
4

## Objective

Resolver una tarea transversal de ofimatica con archivos locales y salida verificable.

## Prompt

# Informe ejecutivo de cuentas prioritarias

Genera un informe ejecutivo de cuentas prioritarias combinando contactos, correos y notas. Debe incluir riesgos y siguientes acciones.

## Required Files

- assistant_synthetic/contactos_50.csv
- assistant_synthetic/emails_hilos.md
- assistant_synthetic/notas_voz.jsonl

## Expected Output Shape

- informe sintetico con acciones

## Expected Keys

- clientes alta
- riesgos
- siguientes acciones
- Madrid

## Skills

- synthesis
- contacts
- executive_report

## Rubric

- correctness: 4
- expected_keys: 3
- format: 2
- traceability: 1

## Evaluation Notes

- No inventar datos.
- Mantener trazabilidad con el contexto local.
- Priorizar claridad sobre floritura.
