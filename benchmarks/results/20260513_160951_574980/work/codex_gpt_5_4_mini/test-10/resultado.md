Voy a leer `assistant_synthetic/contactos_50.csv`, identificar qué columnas trae y generar el CSV de proveedores con las columnas pedidas en el mismo directorio de trabajo.

Ya vi la estructura: el archivo trae `tipo` y `prioridad`, así que voy a filtrar solo `proveedor` y mapear las columnas a `Nombre, Empresa, Rol, Email, Ciudad y Prioridad`.

El primer intento falló por el perfil de PowerShell del entorno, así que lo voy a resolver con cmdlets nativos de PowerShell para evitar depender de `python` o del perfil cargado.

El CSV ya quedó generado. Voy a verificar las primeras filas para confirmar que las columnas quedaron en el orden pedido y que solo aparecen proveedores.

He creado el CSV de proveedores en:

[`D:\inspector\benchmarks\results\20260513_160951_574980\work\codex_gpt_5_4_mini\test-10\assistant_synthetic\proveedores.csv`](/D:/inspector/benchmarks/results/20260513_160951_574980/work/codex_gpt_5_4_mini/test-10/assistant_synthetic/proveedores.csv)

- Incluye 8 proveedores filtrados desde `contactos_50.csv`
- Columnas: `Nombre, Empresa, Rol, Email, Ciudad, Prioridad`

Si quieres, también puedo generarlo ordenado por prioridad o con un nombre de archivo distinto.
