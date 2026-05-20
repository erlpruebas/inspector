Voy a revisar la estructura del CSV origen y luego generar el archivo de proveedores en el directorio de trabajo con las columnas pedidas.

El archivo tiene una columna `tipo`; voy a filtrar las filas donde `tipo` es `proveedor` y exportar solo las seis columnas solicitadas con los encabezados en español.

El primer intento falló por expansión de variables en PowerShell al invocar otro proceso. Voy a rehacerlo escapando el script y luego comprobar conteo y cabecera.

He creado el CSV de proveedores en:

[assistant_synthetic/proveedores.csv](D:/inspector/benchmarks/results/20260519_205916_918518/work/codex_gpt_5_5/test-10/assistant_synthetic/proveedores.csv)

Contiene 8 proveedores filtrados desde `contactos_50.csv` y las columnas: `Nombre`, `Empresa`, `Rol`, `Email`, `Ciudad`, `Prioridad`.
