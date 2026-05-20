Usaré la skill de Spreadsheets porque el trabajo es auditar CSV locales y resumir discrepancias/duplicados con trazabilidad. Primero voy a revisar la estructura de los archivos y luego haré el cruce de datos.

Ya tengo la guía suficiente; no hace falta crear un libro Excel porque el pedido es un informe textual. Voy a inspeccionar encabezados, conteos y posibles claves repetidas en los tres CSV.

La estructura es uniforme: fecha, concepto, categoría, declarado, esperado y estado. Ahora calcularé diferencias de importe, duplicados exactos y filas limpias por mes para evitar depender solo del campo `estado`.

**Informe Q1**

Auditados los 3 CSV: 9 partidas en total.

| Mes | Partidas | Declarado | Esperado | Diferencia | Limpias | Discrepancias | Duplicados marcados |
|---|---:|---:|---:|---:|---:|---:|---:|
| Enero | 3 | 267,50 | 267,50 | 0,00 | 3 | 0 | 0 |
| Febrero | 3 | 178,10 | 188,10 | -10,00 | 2 | 1 | 0 |
| Marzo | 3 | 554,70 | 554,70 | 0,00 | 1 | 0 | 2 |

**Discrepancias**
- `assistant_synthetic/gastos_2026_02.csv`: `2026-02-22`, Licencia PDF, software. Declarado `19,90`, esperado `29,90`; diferencia `-10,00`. Estado: `importe_discrepante`.

**Duplicados**
- `assistant_synthetic/gastos_2026_03.csv`: `2026-03-04`, Hotel Barcelona, viajes, `210,00`. Aparece 2 veces con los mismos importes. Exceso potencial declarado si solo una partida es válida: `210,00`.

**Partidas limpias**
- Enero: Hotel Madrid `180,00`, Taxi aeropuerto `38,50`, Software encuestas `49,00`.
- Febrero: Cena cliente `96,20`, Tren Valencia `62,00`.
- Marzo: Comida equipo `134,70`.

**Total Q1**
Declarado: `1.000,30`; esperado: `1.010,30`; diferencia neta por importes: `-10,00`. Además, hay un duplicado potencial de `210,00` en marzo que debe revisarse antes de cerrar el trimestre.
