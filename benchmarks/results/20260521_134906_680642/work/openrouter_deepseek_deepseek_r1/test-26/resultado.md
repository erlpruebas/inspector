# Auditoría de Gastos Enero-Mayo 2026

## Resumen Ejecutivo

Se auditaron 15 transacciones de gastos desde enero hasta mayo de 2026. Se identificaron 4 casos que requieren atención: un duplicado, un recibo faltante, una discrepancia en importe y un gasto que necesita revisión de proveedor.

## Hallazgos Detallados

### 1. Duplicados
- **Caso**: "Hotel Barcelona" el 2026-03-04 por importe de 210.0 EUR, registrado dos veces en marzo.
- **Impacto**: Posible pago duplicado o error de registro.
- **Recomendación**: Implementar un control que detecte y prevenga registros duplicados basado en concepto, fecha e importe antes de la contabilización.

### 2. Recibos Faltantes
- **Caso**: "Taxi cliente" el 2026-04-11 por 28.3 EUR, marcado como "sin_recibo".
- **Impacto**: Falta de soporte documental para la deducción o reembolso.
- **Recomendación**: Establecer una política obligatoria de adjuntar recibo para todo gasto. Crear un proceso de seguimiento semanal para solicitar documentos pendientes.

### 3. Discrepancias de Importe
- **Caso**: "Licencia PDF" el 2026-02-22 con importe declarado de 19.9 EUR frente a 29.9 EUR esperado, marcado como "importe_discrepante".
- **Impacto**: Diferencia de 10.0 EUR no justificada, afectando la precisión financiera.
- **Recomendación**: Introducir una conciliación mensual obligatoria entre importes declarados y facturas o presupuestos originales antes del pago.

### 4. Otros Problemas
- **Caso**: "Suscripcion IA" el 2026-05-03 por 120.0 EUR, marcado como "revisar_proveedor".
- **Impacto**: Riesgo de gasto con proveedor no autorizado o no evaluado.
- **Recomendación**: Crear y mantener una lista de proveedores aprobados. Implementar un flujo de aprobación para nuevos proveedores o servicios recurrentes.

## Recomendaciones Generales de Control Interno

1. **Automatización de Detección**: Utilizar un sistema que alerte sobre posibles duplicados al ingresar un gasto con mismo concepto, fecha e importe en un período corto.
2. **Política Documental Estricta**: Ningún gasto debe ser reembolsado o contabilizado sin el recibo digital o físico correspondiente. Asignar un responsable de seguimiento.
3. **Proceso de Conciliación Mensual**: Revisar sistemáticamente todas las transacciones comparando el importe declarado con el esperado (presupuesto, factura,
