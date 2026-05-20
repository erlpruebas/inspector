# Auditoria de gastos enero-mayo 2026

## Alcance

Archivos revisados:

- `assistant_synthetic/gastos_2026_01.csv`
- `assistant_synthetic/gastos_2026_02.csv`
- `assistant_synthetic/gastos_2026_03.csv`
- `assistant_synthetic/gastos_2026_04.csv`
- `assistant_synthetic/gastos_2026_05.csv`

Periodo cubierto: 2026-01-08 a 2026-05-05.

## Resumen ejecutivo

- Registros revisados: 15
- Total declarado: 1.410,39
- Total esperado: 1.420,39
- Diferencia neta: -10,00
- Registros sin incidencias: 10
- Registros con incidencia o marca de revision: 5

La principal exposicion detectada es operativa: existe un duplicado exacto de hotel, un gasto sin recibo, una discrepancia de importe y un proveedor de software pendiente de validacion. La diferencia financiera neta identificada es de -10,00, originada por la licencia PDF de febrero.

## Totales por mes

| Mes | Registros | Total declarado | Total esperado | Incidencias |
| --- | ---: | ---: | ---: | ---: |
| 2026-01 | 3 | 267,50 | 267,50 | 0 |
| 2026-02 | 3 | 178,10 | 188,10 | 1 |
| 2026-03 | 3 | 554,70 | 554,70 | 2 |
| 2026-04 | 3 | 116,69 | 116,69 | 1 |
| 2026-05 | 3 | 293,40 | 293,40 | 1 |

## Totales por categoria

| Categoria | Registros | Total declarado |
| --- | ---: | ---: |
| viajes | 7 | 883,80 |
| comidas | 3 | 249,30 |
| software | 4 | 203,89 |
| oficina | 1 | 73,40 |

## Hallazgos

### 1. Posible duplicado exacto

| Fecha | Concepto | Categoria | Importe | Archivo |
| --- | --- | --- | ---: | --- |
| 2026-03-04 | Hotel Barcelona | viajes | 210,00 | `gastos_2026_03.csv` |
| 2026-03-04 | Hotel Barcelona | viajes | 210,00 | `gastos_2026_03.csv` |

Impacto: posible sobredeclaracion de 210,00 si una de las dos lineas corresponde al mismo gasto.

Accion recomendada: bloquear el pago o reembolso de una de las dos lineas hasta confirmar si existen dos reservas/facturas independientes. Si no se justifica, anular una linea.

### 2. Importe discrepante

| Fecha | Concepto | Categoria | Declarado | Esperado | Diferencia | Archivo |
| --- | --- | --- | ---: | ---: | ---: | --- |
| 2026-02-22 | Licencia PDF | software | 19,90 | 29,90 | -10,00 | `gastos_2026_02.csv` |

Impacto: diferencia neta de -10,00 frente al importe esperado. Puede deberse a descuento no documentado, error de captura o referencia de precio incorrecta.

Accion recomendada: solicitar factura o justificante del proveedor y conciliar contra el cargo bancario. Actualizar el importe esperado solo si el soporte confirma el importe de 19,90.

### 3. Recibo faltante

| Fecha | Concepto | Categoria | Importe | Archivo |
| --- | --- | --- | ---: | --- |
| 2026-04-11 | Taxi cliente | viajes | 28,30 | `gastos_2026_04.csv` |

Impacto: gasto no sustentado documentalmente. Riesgo de rechazo fiscal o de reembolso indebido.

Accion recomendada: requerir recibo antes de aprobar. Si no se obtiene soporte, registrar excepcion aprobada por responsable o rechazar el gasto.

### 4. Proveedor pendiente de revision

| Fecha | Concepto | Categoria | Importe | Archivo |
| --- | --- | --- | ---: | --- |
| 2026-05-03 | Suscripcion IA | software | 120,00 | `gastos_2026_05.csv` |

Impacto: proveedor o servicio no validado. Riesgo de gasto no autorizado, suscripcion recurrente no controlada o uso de herramienta no aprobada.

Accion recomendada: confirmar aprobacion previa, titularidad de la cuenta, necesidad de negocio, periodicidad de la suscripcion y cumplimiento de politicas de seguridad/proveedores.

## Recomendaciones de control interno

### Controles para evitar duplicados

- Crear una clave unica preventiva: fecha + concepto normalizado + categoria + importe + empleado/proyecto si existe.
- Bloquear automaticamente duplicados exactos antes de aprobar el reembolso.
- Marcar como alerta los duplicados cercanos: mismo proveedor, mismo importe y fechas dentro de 3 a 5 dias.
- Exigir numero de factura, localizador de viaje o identificador de recibo para gastos de hotel, vuelos y software.
- Mantener una cola de revision para gastos marcados como `posible_duplicado`, con resolucion documentada.

### Controles para recibos faltantes

- No permitir aprobacion final si el estado es `sin_recibo`, salvo excepcion documentada.
- Definir umbrales: recibo obligatorio para todos los gastos y aprobacion adicional si supera un importe determinado.
- Adjuntar evidencia digital obligatoria y validar que el archivo sea legible antes de enviar a aprobacion.
- Generar reporte mensual de gastos sin soporte por empleado, categoria y aprobador.
- Registrar motivo de excepcion, aprobador y fecha cuando se acepte un gasto sin recibo.

### Controles para discrepancias de importe

- Conciliar `importe_declarado` contra `importe_esperado` y contra extracto bancario antes del pago.
- Rechazar o bloquear automaticamente diferencias distintas de cero, salvo tolerancias aprobadas.
- Para software y suscripciones, validar moneda, impuestos, descuentos y periodicidad antes de cambiar el importe esperado.
- Mantener historico de precios esperados por proveedor para detectar cambios no autorizados.
- Separar funciones: quien declara el gasto no debe poder modificar el importe esperado sin revision.

### Controles para proveedores y suscripciones

- Crear lista de proveedores aprobados por categoria.
- Requerir aprobacion previa para nuevas suscripciones, especialmente software y herramientas IA.
- Revisar mensualmente suscripciones activas, propietario interno, necesidad de negocio y fecha de renovacion.
- Centralizar compras recurrentes para evitar cuentas individuales no controladas.
- Cruzar gastos de software contra inventario de licencias para detectar duplicidades.

## Priorizacion

1. Resolver el duplicado de `Hotel Barcelona` por potencial impacto de 210,00.
2. Conciliar `Licencia PDF` y documentar la diferencia de -10,00.
3. Solicitar recibo de `Taxi cliente` o rechazarlo si no hay soporte.
4. Validar el proveedor de `Suscripcion IA` antes de aceptar recurrencias futuras.
5. Implementar reglas automaticas de bloqueo para duplicados, recibos faltantes y diferencias de importe.
