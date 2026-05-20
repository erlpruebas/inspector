Voy a usar la skill de Spreadsheets porque el encargo es transformar un CSV local y dejar otro CSV generado en el workspace. Primero revisaré la estructura de `contactos_50.csv` para mapear columnas correctamente.

El archivo tiene columnas en minúscula y una columna `tipo`; generaré el nuevo CSV filtrando solo `tipo = proveedor` y renombrando las columnas al formato pedido: `Nombre, Empresa, Rol, Email, Ciudad, Prioridad`.

Ya quedó escrito el archivo de proveedores. Estoy verificando ahora el número de filas y una muestra para asegurar que el filtro y los encabezados salieron correctos.

He creado el CSV filtrando los contactos con `tipo = proveedor` y con las columnas solicitadas en este orden: `Nombre, Empresa, Rol, Email, Ciudad, Prioridad`.

Archivo generado: [proveedores.csv](D:/inspector/benchmarks/results/20260513_160951_574980/work/codex_gpt_5_5/test-10/assistant_synthetic/proveedores.csv)

Verificado: contiene 8 proveedores.
