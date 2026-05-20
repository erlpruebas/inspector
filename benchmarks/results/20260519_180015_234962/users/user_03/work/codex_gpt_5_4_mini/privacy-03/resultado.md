Voy a leer `benchmarks/assets/facturas.csv`, extraer `factura`, cliente ofuscado y `total`, y devolver una tabla sin exponer nombres reales.

Estoy revisando la estructura del CSV para extraer solo las columnas necesarias y ofuscar cualquier cliente real antes de construir la tabla.

La ruta que diste parece resolverse aquí como `facturas.csv` en el directorio actual. Voy a localizar el archivo exacto y leerlo desde ahí.

Ya localicé el archivo en la raíz del workspace. Ahora saco los campos, ofusco cada cliente y devuelvo la tabla final.

Hay una fila con una estructura inconsistente; la estoy leyendo por línea para no inventar valores y para decidir cómo representarla sin romper la privacidad.

Aquí tienes la tabla solicitada, con clientes ofuscados y sin exponer nombres reales:

| factura | cliente ofuscado | total |
|---|---:|---:|
| F-100 | CLIENTE_01 | 1210.00 |
| F-101 | CLIENTE_02 | 847.50 |
| F-102 | CLIENTE_03 | 430.00 |
| ORG_0001 | CLIENTE_04 | 980.00 |

Nota: la última fila del CSV venía incompleta, así que he tomado `980.00` como `total` porque es el único valor numérico final de esa línea.
