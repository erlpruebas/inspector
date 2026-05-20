**Auditoría de Gastos – Enero a Mayo 2026**

---

### 1. Resumen Ejecutivo  
Durante el periodo analizado se registraron 15 transacciones. Se identificaron tres tipos de anomalías:

| Tipo de anomalía | Nº de casos | Descripción breve |
|------------------|-------------|-------------------|
| Duplicados | 2 | Hotel Barcelona (03/04/2026) |
| Recibos faltantes | 1 | Taxi cliente (11/04/2026) |
| Discrepancias de importe | 1 | Licencia PDF (22/02/2026) |
| Revisión de proveedor | 1 | Suscripción IA (03/05/2026) |

---

### 2. Hallazgos Detallados  

| Mes | Fecha | Concepto | Categoría | Importe Declarado | Importe Esperado | Estado | Comentario |
|-----|-------|----------|-----------|-------------------|------------------|--------|------------|
| Enero | 08/01 | Hotel Madrid | viajes | 180.0 | 180.0 | ok | - |
| Enero | 09/01 | Taxi aeropuerto | viajes | 38.5 | 38.5 | ok | - |
| Enero | 15/01 | Software encuestas | software | 49.0 | 49.0 | ok | - |
| Febrero | 03/02 | Cena cliente | comidas | 96.2 | 96.2 | ok | - |
| Febrero | 14/02 | Tren Valencia | viajes | 62.0 | 62.0 | ok | - |
| Febrero | 22/02 | Licencia PDF | software | 19.9 | 29.9 | importe_discrepante | Diferencia de 10.0 |
| Marzo | 04/03 | Hotel Barcelona | viajes | 210.0 | 210.0 | posible_duplicado | Duplicado |
| Marzo | 04/03 | Hotel Barcelona | viajes | 210.0 | 210.0 | posible_duplicado | Duplicado |
| Marzo | 19/03 | Comida equipo | comidas | 134.7 | 134.7 | ok | - |
| Abril | 02/04 | Dominio anual | software | 14.99 | 14.99 | ok | - |
| Abril | 11/04 | Taxi cliente | viajes | 28.3 | 28.3 | sin_recibo | Recibo no presentado |
| Abril | 25/04 | Material oficina | oficina | 73.4 | 73.4 | ok | - |
| Mayo | 01/05 | Vuelo Barcelona | viajes | 155.0 | 155.0 | ok | - |
| Mayo | 03/05 | Suscripcion IA | software | 120.0 | 120.0 | revisar_proveedor | Verificar proveedor |
| Mayo | 05/05 | Cafe reunion | comidas | 18.4 | 18.4 | ok | - |

---

### 3. Recomendaciones de Control Interno  

| Área | Problema Detectado | Recomendación | Responsable | Plazo |
|------|--------------------|---------------|-------------|-------|
| **Gestión de facturas** | Recibo faltante (Taxi cliente 11/04) | Implementar un proceso de captura de recibos antes de la aprobación de gasto. Requerir el archivo adjunto o número de factura en el sistema de reporte. | Departamento de Finanzas | 30 días |
| **Validación de importes** | Discrepancia de importe (Licencia PDF 22/02) | Establecer una regla de validación automática que compare `importe_declarado` con `importe_esperado` y genere alerta si difiere >5%. | Equipo de TI | 15 días |
| **Control de duplicados** | Duplicados (Hotel Barcelona 04/03) | Añadir un filtro de duplicados basado en combinación de fecha, concepto y categoría. Solicitar confirmación antes de registrar una transacción idéntica. | Departamento de Compras | 20 días |
| **Verificación de proveedores** | Revisión de proveedor (Suscripción IA 03/05) | Crear una lista aprobada de proveedores y obligar a seleccionar de esa lista. Si el proveedor no está en la lista, requerir aprobación del gerente. | Departamento de Compras | 10 días |
| **Capacitación** | Falta de conocimiento sobre políticas de gasto | Realizar sesiones trimestrales de capacitación sobre políticas de gasto, requisitos de documentación y procedimientos de aprobación. | RRHH | 60 días |
| **Auditoría interna** | Falta de seguimiento de anomalías | Programar auditorías mensuales de gastos con revisión de anomalías detectadas. Generar reportes de seguimiento y acciones correctivas. | Auditoría Interna | 30 días |

---

### 4. Próximos Pasos  

1. **Implementar las reglas de validación** en el sistema de reporte de gastos.  
2. **Actualizar la lista de proveedores** y habilitar la selección obligatoria.  
3. **Capacitar al personal** sobre la importancia de adjuntar recibos y verificar importes.  
4. **Realizar la primera auditoría interna** en 30 días para medir la efectividad de las mejoras.  

---

**Conclusión**  
Con la adopción de las recomendaciones anteriores se espera reducir significativamente los riesgos de duplicados, faltas de documentación y discrepancias de importe, mejorando la integridad y confiabilidad de los registros de gastos.
