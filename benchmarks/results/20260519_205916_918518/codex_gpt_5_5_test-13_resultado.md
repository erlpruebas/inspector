Voy a usar la skill de Spreadsheets porque el trabajo es una auditoría sobre CSV con importes y registros. Primero voy a inspeccionar la estructura de los archivos y luego calcularé duplicados, discrepancias y partidas limpias.

Los CSV son pequeños y comparten el mismo esquema: `fecha`, `concepto`, `categoria`, importes declarado/esperado y `estado`. Ahora voy a leerlos completos y agrupar por estado, diferencias de importe y repetición exacta de líneas.

**Resumen Q1**

Audité los 3 CSV locales. Hay **9 registros** en total:

| Mes | Registros | Limpias | Discrepancias | Posibles duplicados | Declarado | Esperado | Diferencia |
|---|---:|---:|---:|---:|---:|---:|---:|
| Enero | 3 | 3 | 0 | 0 | 267,50 | 267,50 | 0,00 |
| Febrero | 3 | 2 | 1 | 0 | 178,10 | 188,10 | -10,00 |
| Marzo | 3 | 1 | 0 | 2 | 554,70 | 554,70 | 0,00 |
| **Q1** | **9** | **6** | **1** | **2** | **1000,30** | **1010,30** | **-10,00** |

**Discrepancia detectada**
- `assistant_synthetic/gastos_2026_02.csv`: `PHONE_0089`, `Licencia PDF`, categoría `software`.
  - Declarado: **19,90**
  - Esperado: **29,90**
  - Diferencia: **-10,00**
  - Estado: `importe_discrepante`

**Duplicado detectado**
- `assistant_synthetic/gastos_2026_03.csv`: dos líneas idénticas marcadas como `posible_duplicado`.
  - `PHONE_0093`, `PERSON_0076`, `viajes`, **210,00**
  - Si solo una debe contar, marzo estaría sobredeclarado en **210,00**.

**Partidas limpias**
- Enero: 3 limpias por **267,50**
- Febrero: 2 limpias por **158,20**
- Marzo: 1 limpia por **134,70**

Total de partidas limpias: **6 registros**, **560,40**.
