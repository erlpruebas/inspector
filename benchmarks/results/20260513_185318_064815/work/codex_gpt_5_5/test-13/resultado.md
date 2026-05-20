Voy a usar la skill de hojas de cálculo porque el trabajo es auditar CSVs y resumir datos tabulares. Primero revisaré el formato de los tres archivos y luego cruzaré duplicados y discrepancias.

Ya tengo las reglas relevantes: no hace falta generar un workbook si el entregable es un informe, pero sí conviene tratar los CSVs como datos estructurados. Ahora voy a inspeccionar columnas, tamaños y algunas filas para entender qué campos permiten detectar discrepancias.

Los archivos son pequeños y tienen el mismo esquema: `fecha`, `concepto`, `categoria`, importes declarado/esperado y `estado`. Voy a calcular el resumen auditando tanto el estado informado como diferencias numéricas y duplicados exactos entre filas.

**Resumen Q1**

Auditados 9 registros en los tres CSVs. Total declarado: **1.000,30**; total esperado: **1.010,30**; diferencia neta: **-10,00**.

**Discrepancias**
- Febrero, `2026-02-22`, **Licencia PDF**: declarado **19,90**, esperado **29,90**. Diferencia: **-10,00**. Estado: `importe_discrepante`.

**Duplicados**
- Marzo, `2026-03-04`, **Hotel Barcelona**, viajes, **210,00**: aparece 2 veces idéntico en `assistant_synthetic/gastos_2026_03.csv`. Estado: `posible_duplicado`.
- Impacto potencial si una fila es duplicada real: sobreconteo de **210,00** en declarado y esperado.

**Partidas limpias**
- Enero: 3 limpias, total **267,50**.
- Febrero: 2 limpias, total **158,20**.
- Marzo: 1 limpia, total **134,70**.
- Total partidas limpias: **6 registros**, **560,40**.

**Detalle limpio**
- `2026-01-08` Hotel Madrid: **180,00**
- `2026-01-09` Taxi aeropuerto: **38,50**
- `2026-01-15` Software encuestas: **49,00**
- `2026-02-03` Cena cliente: **96,20**
- `2026-02-14` Tren Valencia: **62,00**
- `2026-03-19` Comida equipo: **134,70**
