# Auditoría Completa de Gastos (Enero - Mayo 2026)

## 1. Resumen Ejecutivo
- **Período auditado**: Enero a Mayo de 2026
- **Total de registros procesados**: 15
- **Registros conformes**: 10
- **Incidencias detectadas**: 5
- **Importe total declarado**: 1.410,39 €
- **Importe total esperado**: 1.420,39 €
- **Desviación neta**: -10,00 € (originada por discrepancia en febrero)

## 2. Detalle de Hallazgos

### 🔴 Discrepancias de Importe
| Mes | Concepto | Importe Declarado | Importe Esperado | Diferencia |
|---|---|---|---|---|
| Febrero | Licencia PDF | 19,90 € | 29,90 € | -10,00 € |

### 🟡 Posibles Duplicados
| Mes | Concepto | Fecha | Importe | Estado |
|---|---|---|---|---|
| Marzo | Hotel Barcelona | 2026-03-04 | 210,00 € | Registrado 2 veces |

### 🟠 Documentación Faltante
| Mes | Concepto | Categoría | Estado |
|---|---|---|---|
| Abril | Taxi cliente | Viajes | Sin recibo |

### 🔵 Revisión de Proveedor
| Mes | Concepto | Categoría | Estado |
|---|---|---|---|
| Mayo | Suscripción IA | Software | Revisar proveedor |

## 3. Recomendaciones de Control Interno

### 3.1. Prevención de Duplicados
- **Validación automática en entrada**: Implementar reglas de negocio que bloqueen o marquen como alerta cualquier registro con la misma `fecha`, `concepto` e `importe` en un plazo de 24-48 horas.
- **Identificadores únicos**: Asignar un ID de transacción o número de factura obligatorio para cada gasto. Cruzar este ID contra el histórico antes de aprobar.
- **Revisión mensual**: El departamento de contabilidad debe ejecutar un script de detección de duplicados antes del cierre mensual.

### 3.2. Gestión de Recibos y Documentación
- **Política de "Sin comprobante, no hay reembolso"**: Establecer como requisito indispensable la carga digital del ticket/factura en el momento de la declaración.
- **Excepciones controladas**: Para gastos menores o de transporte urgente (ej. taxis), permitir una declaración jurada firmada por el responsable directo, con un límite máximo mensual por empleado.
- **Digitalización obligatoria**: Integrar OCR en la plataforma de gastos para validar automáticamente que el recibo adjunto coincide con el importe y la fecha declarados.

### 3.3. Conciliación y Discrepancias de Importe
- **Validación contra contratos/facturas**: Vincular el campo `importe_esperado` a la orden de compra o contrato vigente. Cualquier desviación > 0% debe requerir justificación documental.
- **Tolerancia configurable**: Definir umbrales de tolerancia (ej. ±1 € por redondeo) para evitar falsos positivos, pero bloquear automáticamente diferencias superiores.
- **Auditoría de licencias**: Revisar trimestralmente los cargos recurrentes de software para asegurar que coinciden con las tarifas vigentes y los usuarios activos.

### 3.4. Gobernanza de Proveedores y Suscripciones
- **Catálogo de proveedores autorizados**: Centralizar la lista de vendors aprobados. Cualquier gasto a un proveedor nuevo debe pasar por una validación de cumplimiento y seguridad.
- **Revisión de renovaciones automáticas**: Implementar un calendario de alertas 30 días antes del vencimiento de suscripciones para evaluar necesidad, coste y alternativas.

## 4. Conclusión
La auditoría revela un control operativo básico con áreas críticas de mejora en la validación de entradas y la documentación soporte. La implementación de las recomendaciones anteriores, junto con la automatización de reglas de validación en el sistema de gestión de gastos, reducirá significativamente el riesgo de fraude, errores contables y pérdidas financieras por duplicados o discrepancias no detectadas.
