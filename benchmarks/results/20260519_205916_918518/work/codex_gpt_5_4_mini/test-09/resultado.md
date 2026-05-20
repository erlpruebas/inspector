Voy a revisar el CSV de marzo, identificar posibles duplicados y cuantificar el impacto. Primero cargaré la guía de hojas de cálculo y luego inspeccionaré el archivo para detectar patrones de cargos repetidos.

Ya tengo la guía necesaria. Ahora voy a leer el CSV y revisar columnas, filas y posibles claves de duplicación para separar duplicados exactos de repeticiones plausibles por importe, fecha y concepto.

El archivo es pequeño, así que voy a calcular el impacto exactamente: sumaré importes tal cual vienen y luego eliminaré duplicados por fila completa y por clave operativa para ver si cambia el total.

Ya tengo el caso duplicado claro. Me falta solo cuantificarlo en proporción al total del mes para que la recomendación quede operativa: cuánto representa el duplicado sobre el gasto reportado.

He revisado `assistant_synthetic/gastos_2026_03.csv` y encontré 1 grupo de cargo duplicado exacto.

**Duplicado detectado**
- `fecha`: `PHONE_0093`
- `concepto`: `PERSON_0076`
- `categoria`: `viajes`
- `importe_declarado`: `210.0`
- `importe_esperado`: `210.0`
- `estado`: `posible_duplicado`
- Aparece **2 veces idéntico**

**Impacto económico**
- Total del archivo tal como está: `554.7`
- Importe duplicado a corregir: `210.0`
- Total neto esperado tras eliminar un duplicado: `344.7`
- Impacto relativo: `37.9%` del total reportado

**Acción recomendada**
- Marcar uno de los dos cargos como duplicado y excluirlo del reembolso/contabilización.
- Verificar el justificante original o el extracto bancario para confirmar si fue un cargo repetido o una duplicación de carga del archivo.
- Si se confirma, dejar un solo movimiento de `210.0` y mantener el resto sin cambios.
