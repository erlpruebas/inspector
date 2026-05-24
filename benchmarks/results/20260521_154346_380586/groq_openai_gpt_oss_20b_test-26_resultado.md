**Auditoría de Gastos – Enero a Mayo 2026**

---

### 1. Resumen Ejecutivo  
| Mes | Total de transacciones | Duplicados | Recibos faltantes | Discrepancias de importe | Otros |
|-----|------------------------|------------|-------------------|--------------------------|-------|
| Enero | 3 | 0 | 0 | 0 | 0 |
| Febrero | 3 | 0 | 0 | 1 | 0 |
| Marzo | 3 | 2 | 0 | 0 | 0 |
| Abril | 3 | 0 | 1 | 0 | 0 |
| Mayo | 3 | 0 | 0 | 0 | 1 |
| **Total** | **15** | **2** | **1** | **1** | **1** |

> **Conclusión**: Se identificaron 5 incidencias relevantes que requieren atención inmediata para fortalecer el control interno.

---

### 2. Hallazgos Detallados  

| Mes | Fecha | Concepto | Categoría | Importe Declarado | Importe Esperado | Estado | Observación |
|-----|-------|----------|-----------|-------------------|------------------|--------|-------------|
| Febrero | 2026‑02‑22 | Licencia PDF | software | 19.9 | 29.9 | importe_discrepante | Diferencia de 10.0 € |
| Marzo | 2026‑03‑04 | Hotel Barcelona | viajes | 210.0 | 210.0 | posible_duplicado | Registro duplicado |
| Marzo | 2026‑03‑04 | Hotel Barcelona | viajes | 210.0 | 210.0 | posible_duplicado | Registro duplicado |
| Abril | 2026‑04‑11 | Taxi cliente | viajes | 28.3 | 28.3 | sin_recibo | Recibo no presentado |
| Mayo | 2026‑05‑03 | Suscripcion IA | software | 120.0 | 120.0 | revisar_proveedor | Revisión de proveedor necesaria |

---

### 3. Recomendaciones de Control Interno  

1. **Prevención de Duplicados**  
   - Implementar un sistema de validación que compare *fecha, concepto, categoría* y *importe* antes de registrar una nueva transacción.  
   - Generar alertas automáticas cuando se detecte un registro idéntico dentro de un rango de 24 h.  
   - Capacitar al personal en la importancia de revisar el historial antes de registrar gastos.

2. **Gestión de Recibos**  
   - Establecer un protocolo obligatorio: cada gasto debe ir acompañado de un recibo digitalizado o fotográfico antes de la aprobación.  
   - Utilizar un software de gestión de facturas que marque los registros sin recibo y los bloquee para el pago.  
   - Realizar auditorías mensuales de los estados “sin_recibo” y exigir la presentación de la documentación faltante.

3. **Control de Importes**  
   - Configurar reglas de negocio que comparen *importe_declarado* con *importe_esperado* y bloqueen la aprobación si la diferencia supera un umbral predefinido (ej. 5 %).  
   - En caso de discrepancia, generar un ticket de revisión que sea atendido por el área de finanzas antes de la liquidación.  
   - Mantener un registro histórico de ajustes para análisis de tendencias y posibles fraudes.

4. **Revisión de Proveedores**  
   - Para estados “revisar_proveedor”, crear un proceso de due diligence que verifique la legitimidad, precios competitivos y cumplimiento de contratos.  
   - Establecer un comité de compras que apruebe nuevos proveedores y revise los existentes cada 6 meses.  
   - Documentar las decisiones de revisión y conservar la evidencia para auditorías externas.

5. **Capacitación y Concienciación**  
   - Realizar sesiones trimestrales de formación sobre políticas de gastos, uso correcto del sistema y consecuencias de incumplimientos.  
   - Distribuir guías rápidas y check‑lists para el registro de gastos.  
   - Fomentar una cultura de reporte proactivo de anomalías.

6. **Monitoreo Continuo**  
   - Implementar dashboards en tiempo real que muestren métricas clave: número de duplicados, faltantes de recibo, discrepancias de importe, etc.  
   - Programar alertas por correo a los responsables de finanzas cuando los indicadores superen umbrales críticos.  
   - Revisar los informes mensuales con la alta dirección para asegurar la trazabilidad y la mejora continua.

---

### 4. Próximos Pasos  

1. **Implementar las reglas de validación** en el sistema de registro de gastos antes del 30 junio.  
2. **Desarrollar el dashboard de control** y capacitar al equipo de finanzas en su uso.  
3. **Revisar y actualizar** la política de gastos y los procedimientos de aprobación en la próxima reunión de auditoría interna.  

---

**Responsable de la auditoría**:  
[Nombre del auditor] – Departamento de Control Interno  
Fecha: 2026‑05‑31
