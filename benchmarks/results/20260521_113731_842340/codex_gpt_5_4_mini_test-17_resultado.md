Usaré la skill de `Spreadsheets` para leer los CSV y calcular totales, categorías y anomalías con trazabilidad. Primero voy a inspeccionar la estructura de los archivos para asegurar que la agregación sea consistente entre meses.

Ya confirmé que los cinco archivos existen. Ahora voy a leerlos en paralelo para ver columnas, valores y posibles inconsistencias antes de calcular los agregados.

Estoy calculando ahora los agregados. Voy a mantener el total “tal como está registrado” y, aparte, señalar las filas con estado anómalo para que el resumen no oculte discrepancias ni duplicados.

**Resumen**
- Total enero-mayo: **1,410.39**
- Mes con mayor gasto: **marzo** con **554.70**
- Mes con menor gasto: **abril** con **116.69**

**Totales por mes**

| Mes | Total |
|---|---:|
| 2026-01 | 267.50 |
| 2026-02 | 178.10 |
| 2026-03 | 554.70 |
| 2026-04 | 116.69 |
| 2026-05 | 293.40 |

**Categorías principales**

| Categoría | Total |
|---|---:|
| viajes | 883.80 |
| comidas | 249.30 |
| software | 203.89 |
| oficina | 73.40 |

**Anomalías detectadas**

| Mes | Fecha | Concepto | Categoría | Importe declarado | Importe esperado | Estado |
|---|---|---|---|---:|---:|---|
| 2026-02 | 2026-02-22 | Licencia PDF | software | 19.90 | 29.90 | importe_discrepante |
| 2026-03 | 2026-03-04 | Hotel Barcelona | viajes | 210.00 | 210.00 | posible_duplicado |
| 2026-03 | 2026-03-04 | Hotel Barcelona | viajes | 210.00 | 210.00 | posible_duplicado |
| 2026-04 | 2026-04-11 | Taxi cliente | viajes | 28.30 | 28.30 | sin_recibo |
| 2026-05 | 2026-05-03 | Suscripcion IA | software | 120.00 | 120.00 | revisar_proveedor |

**Nota**
- El total anterior usa los importes declarados tal como están en los CSV.
- Marzo contiene un gasto marcado como `posible_duplicado` y aparece dos veces, así que el total bruto de ese mes incluye ambas líneas.
- Si quieres, puedo darte una versión depurada sin duplicados y con ajuste por discrepancias.
