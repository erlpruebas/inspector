Voy a leer los CSV locales y cruzarlos por importe y fecha para sacar solo coincidencias y discrepancias, omitiendo nombres o identificadores sensibles. Primero confirmo el esquema de ambos archivos y luego hago el emparejamiento.

Los CSV no están en `benchmarks/assets` dentro de este workspace; están en la raíz del directorio de trabajo. Voy a leer esos dos archivos directamente y cruzarlos con tolerancia de fecha para identificar pares plausibles.

Los archivos tienen un formato limpio pero los valores están anonimizados con tokens. Voy a importarlos como CSV para asegurar que cada fila quede separada y luego comparar importes y fechas.

Ya confirmé que hay pocos registros y que uno de los archivos tiene una estructura rara: el pago aparece como una sola fila con campos tokenizados. Voy a revisar el contenido bruto para ver si las fechas/importe están en otras columnas o si el archivo viene con delimitadores atípicos.

Hay dos irregularidades: en pagos la fila está compactada en una sola línea con varios registros, y en facturas la última fila viene con una columna faltante. Voy a normalizar ambas tablas por coma y luego intentar emparejar los registros que sí tienen un número de campos coherente.

Coincidencias:

- El pago que referencia `F-100` encaja con la factura `F-100` por referencia y por fecha aproximada.
- El pago que menciona la factura `101` encaja con la factura `F-101` por referencia y por fecha aproximada.

Discrepancias:

- La factura `F-102` no tiene un pago relacionado visible.
- La factura con total `980.00` no muestra un pago asociado claro.
- Hay un pago aislado de `125.00` sin factura correspondiente.
- No puedo पुष्टि confirmar ninguna coincidencia exacta de importe visible entre ambos ficheros, porque en el archivo de pagos parte de los importes y fechas están anonimizados o mal alineados.
