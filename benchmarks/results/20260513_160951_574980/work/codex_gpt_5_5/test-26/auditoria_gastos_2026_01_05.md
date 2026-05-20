# Auditoria de gastos enero-mayo 2026

## Alcance

Archivos revisados:

- `assistant_synthetic/gastos_2026_01.csv`
- `assistant_synthetic/gastos_2026_02.csv`
- `assistant_synthetic/gastos_2026_03.csv`
- `assistant_synthetic/gastos_2026_04.csv`
- `assistant_synthetic/gastos_2026_05.csv`

Periodo auditado: enero a mayo de 2026.

## Resumen ejecutivo

- Registros revisados: 15
- Total declarado: 1.410,39 EUR
- Total esperado: 1.420,39 EUR
- Diferencia neta declarada vs. esperada: -10,00 EUR
- Excepciones detectadas: 5 registros afectados por 4 incidencias de control

La auditoria identifica un duplicado potencial por 210,00 EUR, un recibo faltante por 28,30 EUR, una discrepancia de importe por -10,00 EUR y un proveedor que requiere revision por 120,00 EUR. El riesgo economico principal es el posible pago duplicado de `Hotel Barcelona`; la discrepancia monetaria confirmada esta concentrada en `Licencia PDF`.

## Resumen por mes

| Mes | Registros | Total declarado | Total esperado | Diferencia |
|---|---:|---:|---:|---:|
| 2026-01 | 3 | 267,50 EUR | 267,50 EUR | 0,00 EUR |
| 2026-02 | 3 | 178,10 EUR | 188,10 EUR | -10,00 EUR |
| 2026-03 | 3 | 554,70 EUR | 554,70 EUR | 0,00 EUR |
| 2026-04 | 3 | 116,69 EUR | 116,69 EUR | 0,00 EUR |
| 2026-05 | 3 | 293,40 EUR | 293,40 EUR | 0,00 EUR |
| **Total** | **15** | **1.410,39 EUR** | **1.420,39 EUR** | **-10,00 EUR** |

## Resumen por categoria

| Categoria | Registros | Total declarado | Total esperado | Diferencia |
|---|---:|---:|---:|---:|
| comidas | 3 | 249,30 EUR | 249,30 EUR | 0,00 EUR |
| oficina | 1 | 73,40 EUR | 73,40 EUR | 0,00 EUR |
| software | 4 | 203,89 EUR | 213,89 EUR | -10,00 EUR |
| viajes | 7 | 883,80 EUR | 883,80 EUR | 0,00 EUR |

## Hallazgos

### 1. Posible duplicado

| Fecha | Concepto | Categoria | Importe declarado | Archivo |
|---|---|---|---:|---|
| 2026-03-04 | Hotel Barcelona | viajes | 210,00 EUR | `assistant_synthetic/gastos_2026_03.csv` |
| 2026-03-04 | Hotel Barcelona | viajes | 210,00 EUR | `assistant_synthetic/gastos_2026_03.csv` |

El gasto aparece dos veces con la misma fecha, concepto, categoria e importe. Si solo corresponde un gasto real, la exposicion por duplicado es de 210,00 EUR.

Accion recomendada: bloquear el pago/reembolso del segundo registro hasta validar factura, reserva, numero de recibo y autorizacion.

### 2. Recibo faltante

| Fecha | Concepto | Categoria | Importe declarado | Estado | Archivo |
|---|---|---|---:|---|---|
| 2026-04-11 | Taxi cliente | viajes | 28,30 EUR | sin_recibo | `assistant_synthetic/gastos_2026_04.csv` |

El gasto esta declarado sin evidencia documental suficiente.

Accion recomendada: solicitar recibo o justificante alternativo; si no se aporta, reclasificar como excepcion no reembolsable o aprobar solo con autorizacion documentada.

### 3. Discrepancia de importe

| Fecha | Concepto | Categoria | Declarado | Esperado | Diferencia | Archivo |
|---|---|---|---:|---:|---:|---|
| 2026-02-22 | Licencia PDF | software | 19,90 EUR | 29,90 EUR | -10,00 EUR | `assistant_synthetic/gastos_2026_02.csv` |

El importe declarado es 10,00 EUR menor que el esperado. No genera sobrepago, pero indica que la captura, tarifa o registro maestro del proveedor podria estar desalineado.

Accion recomendada: reconciliar contra factura/contrato y actualizar la base de precios esperados o corregir el gasto si el declarado es erroneo.

### 4. Proveedor a revisar

| Fecha | Concepto | Categoria | Importe declarado | Estado | Archivo |
|---|---|---|---:|---|---|
| 2026-05-03 | Suscripcion IA | software | 120,00 EUR | revisar_proveedor | `assistant_synthetic/gastos_2026_05.csv` |

El estado indica necesidad de validacion del proveedor. No hay diferencia de importe, pero falta confirmacion de legitimidad, aprobacion o encaje con politica.

Accion recomendada: verificar proveedor, titularidad de cuenta, contrato/suscripcion activa, aprobador y necesidad de negocio antes de pago recurrente.

## Recomendaciones de control interno

### Controles para evitar duplicados

- Crear una clave unica preventiva por `fecha + proveedor/concepto normalizado + importe + categoria + empleado/proyecto` antes de aprobar el gasto.
- Alertar coincidencias exactas y coincidencias cercanas, por ejemplo mismo proveedor e importe en una ventana de 3 a 7 dias.
- Exigir numero de factura/recibo o identificador de transaccion para gastos de viajes, hoteles, software y suscripciones.
- Bloquear automaticamente registros marcados como `posible_duplicado` hasta revision por una persona distinta del solicitante.

### Controles para recibos faltantes

- Configurar validacion obligatoria de adjunto para todas las categorias, con excepciones solo por politica y con aprobacion documentada.
- Definir umbrales: sin recibo por encima de importes bajos debe quedar en estado pendiente y no pagarse.
- Mantener lista de justificantes alternativos aceptables, como extracto bancario, confirmacion de proveedor o aprobacion de excepcion.
- Medir mensualmente gastos sin recibo por empleado, categoria y aprobador para detectar patrones.

### Controles para discrepancias

- Comparar importe declarado contra importe esperado, contrato, tarifa o presupuesto autorizado antes de contabilizar.
- Establecer tolerancias por categoria: por ejemplo, 0 EUR para software recurrente y una tolerancia baja para taxis/comidas.
- Enviar a revision toda diferencia distinta de cero en suscripciones, licencias y proveedores recurrentes.
- Mantener catalogo actualizado de proveedores, precios esperados, periodicidad y aprobadores responsables.

### Controles de aprobacion y gobierno

- Separar funciones: quien solicita no debe ser quien aprueba excepciones de duplicados, recibos faltantes o proveedores nuevos.
- Crear estados normalizados: `pendiente_recibo`, `pendiente_duplicado`, `pendiente_discrepancia`, `pendiente_proveedor`, `aprobado`, `rechazado`.
- Registrar decision, aprobador, fecha de resolucion y evidencia para cada excepcion.
- Revisar mensualmente un reporte de excepciones abiertas y reincidencias.

## Prioridades de remediacion

1. Validar y resolver el duplicado de `Hotel Barcelona` por 210,00 EUR.
2. Solicitar recibo o aprobacion excepcional para `Taxi cliente` por 28,30 EUR.
3. Reconciliar `Licencia PDF` por diferencia de -10,00 EUR.
4. Revisar proveedor y autorizacion de `Suscripcion IA` por 120,00 EUR.
5. Implantar controles automaticos de clave unica, adjuntos obligatorios y tolerancias de importe antes del siguiente ciclo mensual.
