Voy a revisar la estructura de los tres CSV y después cruzaré los registros para separar discrepancias, posibles duplicados y partidas sin incidencias.

La lectura directa con PowerShell falló por memoria al intentar abrir los encabezados en paralelo. Voy a cambiar a un lector CSV por streaming para no cargar archivos grandes completos.

Los archivos son pequeños y ya muestran un campo `estado`, pero voy a validar contra los importes y detectar duplicados por clave de gasto para no depender solo de la etiqueta del CSV.

Voy a ejecutar un script temporal de auditoría dentro del workspace para obtener el resumen completo; lo retiraré al terminar para no dejar archivos auxiliares.

Auditoría Q1 completada sobre los tres CSV indicados.

**Resumen**
- Registros revisados: 9
- Total declarado: 1000,30
- Total esperado: 1010,30
- Diferencia neta: -10,00

**Discrepancias**
- `assistant_synthetic/gastos_2026_02.csv`
  - 2026-02-22, `Licencia PDF`, software
  - Declarado: 19,90
  - Esperado: 29,90
  - Diferencia: -10,00
  - Estado: `importe_discrepante`

**Duplicados**
- `assistant_synthetic/gastos_2026_03.csv`
  - 2026-03-04, `Hotel Barcelona`, viajes
  - Importe: 210,00
  - Ocurrencias: 2
  - Estado: `posible_duplicado`

**Partidas limpias**
- Enero: Hotel Madrid 180,00; Taxi aeropuerto 38,50; Software encuestas 49,00
- Febrero: Cena cliente 96,20; Tren Valencia 62,00
- Marzo: Comida equipo 134,70

Por mes: enero no tiene incidencias; febrero concentra la discrepancia de -10,00; marzo no tiene diferencia de importe, pero sí un duplicado potencial.
