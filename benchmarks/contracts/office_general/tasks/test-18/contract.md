# Task Contract

## Id
test-18

## Title
Segmentar prospectos para campana

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

# Segmentar prospectos para campana

Segmenta los contactos tipo prospecto para una campana. Incluye empresa, ciudad, responsable sugerido y motivo de prioridad.

## Required Files

- assistant_synthetic/contactos_50.csv

## Expected Output Shape

- respuesta util y trazable

## Expected Keys

- prospecto
- BravoSoft
- Noda Labs
- RedNova

## Skills

- contacts
- segmentation

## Rubric

- correctness: 4
- expected_keys: 3
- format: 2
- traceability: 1

## Evaluation Notes

- No inventar datos.
- Mantener trazabilidad con el contexto local.
- Priorizar claridad sobre floritura.
