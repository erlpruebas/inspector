Voy a revisar la estructura de `assistant_synthetic/contactos_50.csv` para detectar las columnas disponibles y derivar el archivo de proveedores con el formato pedido.

La fuente tiene `tipo`, así que voy a filtrar `proveedor` y renombrar las columnas solicitadas manteniendo los datos originales.

Ya está generado. Haré una comprobación rápida del encabezado y algunas filas para confirmar que el CSV quedó con las columnas exactas.

Creado `assistant_synthetic/proveedores.csv` con las columnas solicitadas: Nombre, Empresa, Rol, Email, Ciudad y Prioridad.

Se exportaron 8 proveedores desde `assistant_synthetic/contactos_50.csv`.
