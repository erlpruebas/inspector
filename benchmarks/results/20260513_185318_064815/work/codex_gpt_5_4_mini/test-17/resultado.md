Voy a leer los CSV de enero a mayo, calcular totales por mes, agrupar categorías principales y detectar anomalías en los importes. Primero revisaré el formato de los archivos para decidir la agregación correcta.

Ya tengo el esquema de trabajo: ahora voy a revisar columnas y muestras de los cinco CSV para confirmar qué campo usar como importe y cómo clasificar categorías antes de calcular los totales.

Ya confirmé el esquema. Ahora calcularé el total mensual y el acumulado por categoría sobre `importe_declarado`, y separaré las filas con `estado` no normal para listar anomalías con su diferencia frente a `importe_esperado` cuando exista.

El primer cálculo mostró un problema de asignación en PowerShell, así que lo rehago con objetos derivados para asegurar totales correctos por mes y por categoría. También revisaré si conviene reportar el total bruto y el neto tras excluir anomalías.

Los datos ya están cerrados. Haré un último cálculo de participación por categoría para que el resumen quede más útil, y luego te entrego el agregado mensual con las anomalías identificadas.

He agregado los 15 movimientos y tomé `importe_declarado` como base del gasto total.

**Resumen total**
- Total enero-mayo: **1.410,39 €**
- Total esperado: **1.420,39 €**
- Diferencia global: **-10,00 €**

**Total por mes**

| Mes | Total declarado | Total esperado | Dif. |
|---|---:|---:|---:|
| 2026-01 | 267,50 € | 267,50 € | 0,00 € |
| 2026-02 | 178,10 € | 188,10 € | -10,00 € |
| 2026-03 | 554,70 € | 554,70 € | 0,00 € |
| 2026-04 | 116,69 € | 116,69 € | 0,00 € |
| 2026-05 | 293,40 € | 293,40 € | 0,00 € |

**Categorías principales**

| Categoría | Total | Peso |
|---|---:|---:|
| viajes | 883,80 € | 62,7% |
| comidas | 249,30 € | 17,7% |
| software | 203,89 € | 14,5% |
| oficina | 73,40 € | 5,2% |

**Anomalías**
- `2026-02-22` `Licencia PDF` (`software`): **19,90 €** declarado vs **29,90 €** esperado, diferencia **-10,00 €**, estado `importe_discrepante`.
- `2026-03-04` `Hotel Barcelona` (`viajes`): marcado `posible_duplicado` en dos filas idénticas de **210,00 €**.
- `2026-04-11` `Taxi cliente` (`viajes`): **28,30 €**, estado `sin_recibo`.
- `2026-05-03` `Suscripcion IA` (`software`): **120,00 €**, estado `revisar_proveedor`.

Si quieres, puedo darte también un resumen “limpio” excluyendo duplicados y ajustando la discrepancia de febrero.
