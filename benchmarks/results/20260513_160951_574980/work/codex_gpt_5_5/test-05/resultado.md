Voy a inspeccionar el CSV local y calcular qué importe no encaja con el patrón de los datos. Primero leo encabezados y unas filas para entender la estructura.

Discrepancia detectada:

| Concepto | Importe declarado | Importe esperado | Recomendacion |
|---|---:|---:|---|
| Licencia PDF | 19,90 | 29,90 | Revisar la factura o corregir el importe declarado a 29,90 si el gasto esperado es el válido. |

El CSV marca esta fila con `estado = importe_discrepante`.
