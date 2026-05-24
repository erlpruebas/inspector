# Auditoría completa de gastos: enero a mayo 2026

## Resumen ejecutivo

Se revisaron 15 gastos registrados entre enero y mayo de 2026.  
Resultado general: el control es aceptable, pero hay incidencias que requieren acción.

### Hallazgos principales
- **1 gasto con importe discrepante**: febrero, licencia PDF.
- **1 gasto duplicado probable**: marzo, hotel Barcelona aparece dos veces con los mismos datos.
- **1 gasto sin recibo**: abril, taxi cliente.
- **1 gasto para revisión de proveedor**: mayo, suscripción IA.

## Resumen por mes

| Mes | Gastos | Estado general | Incidencias |
|---|---:|---|---|
| Enero | 3 | Correcto | Ninguna |
| Febrero | 3 | Con observación | 1 discrepancia de importe |
| Marzo | 3 | Incidencia crítica | 1 duplicado probable |
| Abril | 3 | Con observación | 1 gasto sin recibo |
| Mayo | 3 | Con observación | 1 proveedor a revisar |

## Detalle de incidencias

### 1) Importe discrepante
**Fecha:** 2026-02-22  
**Concepto:** Licencia PDF  
**Categoría:** software  
**Importe declarado:** 19.9  
**Importe esperado:** 29.9  
**Diferencia:** -10.0

**Observación:**  
Existe una diferencia relevante entre el importe declarado y el esperado. Esto puede deberse a error de captura, descuento no documentado o factura incompleta.

**Acción recomendada:**  
- Validar la factura o justificante original.
- Confirmar si hubo descuento, promo o ajuste.
- Corregir el registro contable si procede.

---

### 2) Posible duplicado
**Fecha:** 2026-03-04  
**Concepto:** Hotel Barcelona  
**Categoría:** viajes  
**Importe declarado:** 210.0  
**Importe esperado:** 210.0  
**Estado:** posible_duplicado

**Observación:**  
El mismo gasto aparece dos veces con idénticos datos, lo que sugiere duplicidad de registro o doble carga.

**Acción recomendada:**  
- Revisar si se trata de una sola estancia o de dos cargos distintos.
- Verificar número de factura, reserva o justificante.
- Eliminar uno de los registros si se confirma duplicidad.

---

### 3) Gasto sin recibo
**Fecha:** 2026-04-11  
**Concepto:** Taxi cliente  
**Categoría:** viajes  
**Importe declarado:** 28.3  
**Importe esperado:** 28.3  
**Estado:** sin_recibo

**Observación:**  
El gasto es consistente en importe, pero falta respaldo documental.

**Acción recomendada:**  
- Solicitar recibo al empleado.
- Establecer plazo máximo de entrega.
- Si no se consigue, aplicar política de no reembolso o aprobación excepcional.

---

### 4) Revisión de proveedor
**Fecha:** 2026-05-03  
**Concepto:** Suscripcion IA  
**Categoría:** software  
**Importe declarado:** 120.0  
**Importe esperado:** 120.0  
**Estado:** revisar_proveedor

**Observación:**  
No hay discrepancia de importe, pero el proveedor requiere revisión. Puede tratarse de cambio de condiciones, renovación no autorizada o proveedor no homologado.

**Acción recomendada:**  
- Revisar contrato, vigencia y centro de coste.
- Confirmar autorización previa para la suscripción.
- Verificar si el proveedor está aprobado por compras o IT.

## Resumen cuantitativo

### Totales por mes
- **Enero:** 267.5
- **Febrero:** 178.1
- **Marzo:** 554.7
- **Abril:** 116.69
- **Mayo:** 293.4

### Total acumulado enero-mayo
**1410.39**

### Total de incidencias por tipo
- Discrepancia de importe: **1**
- Posible duplicado: **1**
- Sin recibo: **1**
- Revisar proveedor: **1**

## Recomendaciones de control interno

### 1) Evitar duplicados
- Bloquear cargas repetidas por combinación de **fecha + concepto + importe + proveedor**.
- Usar un identificador único de justificante o factura.
- Aplicar revisión automática de similitud para detectar registros repetidos.
- Hacer conciliación semanal de gastos cargados contra tarjetas, facturas y reservas.

### 2) Reducir recibos faltantes
- Exigir recibo obligatorio para todos los gastos salvo excepciones justificadas.
- Configurar alertas automáticas para
