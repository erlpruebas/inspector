# Informe de Discrepancias de Gastos Q1 2026

## Resumen General

Se ha realizado una auditoría de los ficheros de gastos para el primer trimestre (Q1) de 2026. Se han identificado partidas con importes discrepantes, gastos duplicados y gastos declarados correctamente.

- **Ficheros Analizados:** `gastos_2026_01.csv`, `gastos_2026_02.csv`, `gastos_2026_03.csv`

## Partidas con Discrepancias

Se ha encontrado una partida cuyo importe declarado no coincide con el esperado.

| Fecha | Concepto | Categoría | Importe Declarado | Importe Esperado | Fichero |
|---|---|---|---|---|---|
| PHONE_0089 | Licencia PDF | software | 19.9 | 29.9 | `gastos_2026_02.csv` |

## Partidas Duplicadas

Se ha detectado una partida que parece estar duplicada.

| Fecha | Concepto | Categoría | Importe | Fichero |
|---|---|---|---|---|
| PHONE_0093 | PERSON_0076 | viajes | 210.0 | `gastos_2026_03.csv` |

## Partidas Correctas

Un total de 6 partidas han sido declaradas correctamente sin ninguna incidencia.

- **Enero:** 3 partidas correctas.
- **Febrero:** 2 partidas correctas.
- **Marzo:** 1 partida correcta.
