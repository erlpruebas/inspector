# Auditoría de Gastos Enero - Mayo 2026

## Resumen Ejecutivo
Se ha realizado la auditoría completa de los registros de gastos correspondientes a los meses de enero a mayo de 2026. Se analizaron 15 transacciones en total, identificando 4 incidencias que requieren intervención inmediata para garantizar la integridad financiera y el cumplimiento normativo interno.

## Hallazgos Detallados
| Fecha | Concepto | Categoría | Importe Declarado | Importe Esperado | Estado | Observación |
|-------|----------|-----------|-------------------|------------------|--------|-------------|
| 2026-02-14 | Licencia PDF | software | 19.9 | 29.9 | importe_discrepante | Diferencia de 10.0€ no justificada. |
| 2026-03-04 | Hotel Barcelona | viajes | 210.0 | 210.0 | posible_duplicado | Registro repetido idéntico en fecha y concepto. |
| 2026-03-04 | Hotel Barcelona | viajes | 210.0 | 210.0 | posible_duplicado | Registro repetido idéntico en fecha y concepto. |
| 2026-04-11 | Taxi cliente | viajes | 28.3 | 28.3 | sin_recibo | Ausencia de comprobante fiscal o ticket. |
| 2026-05-03 | Suscripcion IA | software | 120.0 | 120.0 | revisar_proveedor | Se requiere validación de vigencia y proveedor. |

## Recomendaciones de Control Interno

### 1. Prevención de Duplicados
- **Validación Automatizada:** Implementar reglas en el sistema de gestión de gastos que bloqueen o alerten ante coincidencias exactas de `fecha`, `concepto` e `importe` antes de la aprobación.
- **Conciliación Semanal:** Asignar al equipo de tesorería la revisión quincenal de movimientos con montos idénticos para detectar duplicaciones manuales o errores de carga.
- **Política de Reembolso Único:** Establecer que cada gasto solo puede ser procesado una vez por ejercicio fiscal, vinculando el ID de transacción al comprobante fiscal.

### 2. Gestión de Recibos y Soporte Documental
- **Carga Obligatoria:** Configurar el portal de gastos para que el sistema no permita enviar la declaración sin adjuntar el soporte digital (PDF, imagen o enlace a factura electrónica) en un plazo máximo de 48 horas.
- **Validación de Comprobantes:** Implementar un checklist de verificación que incluya: número de factura, fecha, IVA desglosado y datos fiscales del proveedor.
- **Sanción por Ausencia:** Aplicar la política de "sin comprobante, sin reembolso" con excepciones únicamente autorizadas por el Director Financiero, documentando la justificación en el expediente.

### 3. Control de Discrepancias de Importe
- **Umbral de Tolerancia:** Definir un margen de aceptación del ±2% para diferencias menores (ajustes de cambio, propinas, etc.). Cualquier desviación superior generará una alerta de revisión obligatoria.
- **Cruce de Datos:** Automatizar el比对 entre el `importe_declarado` y los contratos vigentes, presupuestos aprobados o listas de precios oficiales.
- **Capacitación Continua:** Realizar sesiones trimestrales al personal sobre la correcta imputación de impuestos, cargos adicionales y la diferencia entre precio neto e IVA incluido para minimizar errores de declaración.

### 4. Optimización de Proveedores y Suscripciones
- **Registro Centralizado:** Mantener un inventario vivo de licencias y servicios recurrentes con responsables, fechas de renovación y costos aprobados.
- **Auditoría de Utilización:** Revisar trimestralmente el uso real de las suscripciones (ej. software IA) para cancelar accesos inactivos o redundantes y evitar pagos por servicios no utilizados.

## Conclusión
La aplicación de estas medidas de control interno mitigará los riesgos de error administrativo, duplicidad de pagos y evasión de soporte documental. Se recomienda implementar un flujo de aprobación en dos niveles (declarante → validador financiero) a partir del trimestre siguiente y configurar alertas automáticas en el ERP para los estados críticos detectados.
