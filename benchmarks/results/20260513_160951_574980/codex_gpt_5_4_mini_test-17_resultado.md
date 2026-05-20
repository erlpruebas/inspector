Voy a leer los cinco CSV locales, consolidar los gastos de enero a mayo y calcular totales mensuales, categorías principales y posibles anomalías. Primero revisaré la estructura de los archivos para ver columnas y formato antes de sumarizar.

Ya confirmé el esquema: `fecha`, `concepto`, `categoria`, `importe_declarado`, `importe_esperado`, `estado`. Ahora voy a consolidar los registros y separar lo normal de las filas marcadas como anomalías para sacar totales confiables.

He detectado una fila duplicada en marzo y otros registros marcados como revisión, así que voy a separar el total bruto del listado de anomalías para que el resumen no oculte ese detalle. Ahora recalculo por mes usando la fecha real.

He consolidado los 5 CSV y calculé el resumen usando `importe_declarado`.

**Totales por mes**
| Mes | Total |
|---|---:|
| Enero 2026 | 267.50 |
| Febrero 2026 | 178.10 |
| Marzo 2026 | 554.70 |
| Abril 2026 | 116.69 |
| Mayo 2026 | 293.40 |
| **Total enero-mayo** | **1,410.39** |

**Categorías principales**
1. `viajes` - 883.80
2. `comidas` - 249.30
3. `software` - 203.89
4. `oficina` - 73.40

Por peso sobre el total:
- `viajes`: 62.7%
- `comidas`: 17.7%
- `software`: 14.5%
- `oficina`: 5.2%

**Anomalías detectadas**
- `2026-02-22` - `Licencia PDF` - `software`: 19.90 declarado vs 29.90 esperado (`importe_discrepante`)
- `2026-03-04` - `Hotel Barcelona` - `viajes`: aparece 2 veces con 210.00 cada una (`posible_duplicado`)
- `2026-04-11` - `Taxi cliente` - `viajes`: 28.30 (`sin_recibo`)
- `2026-05-03` - `Suscripcion IA` - `software`: 120.00 (`revisar_proveedor`)

**Lectura rápida**
- Marzo es el mes con más gasto.
- `viajes` concentra la mayor parte del gasto total.
- Hay 5 filas marcadas como anómalas, correspondientes a 4 incidencias distintas.

Si quieres, te saco también el **total depurado excluyendo anomalías**.
