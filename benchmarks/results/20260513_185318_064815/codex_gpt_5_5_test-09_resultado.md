Usaré la skill de spreadsheets porque el trabajo es análisis de un CSV con importes y posibles duplicados. Primero voy a revisar el esquema del archivo y luego calcularé candidatos con criterios reproducibles.

Voy a tratar “duplicado” como cargos con misma fecha, comercio/descripcion e importe, salvo que el archivo tenga identificadores o estados que indiquen otra cosa. Revisaré columnas y muestras antes de fijar el criterio final.

El archivo es pequeño y trae una columna `estado`; además, los dos primeros registros ya vienen marcados como `posible_duplicado`. Voy a cuantificarlo agrupando por fecha, concepto, categoría e importes para separar el cargo legítimo del exceso.

Detecté un duplicado claro en `assistant_synthetic/gastos_2026_03.csv`.

| Fecha | Concepto | Categoría | Importe | Repeticiones | Cargo duplicado |
|---|---:|---|---:|---:|---:|
| 2026-03-04 | Hotel Barcelona | viajes | 210,00 | 2 | 210,00 |

Impacto económico: **210,00** de sobrecargo potencial.  
Total declarado en el CSV: **554,70**. Total corregido estimado: **344,70**.

Acción recomendada: **rechazar o reclamar uno de los dos cargos de “Hotel Barcelona” por 210,00**, manteniendo solo un cargo válido. El registro de “Comida equipo” por 134,70 no presenta duplicidad.
