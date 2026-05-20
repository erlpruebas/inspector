Usaré la skill de Spreadsheets porque el trabajo es análisis de un CSV local: primero revisaré estructura y columnas, luego calcularé duplicados e impacto.

Ya tengo la guía necesaria. Ahora voy a leer el CSV y perfilar campos, importes y posibles claves de duplicidad antes de clasificar falsos positivos.

El archivo tiene 3 movimientos. Hay un par exactamente repetido con mismo `fecha`, `concepto`, `categoria`, `importe_declarado`, `importe_esperado` y `estado`; calcularé el exceso contando una sola línea como válida.

Auditado `assistant_synthetic/gastos_2026_03.csv`.

Detecté 1 cargo duplicado exacto:

| Filas CSV | Fecha | Concepto | Categoría | Importe |
|---|---|---|---|---:|
| 2 y 3 | `PHONE_0093` | `PERSON_0076` | viajes | 210.00 |

Impacto económico:
- Total declarado en el archivo: **554.70**
- Total correcto si se conserva solo una ocurrencia: **344.70**
- Exceso por duplicidad: **210.00**

Acción recomendada: **rechazar o revertir una de las dos líneas duplicadas** y mantener solo una como gasto válido. No hay diferencia entre `importe_declarado` e `importe_esperado`; el problema es la doble contabilización del mismo cargo.
