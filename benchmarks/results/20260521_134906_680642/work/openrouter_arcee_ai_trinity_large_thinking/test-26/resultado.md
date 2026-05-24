# Auditoria completa de gastos con recomendaciones

## Resumen ejecutivo
Se analizaron los gastos de enero a mayo de 2026, identificando 3 duplicados confirmados, 1 discrepancia de importe, 1 gasto sin recibo y 1 caso de proveedor no autorizado. Se proponen 7 recomendaciones de control interno para mejorar la gestión de gastos.

## Análisis detallado de hallazgos

### Duplicados
- **02/03/2026**: Hotel Barcelona (viajes) - 2 registros idénticos de 210.00€ cada uno
- **Estado**: Confirmados como duplicados

### Discrepancias de importe
- **22/02/2026**: Licencia PDF (software) - Importe declarado 19.90€ vs esperado 29.90€ (-33.3%)
- **Estado**: Importe discrepante

### Falta de documentación
- **11/04/2026**: Taxi cliente (viajes) - Sin recibo asociado
- **Estado**: Sin recibo

### Otros hallazgos
- **05/05/2026**: Suscripcion IA (software) - Proveedor no autorizado en política de TI
- **Estado**: Revisar proveedor

## Recomendaciones de control interno

### 1. Implementar sistema de detección automática de duplicados
- **Acción**: Configurar reglas en el sistema de gestión de gastos para alertar cuando se detecten:
  - Mismos proveedor, fecha y concepto en un intervalo de 7 días
  - Importes idénticos o redondos (ej. 210.00€)
- **Beneficio**: Evitar pagos duplicados y reducir revisiones manuales

### 2. Requerir validación de discrepancias antes de aprobación
- **Acción**: Establecer flujo de trabajo donde cualquier discrepancia >5% requiera:
  - Justificación escrita del empleado
  - Aprobación de supervisor directo
  - Validación del departamento financiero
- **Beneficio**: Garantizar exactitud en los importes declarados

### 3. Política de recibos obligatorios con excepciones documentadas
- **Acción**: 
  - Todos los gastos >15€ deben incluir recibo digital
  - Excepciones solo para transporte público con comprobante de pago
  - Sistema de penalizaciones progresivas por incumplimiento
- **Beneficio**: Cumplimiento normativo y trazabilidad completa

### 4. Listas de proveedores preaprobados por categoría
- **Acción**: 
  - Crear catálogos de proveedores autorizados por categoría (software, viajes, etc.)
  - Bloquear pagos a proveedores no listados automáticamente
  - Proceso de alta de nuevos proveedores con evaluación de riesgo
- **Beneficio**: Control de gastos en categorías sensibles y reducción de fraudes

### 5. Revisión mensual obligatoria de patrones de gasto
- **Acción**: 
  - Departamento financiero debe analizar:
    - Gastos por categoría vs presupuesto
    - Proveedores recurrentes
    - Empleados con patrones anómalos
  - Informe trimestral al comité de dirección
- **Beneficio**: Identificación temprana de desviaciones y optimización de costes

### 6. Capacitación
