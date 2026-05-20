# Auditoría de Gastos – Enero a Mayo 2026

## Resumen de Gastos

| Mes | Nº de transacciones | Total Declarado (EUR) |
|-----|---------------------|-----------------------|
| Enero | 3 | 267.50 |
| Febrero | 3 | 178.10 |
| Marzo | 3 | 554.70 |
| Abril | 3 | 116.69 |
| Mayo | 3 | 293.40 |
| **Total** | **15** | **1 310.39** |

## Hallazgos Clave

| Tipo de Hallazgo | Detalle | Fecha | Concepto | Categoría | Importe Declarado | Importe Esperado | Estado |
|------------------|---------|-------|----------|-----------|-------------------|------------------|--------|
| **Duplicado** | Registro idéntico repetido | 2026‑03‑04 | Hotel Barcelona | viajes | 210.00 | 210.00 | posible_duplicado |
| **Duplicado** | Registro idéntico repetido | 2026‑03‑04 | Hotel Barcelona | viajes | 210.00 | 210.00 | posible_duplicado |
| **Sin Recibo** | Falta comprobante | 2026‑04‑11 | Taxi cliente | viajes | 28.30 | 28.30 | sin_recibo |
| **Discrepancia** | Importe declarado menor que esperado | 2026‑02‑22 | Licencia PDF | software | 19.90 | 29.90 | importe_discrepante |
| **Revisión Proveedor** | Necesita verificación de proveedor | 2026‑05‑03 | Suscripción IA | software | 120.00 | 120.00 | revisar_proveedor |

### Resumen de Problemas

| Problema | Nº de casos | Impacto |
|----------|-------------|---------|
| Duplicados | 2 | 210.00 EUR (duplicado) |
| Sin recibo | 1 | 28.30 EUR |
| Discrepancia | 1 | 10.00 EUR |
| Revisión proveedor | 1 | Riesgo de proveedor no verificado |

## Recomendaciones de Control Interno

1. **Prevención de Duplicados**
   - Implementar una regla de negocio que verifique la unicidad de la combinación *(fecha, concepto, categoría, importe)* antes de aprobar la transacción.
   - Utilizar un sistema de control de versiones o un hash de la línea de gasto para detectar duplicados automáticamente.
   - Establecer un proceso de revisión manual para transacciones con estado *posible_duplicado*.

2. **Captura Obligatoria de Recibos**
   - Requerir la carga de un comprobante digital (PDF, foto) antes de que la transacción pase a estado *ok*.
   - Configurar alertas automáticas cuando un gasto se registre con estado *sin_recibo*.
   - Realizar auditorías periódicas de la base de datos para identificar y corregir registros sin recibo.

3. **Validación de Importes**
   - Automatizar la comparación entre *importe_declarado* y *importe_esperado* al momento de la entrada de datos.
   - Generar un reporte de discrepancias que sea revisado por el departamento financiero.
   - Establecer límites de tolerancia (por ejemplo, ±5 %) y requerir justificación para desviaciones mayores.

4. **Gestión de Proveedores**
   - Mantener un registro actualizado de proveedores aprobados con sus datos de contacto y condiciones de pago.
   - Revisar y aprobar nuevos proveedores antes de permitir la creación de gastos asociados.
   - Para gastos con estado *revisar_proveedor*, asignar una tarea de verificación al responsable de compras.

5. **Segregación de Funciones y Auditoría Continua**
   - Separar las funciones de creación, aprobación y conciliación de gastos entre distintos usuarios.
   - Programar auditorías mensuales que revisen los estados de los gastos y los controles implementados.
   - Utilizar dashboards que muestren métricas clave (duplicados, sin recibo, discrepancias) en tiempo real.

6. **Capacitación y Políticas Claras**
   - Capacitar al personal en los procedimientos de registro de gastos y en la importancia de los controles.
   - Documentar y difundir las políticas de gastos, incluyendo ejemplos de casos de duplicados, sin recibo y discrepancias.

## Próximos Pasos

1. **Implementar** las reglas de unicidad y validación de importes en el sistema de gestión de gastos.
2. **Actualizar** el flujo de trabajo para requerir recibos digitales antes de la aprobación.
3. **Revisar** el proveedor *Suscripción IA* y actualizar la lista de proveedores aprobados.
4. **Realizar** una auditoría de los gastos de marzo y abril para confirmar que los duplicados y sin recibo se han corregido.
5. **Monitorear** los indicadores de control en un dashboard y ajustar los umbrales según sea necesario.

---
