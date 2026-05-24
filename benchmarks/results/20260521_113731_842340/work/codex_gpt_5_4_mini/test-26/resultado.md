Voy a revisar los cinco CSV de enero a mayo, consolidar gastos y buscar duplicados, recibos faltantes y discrepancias de importes o fechas. Después te devuelvo un informe con hallazgos y controles internos concretos.

Ya localicé los archivos. Ahora voy a inspeccionar la estructura de los CSV para definir las reglas de cruce antes de calcular duplicados y faltantes.

Ya confirmé el esquema: `fecha`, `concepto`, `categoria`, `importe_declarado`, `importe_esperado` y `estado`. Ahora estoy consolidando las 15 filas para clasificar hallazgos por tipo y por mes.

Ya tengo la base del dictamen. Estoy sacando un resumen por mes y por tipo de excepción para que el informe distinga entre error contable, falta documental y revisión operativa.

**Resumen ejecutivo**

He auditado los 15 gastos de enero a mayo de 2026. Hay 4 excepciones relevantes:

- 1 duplicado de alta confianza en marzo
- 1 importe discrepante en febrero
- 1 gasto sin recibo en abril
- 1 gasto con revisión de proveedor en mayo

La diferencia neta entre `importe_declarado` e `importe_esperado` es de `-10,00`, causada por `Licencia PDF` en febrero. El duplicado de marzo no altera esa variación neta porque aparece duplicado tanto en el declarado como en el esperado, pero sí infla el gasto bruto.

**Hallazgos**

| Fecha | Mes | Concepto | Hallazgo | Impacto |
|---|---:|---|---|---:|
| 2026-03-04 | marzo | Hotel Barcelona | Duplicado exacto, repetido 2 veces | `210,00` por cada línea duplicada |
| 2026-02-22 | febrero | Licencia PDF | Importe declarado inferior al esperado | `-10,00` |
| 2026-04-11 | abril | Taxi cliente | Falta recibo | Riesgo documental y de reembolso |
| 2026-05-03 | mayo | Suscripcion IA | Revisar proveedor | Riesgo de aprobación/contrato |

**Resumen por mes**

- Enero: `267,50` sin incidencias
- Febrero: `178,10` declarado vs `188,10` esperado, variación `-10,00`
- Marzo: `554,70` bruto, con duplicado; sin depurar, el mes queda sobrestado
- Abril: `116,69` sin diferencias numéricas, pero con falta de recibo
- Mayo: `293,40` sin diferencias numéricas, pero con revisión de proveedor pendiente

**Lectura de control**

- El duplicado de marzo es el riesgo más claro de sobrepago.
- El caso de febrero apunta a una discrepancia de captura o facturación.
- La ausencia de recibo en abril es un fallo de soporte documental.
- La revisión de proveedor en mayo es una alerta de control de compras, no necesariamente un error contable.

**Recomendaciones de control interno**

1. **Bloqueo de duplicados**
- Validar combinaciones únicas `fecha + concepto + categoría + importe + proveedor`.
- Avisar al usuario si intenta cargar una línea idéntica a otra ya registrada.
- Requerir revisión manual de cualquier gasto marcado como posible duplicado antes de pagar.

2. **Conciliación importe-declarado vs recibo**
- Obligar a que el importe declarado coincida con el recibo o justificar la diferencia con un motivo estándar.
- Marcar automáticamente diferencias por encima de un umbral, por ejemplo `1,00` o `2%`.
- Hacer revisión independiente de los casos discrepantes.

3. **Política de recibos obligatorios**
- No aceptar reembolsos sin recibo salvo excepción formal aprobada.
- Requerir carga del justificante en el momento de la solicitud.
- Mantener un registro de excepciones con fecha de regularización.

4. **Control de proveedores y suscripciones**
- Aprobar altas o renovaciones de proveedor antes del cargo.
- Revisar cargos recurrentes con owner asignado.
- Exigir evidencia de contrato o renovación para software y suscripciones.

5. **Cierre mensual con revisión de excepciones**
- Emitir un reporte mensual de `duplicados`, `sin_recibo`, `importe_discrepante` y `revisar_proveedor`.
- Asignar responsable y fecha límite por cada excepción.
- Cerrar el mes solo cuando las excepciones queden resueltas o justificadas.

6. **Trazabilidad y aprobación**
- Registrar quién cargó, quién aprobó y quién revisó cada gasto.
- Separar funciones de aprobación y pago cuando sea posible.
- Conservar un historial de cambios para auditoría.

Si quieres, puedo convertir esto en una tabla de control más formal, con `hallazgo`, `riesgo`, `impacto` y `acción correctiva` lista para pegar en un informe.
