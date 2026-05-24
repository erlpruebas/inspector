# Auditoría Completa de Gastos (Enero-Mayo 2026)

## Resumen Ejecutivo
Se auditaron **14 registros** distribuidos en los meses de enero a mayo de 2026.  
**Total declarado:** 1.192,29 €  
**Total esperado:** 1.202,29 €  
**Diferencia:** +10,00 € (principalmente por discrepancia en licencia PDF).

### Hallazgos por categoría
| Categoría | Registros | Importe declarado | Observaciones |
|-----------|-----------|-------------------|---------------|
| viajes    | 6         | 673,80 €          | 1 posible duplicado, 1 sin recibo |
| software  | 4         | 203,89 €          | 1 discrepancia de importe, 1 revisar proveedor |
| comidas   | 3         | 249,30 €          | Sin incidencias relevantes |
| oficina   | 1         | 73,40 €           | Sin incidencias |

## Incidencias Detectadas

### 1. Duplicados
- **2026-03-04** – Hotel Barcelona (viajes) – 210,00 € (dos registros idénticos con estado `posible_duplicado`).

### 2. Discrepancias de importe
- **2026-02-22** – Licencia PDF (software) – Declarado 19,90 € vs Esperado 29,90 € (diferencia +10,00 €).

### 3. Recibos faltantes
- **2026-04-11** – Taxi cliente (viajes) – 28,30 € (estado `sin_recibo`).

### 4. Otros
- **2026-05-03** – Suscripción IA (software) – 120,00 € (estado `revisar_proveedor`).

## Recomendaciones de Control Interno

1. **Prevención de duplicados**
   - Implementar validación automática por combinación de fecha + concepto + importe antes de registrar el gasto.
   - Exigir aprobación de un segundo responsable cuando se detecte posible duplicado.

2. **Control de recibos**
   - Establecer política de “sin recibo = no reembolsable” salvo autorización expresa del director financiero.
   - Digitalizar y adjuntar justificantes en el sistema en un plazo máximo de 48 horas.

3. **Conciliación de importes**
   - Configurar alertas automáticas cuando `importe_declarado ≠ importe_esperado`.
   - Revisar mensualmente los contratos con proveedores de software para evitar discrepancias de precio.

4. **Revisión de proveedores**
   - Crear un catálogo de proveedores aprobados. Cualquier gasto a un proveedor no catalogado debe pasar por revisión previa.

5. **Seguimiento y reporting**
   - Generar informe mensual de incidencias con clasificación por riesgo (alto/medio/bajo).
   - Realizar auditoría trimestral de gastos por muestreo aleatorio (mínimo 20 % de los registros).

## Conclusión
El sistema de gastos presenta controles débiles en la detección de duplicados y en la obligatoriedad de adjuntar justificantes. La implantación de las recomendaciones anteriores reduciría significativamente el riesgo de fraude y errores administrativos.
