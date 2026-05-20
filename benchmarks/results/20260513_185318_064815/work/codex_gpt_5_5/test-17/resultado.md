Voy a usar la skill de Spreadsheets para revisar y agregar los CSV, porque el trabajo es análisis tabular con totales, categorías y anomalías.

Voy a comprobar primero la estructura de los cinco archivos y luego haré la agregación. Si los campos son consistentes, calculo todo en una sola pasada para evitar discrepancias entre totales y categorías.

La estructura es uniforme: fecha, concepto, categoría, importe declarado, importe esperado y estado. Ahora agrego por mes y categoría, y marco como anomalía cualquier fila con estado distinto de `ok` o diferencia entre importes.

Totales calculados sobre `importe_declarado`, incluyendo todas las filas cargadas.

**Total enero-mayo:** 1.410,39 EUR  
**Total esperado:** 1.420,39 EUR  
**Diferencia declarada vs esperada:** -10,00 EUR

**Total Por Mes**

| Mes | Total declarado | Total esperado | Gastos |
|---|---:|---:|---:|
| Enero | 267,50 | 267,50 | 3 |
| Febrero | 178,10 | 188,10 | 3 |
| Marzo | 554,70 | 554,70 | 3 |
| Abril | 116,69 | 116,69 | 3 |
| Mayo | 293,40 | 293,40 | 3 |

**Categorías Principales**

| Categoría | Total declarado | % del total | Gastos |
|---|---:|---:|---:|
| viajes | 883,80 | 62,7% | 7 |
| comidas | 249,30 | 17,7% | 3 |
| software | 203,89 | 14,5% | 4 |
| oficina | 73,40 | 5,2% | 1 |

**Anomalías**

| Fecha | Concepto | Categoría | Declarado | Esperado | Diferencia | Estado |
|---|---|---|---:|---:|---:|---|
| 2026-02-22 | Licencia PDF | software | 19,90 | 29,90 | -10,00 | importe_discrepante |
| 2026-03-04 | Hotel Barcelona | viajes | 210,00 | 210,00 | 0,00 | posible_duplicado |
| 2026-03-04 | Hotel Barcelona | viajes | 210,00 | 210,00 | 0,00 | posible_duplicado |
| 2026-04-11 | Taxi cliente | viajes | 28,30 | 28,30 | 0,00 | sin_recibo |
| 2026-05-03 | Suscripcion IA | software | 120,00 | 120,00 | 0,00 | revisar_proveedor |

Nota: marzo queda inflado si el duplicado de `Hotel Barcelona` no corresponde. Excluyendo una de esas dos líneas, el total enero-mayo bajaría a **1.200,39 EUR**.
