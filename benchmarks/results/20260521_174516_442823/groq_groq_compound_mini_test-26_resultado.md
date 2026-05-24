# Auditoría de Gastos Enero‑Mayo 2026  

## 1. Resumen financiero  

| Mes | Importe declarado (EUR) | Importe esperado (EUR) | Comentario |
|-----|------------------------|------------------------|------------|
| Enero | 267,50 | 267,50 | Sin incidencias |
| Febrero | 178,10 | 188,10* | 1 discrepancia de importe |
| Marzo | 554,70 | 554,70 | 1 posible duplicado |
| Abril | 116,69 | 116,69 | 1 falta de recibo |
| Mayo | 293,40 | 293,40 | 1 revisión de proveedor |
| **Total** | **1 410,39** | **1 416,39** | |

\* En febrero, la **Licencia PDF** tiene importe declarado 19,90 € vs. esperado 29,90 € (diferencia +10,00 €).  

## 2. Detalle por mes  

### Enero 2026  
| Fecha | Concepto | Categoría | Importe (€) | Estado |
|-------|----------|-----------|-------------|--------|
| 08‑01 | Hotel Madrid | viajes | 180,00 | ok |
| 09‑01 | Taxi aeropuerto | viajes | 38,50 | ok |
| 15‑01 | Software encuestas | software | 49,00 | ok |

### Febrero 2026  
| Fecha | Concepto | Categoría | Importe (€) | Estado |
|-------|----------|-----------|-------------|--------|
| 03‑02 | Cena cliente | comidas | 96,20 | ok |
| 14‑02 | Tren Valencia | viajes | 62,00 | ok |
| 22‑02 | Licencia PDF | software | 19,90 | **importe_discrepante** (esperado 29,90) |

### Marzo 2026  
| Fecha | Concepto | Categoría | Importe (€) | Estado |
|-------|----------|-----------|-------------|--------|
| 04‑03 | Hotel Barcelona | viajes | 210,00 | **posible_duplicado** |
| 04‑03 | Hotel Barcelona | viajes | 210,00 | **posible_duplicado** |
| 19‑03 | Comida equipo | comidas | 134,70 | ok |

### Abril 2026  
| Fecha | Concepto | Categoría | Importe (€) | Estado |
|-------|----------|-----------|-------------|--------|
| 02‑04 | Dominio anual | software | 14,99 | ok |
| 11‑04 | Taxi cliente | viajes | 28,30 | **sin_recibo** |
| 25‑04 | Material oficina | oficina | 73,40 | ok |

### Mayo 2026  
| Fecha | Concepto | Categoría | Importe (€) | Estado |
|-------|----------|-----------|-------------|--------|
| 01‑05 | Vuelo Barcelona | viajes | 155,00 | ok |
| 03‑05 | Suscripción IA | software | 120,00 | **revisar_proveedor** |
| 05‑05 | Café reunión | comidas | 18,40 | ok |

## 3. Incidencias detectadas  

| Tipo | Mes | Registro(s) afectado(s) | Impacto económico | Observaciones |
|------|-----|--------------------------|-------------------|---------------|
| **Importe discrepante** | Febrero | Licencia PDF | +10,00 € (sub‑declarado) | Verificar factura y ajustar registro. |
| **Posible duplicado** | Marzo | Hotel Barcelona (2 filas) | 210,00 € duplicados | Confirmar si se trata de dos estancias distintas o error de carga. |
| **Falta de recibo** | Abril | Taxi cliente | 28,30 € sin respaldo documental | Solicitar comprobante o anular gasto. |
| **Revisión de proveedor** | Mayo | Suscripción IA | 120,00 € | Validar contrato, condiciones y facturación con el proveedor. |

## 4. Recomendaciones de control interno  

1. **Política de documentación obligatoria**  
   - Exigir recibo o factura escaneada antes de registrar cualquier gasto.  
   - Implementar un workflow de aprobación que bloquee la contabilización sin documento adjunto.

2. **Validación automática de importes**  
   - Incorporar una regla de negocio que compare el importe declarado con el importe esperado (precio de lista, contrato o presupuesto).  
   - Generar alertas cuando la diferencia supere el 5 % del importe esperado.

3. **Detección de duplicados**  
   - Crear un algoritmo de coincidencia que compare fecha, concepto, categoría e importe.  
   - Cuando se detecten coincidencias exactas, requerir confirmación del responsable o marcar para revisión.

4. **Gestión de proveedores**  
   - Mantener un registro actualizado de precios y condiciones contractuales.  
   - Realizar revisiones trimestrales de facturas contra los acuerdos firmados, especialmente para suscripciones y licencias.

5. **Auditorías parciales mensuales**  
   - Designar a un auditor interno para revisar los gastos de cada mes antes del cierre financiero.  
   - Generar un informe de incidencias y asegurar su resolución antes de la consolidación.

6. **Capacitación continua**  
   - Formar a los empleados en la correcta captura de gastos, la importancia del recibo y el procedimiento de revisión.  
   - Difundir ejemplos de errores comunes (duplicados, faltas de recibo, discrepancias de importe).

7. **Herramientas de reporte y seguimiento**  
   - Utilizar un dashboard que muestre en tiempo real el número de incidencias por tipo y su estado de resolución.  
   - Establecer SLA internos (p.ej., 48 h para resolver una falta de recibo).

---

**Conclusión**  
El total declarado de 1 410,39 € está ligeramente por debajo del importe esperado (1 416,39 €) debido a una discrepancia y a un posible registro duplicado. La implementación de los controles propuestos reducirá riesgos de fraude, errores contables y mejorará la calidad de la información financiera.
