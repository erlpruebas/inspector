Usaré la skill de Spreadsheets porque el trabajo es agregar y analizar varios CSV locales con totales, categorías y anomalías. Primero voy a inspeccionar la estructura de los archivos para elegir el cálculo correcto.

Los CSV tienen columnas de fecha, concepto, categoría, importe declarado, importe esperado y estado. Voy a agregar por `importe_declarado`, y usaré `estado` más la comparación declarado vs esperado para detectar anomalías.

Resumen calculado sobre `importe_declarado` e incluyendo todos los registros.

**Total por mes**

| Mes | Total | Anomalías |
|---|---:|---:|
| Enero 2026 | 267,50 | 0 |
| Febrero 2026 | 178,10 | 1 |
| Marzo 2026 | 554,70 | 2 |
| Abril 2026 | 116,69 | 1 |
| Mayo 2026 | 293,40 | 1 |

**Total enero-mayo:** 1.410,39

**Categorías principales**

| Categoría | Total | % del total |
|---|---:|---:|
| viajes | 883,80 | 62,7% |
| comidas | 249,30 | 17,7% |
| software | 203,89 | 14,5% |
| oficina | 73,40 | 5,2% |

**Anomalías detectadas**

| Fecha | Concepto | Categoría | Declarado | Esperado | Diferencia | Estado |
|---|---|---|---:|---:|---:|---|
| 2026-02-22 | Licencia PDF | software | 19,90 | 29,90 | -10,00 | importe_discrepante |
| 2026-03-04 | Hotel Barcelona | viajes | 210,00 | 210,00 | 0,00 | posible_duplicado |
| 2026-03-04 | Hotel Barcelona | viajes | 210,00 | 210,00 | 0,00 | posible_duplicado |
| 2026-04-11 | Taxi cliente | viajes | 28,30 | 28,30 | 0,00 | sin_recibo |
| 2026-05-03 | Suscripcion IA | software | 120,00 | 120,00 | 0,00 | revisar_proveedor |

Nota: marzo incluye ambos registros de `Hotel Barcelona`; si se elimina un duplicado, el total de marzo bajaría de 554,70 a 344,70 y el total enero-mayo bajaría a 1.200,39.
