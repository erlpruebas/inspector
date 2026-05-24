# Auditoría de Gastos - Enero a Mayo 2026
## Informe de Control Interno y Recomendaciones

---

## 1. Resumen Ejecutivo

Se analizaron **15 transacciones** entre enero y mayo de 2026, correspondientes a 5 categorías de gasto. El análisis identificó **3 áreas de riesgo** que requieren atención inmediata: duplicidad de registros, discrepancias en importes y falta de documentación soporte.

**Hallazgos clave:**
- **2 transacciones duplicadas** (Hotel Barcelona, 4 marzo)
- **1 discrepancia de importe** (Licencia PDF, febrero)
- **1 gasto sin recibo** (Taxi cliente, abril)
- **1 proveedor bajo revisión** (Suscripción IA, mayo)

---

## 2. Análisis por Mes

### Enero 2026
- **Total gastado:** €267.5
- **Transacciones:** 3 (todas OK)
- **Categorías:** Viajes (66.7%), Software (33.3%)

### Febrero 2026
- **Total gastado:** €178.1
- **Transacciones:** 3 (1 discrepancia)
- **Discrepancia:** Licencia PDF - declarado €19.9 vs esperado €29.9 (-33.4%)

### Marzo 2026
- **Total gastado:** €555.0
- **Transacciones:** 3 (2 duplicadas)
- **Duplicidad:** Hotel Barcelona - 2 registros idénticos de €210.0

### Abril 2026
- **Total gastado:** €116.73
- **Transacciones:** 3 (1 sin recibo)
- **Falta documentación:** Taxi cliente - sin recibo asociado

### Mayo 2026
- **Total gastado:** €293.4
- **Transacciones:** 3 (1 proveedor en revisión)
- **Observación:** Suscripción IA - proveedor bajo evaluación

---

## 3. Problemas Detectados y Recomendaciones

### 3.1 Duplicidad de Registros
**Problema:** Dos registros idénticos para el mismo gasto (Hotel Barcelona, 4 marzo).

**Recomendaciones:**
1. **Implementar validación cruzada:** Antes de registrar un gasto, el sistema debe verificar coincidencias en: fecha, concepto, categoría e importe.
2. **Establecer límite de 24 horas:** No permitir registros de conceptos idénticos en un período menor a 24 horas sin aprobación adicional.
3. **Auditoría mensual de duplicados:** Incluir en el cierre mensual una verificación automática de posibles duplicados.

### 3.2 Discrepancias en Importes
**Problema:** Diferencia significativa entre importe declarado y esperado (Licencia PDF, febrero).

**Recomendaciones:**
1. **Validación de presupuestos:** Para compras de software, requerir cotización previa y comparar con importe declarado.
2. **Límite de variación:** Establecer umbrales de variación (ej. ±5%) que requieran justificación adicional.
3. **Comunicación con proveedor:** Contactar al proveedor para aclarar la discrepancia y ajustar registros si es necesario.

### 3.3 Falta de Documentación Soporte
**Problema:** Taxi cliente (abril) registrado como "sin recibo".

**Recomendaciones:**
1. **Política de recibos obligatorios:** Todo gasto superior a €25 debe ir acompañado de recibo digital.
2. **Plazo máximo de 3 días:** Los recibos deben subirse al sistema dentro de los 3 días hábiles posteriores al gasto.
3. **Bloqueo de pagos:** No procesar reembolsos sin documentación completa.

### 3.4 Revisión de Proveedores
**Problema:** Suscripción IA bajo revisión por posible incumplimiento de políticas.

**Recomendaciones:**
1. **Lista de proveedores aprobados:** Mantener un registro actualizado de proveedores autorizados.
2. **Proceso de onboarding:** Todo nuevo proveedor debe ser validado por el departamento de compras.
3. **Revisión trimestral:** Evaluar el desempeño y cumplimiento de todos los proveedores activos.

---

## 4. Indicadores de Control (KPI)

| Indicador | Valor | Meta |
|-----------|-------|------|
| % transacciones con problemas | 26.7% | <5% |
| Gasto afectado por problemas | €420.6 | <1% |
| Tiempo promedio en resolver discrepancias | N/A | <48h |

---

## 5. Plan de Acción Inmediata

1. **Corregir duplicados:** Eliminar uno de los registros del Hotel Barcelona (marzo) - ahorro potencial: €210.0
2. **Resolver discrepancia:** Contactar a Office Depot (licencia PDF) antes del 15 de junio
3. **Obtener recibo faltante:** Solicitar recibo del taxi de abril antes del 10 de junio
4. **Validar proveedor:** Finalizar revisión de suscripción IA antes del 30 de junio

---

## 6. Mejoras al Sistema de Reporte

### 6.1 Automatización
- **Validaciones en tiempo real:** Implementar reglas de negocio en el formulario de registro.
- **Alertas automáticas:** Notificar a auditores
