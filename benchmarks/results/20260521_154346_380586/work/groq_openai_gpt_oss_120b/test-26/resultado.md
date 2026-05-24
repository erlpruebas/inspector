# Auditoría de gastos (enero – mayo 2026)

## 1. Resumen financiero
| Mes | Importe declarado total | Comentarios |
|-----|------------------------|-------------|
| Enero | **267,50 €** | Todos los registros con estado *ok*. |
| Febrero | **178,10 €** | 1 registro con discrepancia de importe. |
| Marzo | **554,70 €** | 2 registros marcados como posible duplicado. |
| Abril | **116,69 €** | 1 registro sin recibo. |
| Mayo | **293,40 €** | 1 registro que requiere revisión de proveedor. |
| **Total** | **1 410,39 €** |  |

## 2. Incidencias detectadas

| Fecha | Concepto | Categoría | Importe declarado | Importe esperado | Estado | Tipo de incidencia |
|-------|----------|-----------|-------------------|------------------|--------|--------------------|
| 2026‑02‑22 | Licencia PDF | software | 19,90 € | 29,90 € | importe_discrepante | **Discrepancia de importe** |
| 2026‑03‑04 | Hotel Barcelona | viajes | 210,00 € | 210,00 € | posible_duplicado | **Posible duplicado** (registro repetido) |
| 2026‑03‑04 | Hotel Barcelona | viajes | 210,00 € | 210,00 € | posible_duplicado | **Posible duplicado** |
| 2026‑04‑11 | Taxi cliente | viajes | 28,30 € | 28,30 € | sin_recibo | **Falta de recibo** |
| 2026‑05‑03 | Suscripción IA | software | 120,00 € | 120,00 € | revisar_proveedor | **Revisión de proveedor** |

## 3. Análisis de riesgos

| Riesgo | Impacto | Probabilidad | Observaciones |
|--------|---------|--------------|---------------|
| Duplicación de gastos | Sobregasto y fraude | Media | Detectado en marzo (Hotel Barcelona). |
| Discrepancia entre importe declarado y esperado | Errores de contabilización o fraude | Baja | Caso único en febrero (Licencia PDF). |
| Falta de documentación (recibos) | Dificultad de auditoría, posible incumplimiento fiscal | Media | Taxi cliente en abril. |
| Proveedores no verificados | Pago a proveedores no autorizados o precios no competitivos | Baja | Suscripción IA en mayo. |

## 4. Recomendaciones de control interno

1. **Procedimiento de validación automática al cargar gastos**  
   - Verificar que el importe declarado coincida con el importe esperado (ej. precios de catálogo o contrato).  
   - Bloquear la carga si la diferencia supera el **5 %** y requerir justificación.

2. **Detección de duplicados**  
   - Implementar regla de unicidad basada en combinación **fecha + concepto + importe**.  
   - Generar alerta y requerir confirmación del responsable antes de aceptar el segundo registro.

3. **Gestión de recibos**  
   - Obligar a adjuntar el comprobante digital antes de que el gasto pueda pasar a estado *ok*.  
   - Establecer un plazo máximo de **48 h** para subir el recibo; de lo contrario, el gasto queda en estado *pendiente* y no se autoriza el reembolso.

4. **Revisión y aprobación de proveedores**  
   - Mantener un registro actualizado de proveedores aprobados y sus tarifas.  
   - Para cualquier gasto con estado *revisar_proveedor*, requerir una validación del área de compras antes de la contabilización.

5. **Flujo de aprobación escalonado**  
   - **Nivel 1**: Responsable directo revisa y aprueba gastos menores (< 100 €).  
   - **Nivel 2**: Supervisor revisa gastos entre 100 € y 500 € y verifica documentación.  
   - **Nivel 3**: Finanzas revisa y autoriza gastos > 500 € y casos con incidencias (duplicados, discrepancias).

6. **Auditorías mensuales de control**  
   - Generar un reporte automático de incidencias (duplicados, sin recibo, discrepancias) y revisarlo en la reunión de cierre mensual.  
   - Aplicar acciones correctivas y actualizar los procedimientos según los hallazgos.

7. **Capacitación continua**  
   - Realizar sesiones trimestrales para el personal que registra gastos, enfocándose en la correcta captura de datos y la importancia de la documentación.

## 5. Próximos pasos

| Acción | Responsable | Plazo |
|--------|-------------|-------|
| Configurar reglas de validación y detección de duplicados en el sistema de gestión de gastos | Equipo de TI / Finanzas | 15 días |
| Actualizar la lista de proveedores aprobados y sus tarifas | Área de Compras | 10 días |
| Implementar flujo de aprobación escalonado | Finanzas | 20 días |
| Programar capacitación sobre documentación de gastos | RR.HH. | 30 días |
| Realizar auditoría de seguimiento en junio 2026 | Auditor interno | 1 mes después de la implementación |

---  

*Este informe sintetiza la información disponible en los archivos CSV de enero a mayo 2026 y propone medidas concretas para fortalecer el control interno de los gastos.*
