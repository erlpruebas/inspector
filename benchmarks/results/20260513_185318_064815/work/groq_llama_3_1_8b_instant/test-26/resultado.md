# Auditoria completa de gastos con recomendaciones

## Resumen de gastos por mes

| Mes | Total gastos | Duplicados | Faltan recibos | Discrepancias |
| --- | --- | --- | --- | --- |
| Enero | 267.5 | 0 | 0 | 0 |
| Febrero | 168.1 | 0 | 1 | 1 |
| Marzo | 454.7 | 1 | 0 | 0 |
| Abril | 216.6 | 0 | 1 | 0 |
| Mayo | 343.4 | 0 | 0 | 1 |

## Recomendaciones de control interno

* Verificar la existencia de recibos para los gastos con estado "sin_recibo".
* Revisar la discrepancia en el gasto de "Licencia PDF" en febrero.
* Investigar la posible duplicación del gasto de "Hotel Barcelona" en marzo.
* Revisar la discrepancia en la suscripción a IA en mayo.
* Implementar un sistema de control de gastos para evitar duplicados y faltan recibos.

## Gastos con estado "ok"

| Fecha | Concepto | Categoria | Importe declarado | Importe esperado |
| --- | --- | --- | --- | --- |
| 2026-01-08 | Hotel Madrid | viajes | 180.0 | 180.0 |
| 2026-01-09 | Taxi aeropuerto | viajes | 38.5 | 38.5 |
| 2026-01-15 | Software encuestas | software | 49.0 | 49.0 |
| 2026-02-03 | Cena cliente | comidas | 96.2 | 96.2 |
| 2026-02-14 | Tren Valencia | viajes | 62.0 | 62.0 |
| 2026-03-19 | Comida equipo | comidas | 134.7 | 134.7 |
| 2026-04-02 | Dominio anual | software | 14.99 | 14.99 |
| 2026-04-25 | Material oficina | oficina | 73.4 | 73.4 |
| 2026-05-01 | Vuelo Barcelona | viajes | 155.0 | 155.0 |
| 2026-05-03 | Cafe reunion | comidas | 18.4 | 18.4 |

## Gastos con estado "posible_duplicado"

| Fecha | Concepto | Categoria | Importe declarado | Importe esperado |
| --- | --- | --- | --- | --- |
| 2026-03-04 | Hotel Barcelona | viajes | 210.0 | 210.0 |
| 2026-03-04 | Hotel Barcelona | viajes | 210.0 | 210.0 |

## Gastos con estado "importe_discrepante"

| Fecha | Concepto | Categoria | Importe declarado | Importe esperado |
| --- | --- | --- | --- | --- |
| 2026-02-22 | Licencia PDF | software | 19.9 | 29.9 |

## Gastos con estado "sin_recibo"

| Fecha | Concepto | Categoria | Importe declarado | Importe esperado |
| --- | --- | --- | --- | --- |
| 2026-04-11 | Taxi cliente | viajes | 28.3 | 28.3 |

## Gastos con estado "revisar_proveedor"

| Fecha | Concepto | Categoria | Importe declarado | Importe esperado |
| --- | --- | --- | --- | --- |
| 2026-05-03 | Suscripcion IA | software | 120.0 | 120.0 |
