Usaré la skill de Spreadsheets porque el trabajo consiste en consolidar y analizar CSV locales. Primero revisaré el formato de los archivos y luego calcularé los agregados y anomalías.

Los CSV tienen columnas homogéneas: `fecha`, `concepto`, `categoria`, `importe_declarado`, `importe_esperado`, `estado`. También veo valores anonimizados en algunas fechas/conceptos, así que trataré las anomalías por importes/estado y no por validez semántica de esos campos.

**Resumen Enero-Mayo 2026**

Total declarado: **1.410,39 €**  
Total esperado: **1.420,39 €**  
Diferencia neta: **-10,00 €**

**Total Por Mes**

| Mes | Total declarado | Registros | Anomalías |
|---|---:|---:|---:|
| Enero | 267,50 € | 3 | 0 |
| Febrero | 178,10 € | 3 | 1 |
| Marzo | 554,70 € | 3 | 2 |
| Abril | 116,69 € | 3 | 1 |
| Mayo | 293,40 € | 3 | 1 |

**Categorías Principales**

| Categoría | Total | % del total |
|---|---:|---:|
| viajes | 883,80 € | 62,7% |
| comidas | 249,30 € | 17,7% |
| software | 203,89 € | 14,5% |
| oficina | 73,40 € | 5,2% |

**Anomalías Detectadas**

| Mes | Concepto | Categoría | Declarado | Esperado | Estado | Diferencia |
|---|---|---|---:|---:|---|---:|
| Febrero | Licencia PDF | software | 19,90 € | 29,90 € | importe_discrepante | -10,00 € |
| Marzo | PERSON_0076 | viajes | 210,00 € | 210,00 € | posible_duplicado | 0,00 € |
| Marzo | PERSON_0076 | viajes | 210,00 € | 210,00 € | posible_duplicado | 0,00 € |
| Abril | Taxi cliente | viajes | 28,30 € | 28,30 € | sin_recibo | 0,00 € |
| Mayo | Suscripcion IA | software | 120,00 € | 120,00 € | revisar_proveedor | 0,00 € |

Marzo es el mes más alto por el posible duplicado de **210,00 €** registrado dos veces. La única diferencia monetaria real está en febrero: **Licencia PDF** declarada por **10,00 € menos** que el importe esperado.
