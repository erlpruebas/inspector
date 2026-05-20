Voy a usar la skill de Spreadsheets porque el trabajo es de análisis sobre varios CSV locales. Primero reviso la estructura de los archivos y luego agrego los resultados.

Los CSV tienen columnas de fecha, concepto, categoría, importes declarado/esperado y estado. Ahora agrego por mes y categoría, y separo cualquier fila cuyo estado no sea `ok` como anomalía.

**Resumen enero-mayo 2026**

Total declarado: **1.410,39 €**  
Total esperado: **1.420,39 €**  
Diferencia: **-10,00 €**, causada por una discrepancia en febrero.

**Total por mes**

| Mes | Total declarado | Total esperado | Líneas |
|---|---:|---:|---:|
| Enero | 267,50 € | 267,50 € | 3 |
| Febrero | 178,10 € | 188,10 € | 3 |
| Marzo | 554,70 € | 554,70 € | 3 |
| Abril | 116,69 € | 116,69 € | 3 |
| Mayo | 293,40 € | 293,40 € | 3 |

**Categorías principales**

| Categoría | Total declarado | % del total |
|---|---:|---:|
| Viajes | 883,80 € | 62,7 % |
| Comidas | 249,30 € | 17,7 % |
| Software | 203,89 € | 14,5 % |
| Oficina | 73,40 € | 5,2 % |

**Anomalías detectadas**

| Fecha | Concepto | Categoría | Declarado | Esperado | Estado |
|---|---|---|---:|---:|---|
| 2026-02-22 | Licencia PDF | Software | 19,90 € | 29,90 € | importe_discrepante |
| 2026-03-04 | Hotel Barcelona | Viajes | 210,00 € | 210,00 € | posible_duplicado |
| 2026-03-04 | Hotel Barcelona | Viajes | 210,00 € | 210,00 € | posible_duplicado |
| 2026-04-11 | Taxi cliente | Viajes | 28,30 € | 28,30 € | sin_recibo |
| 2026-05-03 | Suscripcion IA | Software | 120,00 € | 120,00 € | revisar_proveedor |
