# Auditoría Completa de Gastos (Enero–Mayo 2026) y Recomendaciones de Control Interno

## Resumen Ejecutivo

Se realizó una auditoría de los gastos declarados entre enero y mayo de 2026, analizando cinco archivos mensuales. El análisis identificó **duplicados, discrepancias en importes, gastos sin recibo y observaciones que requieren revisión**. El importe total declarado en el período fue de **€1,309.39**. Se proponen controles para mitigar los riesgos detectados.

## Hallazgos Detallados

### 1. Duplicados Detectados
- **Marzo 2026**: El gasto "Hotel Barcelona" por €210.00 aparece dos veces en la misma fecha (2026-03-04). Estado marcado como `posible_duplicado`. **Importe duplicado: €210.00**.

### 2. Discrepancias en Importes
- **Febrero 2026**: Gasto "Licencia PDF". Importe declarado: €19.90. Importe esperado: €29.90. Diferencia: **-€10.00**. Estado: `importe_discrepante`.

### 3. Gastos sin Recibo
- **Abril 2026**: Gasto "Taxi cliente" por €28.30 marcado como `sin_recibo`.

### 4. Observaciones para Revisión
- **Mayo 2026**: Gasto "Suscripcion IA" por €120.00 marcado como `revisar_proveedor`. Se requiere validación del proveedor y del contrato.

### 5. Resumen de Estados
- **OK**: 10 registros.
- **Posible Duplicado**: 2 registros (el mismo gasto duplicado).
- **Importe Discrepante**: 1 registro.
- **Sin Recibo**: 1 registro.
- **Revisar Proveedor**: 1 registro.

### 6. Análisis por Categoría (Importe Total Declarado)
- **Software**: €203.89 (Licencias, suscripciones, dominio).
- **Viajes**: €673.80 (Hoteles, transportes).
- **Comidas**: €249.30.
- **Oficina**: €73.40.

## Recomendaciones de Control Interno

### A. Para Evitar Duplicados
1.  **Implementar un Registro Único Centralizado**: Utilizar un sistema (ERP o software de gastos) con un identificador único (ID) para cada gasto, generado automáticamente al momento de la declaración.
2.  **Validación Automática de Duplicados**: Configurar el sistema para que alerte al intentar registrar un gasto con el mismo concepto, importe, fecha y empleado en un período corto (ej., 7 días).
3.  **Conciliación Mensual Automatizada**: Establecer un proceso donde el sistema genere un reporte de posibles duplicados para su revisión antes del cierre contable.

### B. Para Garantizar la Integridad de los Recibos
1.  **Política de "Sin Recibo, Sin Reembolso"**: Formalizar y comunicar que todo gasto requiere un comprobante fiscal digital o físico válido. El estado `sin_recibo` debe bloquear el pago.
2.  **Digitalización Obligatoria**: Implementar una herramienta que
