# Informe de discrepancias de gastos Q1

Este informe detalla las discrepancias, duplicados y partidas limpias encontradas en los registros de gastos de enero, febrero y marzo de 2026.

## Resumen General

Se han analizado los archivos `gastos_2026_01.csv`, `gastos_2026_02.csv` y `gastos_2026_03.csv`.

## Discrepancias de Importe

Se ha identificado una discrepancia en el importe declarado y el importe esperado en el mes de febrero:

*   **Concepto:** Licencia PDF
*   **Fecha:** 2026-02-22
*   **Categoría:** software
*   **Importe Declarado:** 19.9
*   **Importe Esperado:** 29.9
*   **Diferencia:** -10.0

## Posibles Duplicados

Se han detectado posibles duplicados en el mes de marzo:

*   **Concepto:** Hotel Barcelona
*   **Fecha:** 2026-03-04
*   **Categoría:** viajes
*   **Importe Declarado:** 210.0
*   **Importe Esperado:** 210.0
*   **Observación:** La misma entrada aparece dos veces con el mismo importe. Se recomienda verificar si se trata de un error de registro o de un gasto real duplicado.

## Partidas Limpias (OK)

Las siguientes partidas se consideran limpias, sin discrepancias ni marcadas como posibles duplicados:

**Enero:**

*   2026-01-08, Hotel Madrid, viajes, 180.0, 180.0
*   2026-01-09, Taxi aeropuerto, viajes, 38.5, 38.5
*   2026-01-15, Software encuestas, software, 49.0, 49.0

**Febrero:**

*   2026-02-03, Cena cliente, comidas, 96.2, 96.2
*   2026-02-14, Tren Valencia, viajes, 62.0, 62.0

**Marzo:**

*   2026-03-19, Comida equipo, comidas, 134.7, 134.7

## Recomendaciones

1.  **Investigar la discrepancia de importe:** Revisar el gasto de "Licencia PDF" del 22 de febrero para aclarar la diferencia de 10.0 entre el importe declarado y el esperado.
2.  **Verificar duplicados:** Confirmar la naturaleza del registro duplicado "Hotel Barcelona" del 4 de marzo para evitar pagos innecesarios o corregir errores de entrada.
