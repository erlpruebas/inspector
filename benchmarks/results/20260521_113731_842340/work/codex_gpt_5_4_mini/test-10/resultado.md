Voy a leer el CSV de origen y transformar sus columnas al esquema solicitado. Primero inspecciono la estructura de `assistant_synthetic/contactos_50.csv` para mapear los campos correctos antes de escribir el nuevo archivo.

La fuente ya trae `tipo` y `prioridad`, así que voy a filtrar solo `proveedor` y reordenar a `Nombre, Empresa, Rol, Email, Ciudad, Prioridad`. Ahora verifico cuántos registros entran para asegurar que el CSV final sea consistente.

Voy a escribir el CSV resultante en `assistant_synthetic/proveedores.csv` con solo los 8 registros de `tipo=proveedor` y las columnas pedidas en el orden exacto.

Ya quedó creado. Hago una verificación rápida del encabezado y el número de filas para confirmar que no hubo desajustes al exportar.

He creado el CSV de proveedores en [assistant_synthetic/proveedores.csv](D:\inspector\benchmarks\results\20260521_113731_842340\work\codex_gpt_5_4_mini\test-10\assistant_synthetic\proveedores.csv).

Incluye 8 proveedores con las columnas solicitadas: `Nombre, Empresa, Rol, Email, Ciudad y Prioridad`.
