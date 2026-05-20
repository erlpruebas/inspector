Voy a leer `assistant_synthetic/contactos_50.csv` para ver su estructura y luego generar el CSV de proveedores con las columnas pedidas.

Estoy verificando si “CSV de proveedores” significa solo registros con `tipo=proveedor` o una transformación completa del archivo; con eso evitaré generar un CSV incorrecto.

Ya confirmé que hay 8 registros con `tipo=proveedor`. Ahora voy a generar un CSV nuevo solo con esos proveedores y con las columnas solicitadas, respetando el orden del archivo original.

El CSV ya está creado. Voy a verificar rápidamente que tenga el encabezado correcto y las 8 filas esperadas.

He creado el CSV de proveedores en [assistant_synthetic/proveedores.csv](/D:/inspector/benchmarks/results/20260519_205916_918518/work/codex_gpt_5_4_mini/test-10/assistant_synthetic/proveedores.csv) con las columnas `Nombre, Empresa, Rol, Email, Ciudad, Prioridad` y 8 registros filtrados desde `contactos_50.csv`.
