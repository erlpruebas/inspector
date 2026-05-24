# Auditoria de gastos enero-mayo 2026

## Alcance

Se revisaron 15 registros de gastos declarados entre enero y mayo de 2026, a partir de:

- `assistant_synthetic/gastos_2026_01.csv`
- `assistant_synthetic/gastos_2026_02.csv`
- `assistant_synthetic/gastos_2026_03.csv`
- `assistant_synthetic/gastos_2026_04.csv`
- `assistant_synthetic/gastos_2026_05.csv`

## Resumen ejecutivo

| Indicador | Resultado |
| --- | ---: |
| Registros revisados | 15 |
| Total declarado | 1.410,39 |
| Total esperado | 1.420,39 |
| Diferencia neta | -10,00 |
| Registros sin excepcion | 10 |
| Registros con excepcion | 5 |

La auditoria identifica tres riesgos principales: duplicidad de gastos de viaje, ausencia de soporte documental y discrepancias entre importes declarados y esperados. El impacto financiero directo confirmado es una diferencia neta de -10,00 por importe declarado inferior al esperado en una licencia de software. Adicionalmente, existe un posible sobrepago o doble contabilizacion de 210,00 por el duplicado de Hotel Barcelona, sujeto a confirmacion.

## Hallazgos

| Fecha | Concepto | Categoria | Declarado | Esperado | Diferencia | Estado | Riesgo |
| --- | --- | --- | ---: | ---: | ---: | --- | --- |
| 2026-02-22 | Licencia PDF | software | 19,90 | 29,90 | -10,00 | importe_discrepante | Error de captura, factura parcial o referencia incorrecta |
| 2026-03-04 | Hotel Barcelona | viajes | 210,00 | 210,00 | 0,00 | posible_duplicado | Doble registro del mismo gasto |
| 2026-03-04 | Hotel Barcelona | viajes | 210,00 | 210,00 | 0,00 | posible_duplicado | Doble registro del mismo gasto |
| 2026-04-11 | Taxi cliente | viajes | 28,30 | 28,30 | 0,00 | sin_recibo | Falta de evidencia documental |
| 2026-05-03 | Suscripcion IA | software | 120,00 | 120,00 | 0,00 | revisar_proveedor | Proveedor pendiente de validacion |

## Analisis por mes

| Mes | Registros | Total declarado | Total esperado | Excepciones |
| --- | ---: | ---: | ---: | ---: |
| 2026-01 | 3 | 267,50 | 267,50 | 0 |
| 2026-02 | 3 | 178,10 | 188,10 | 1 |
| 2026-03 | 3 | 554,70 | 554,70 | 2 |
| 2026-04 | 3 | 116,69 | 116,69 | 1 |
| 2026-05 | 3 | 293,40 | 293,40 | 1 |

## Analisis por categoria

| Categoria | Registros | Total declarado | Excepciones |
| --- | ---: | ---: | ---: |
| viajes | 7 | 883,80 | 3 |
| software | 4 | 203,89 | 2 |
| comidas | 3 | 249,30 | 0 |
| oficina | 1 | 73,40 | 0 |

La categoria viajes concentra el mayor importe declarado y la mayor cantidad de excepciones. Software presenta menos volumen, pero dos incidencias relevantes: una discrepancia de importe y un proveedor pendiente de revision.

## Duplicados

Se encontro una clave duplicada exacta por fecha, concepto e importe:

| Clave | Ocurrencias | Total registrado | Importe potencialmente duplicado |
| --- | ---: | ---: | ---: |
| 2026-03-04, Hotel Barcelona, 210,00 | 2 | 420,00 | 210,00 |

Accion recomendada: bloquear el pago o reembolso de una de las dos lineas hasta validar si corresponden a noches, reservas o empleados distintos. Con los datos disponibles, ambos registros son indistinguibles.

## Recibos faltantes

| Fecha | Concepto | Importe |
| --- | --- | ---: |
| 2026-04-11 | Taxi cliente | 28,30 |

Accion recomendada: solicitar recibo antes de aprobar el gasto. Si no se obtiene, aplicar la politica de excepcion documentada con aprobacion del responsable.

## Discrepancias de importe

| Fecha | Concepto | Declarado | Esperado | Diferencia |
| --- | --- | ---: | ---: | ---: |
| 2026-02-22 | Licencia PDF | 19,90 | 29,90 | -10,00 |

Accion recomendada: conciliar contra factura, extracto bancario y orden de compra. Si el importe esperado es correcto, ajustar el registro a 29,90; si el declarado es correcto, actualizar el importe esperado y documentar la causa.

## Proveedores a revisar

| Fecha | Concepto | Categoria | Importe |
| --- | --- | --- | ---: |
| 2026-05-03 | Suscripcion IA | software | 120,00 |

Accion recomendada: verificar alta del proveedor, titularidad de la suscripcion, aprobacion previa, periodicidad y necesidad de negocio. Si es recurrente, registrar contrato o aprobacion marco.

## Recomendaciones de control interno

1. Implementar control automatico de duplicados antes de aprobar gastos, usando como clave minima fecha, concepto normalizado, importe, categoria y empleado o centro de coste si esta disponible.
2. Exigir recibo adjunto para todos los gastos, con bloqueo automatico de aprobacion si el campo de soporte documental esta vacio.
3. Separar los estados de excepcion en campos estructurados: `duplicado`, `sin_recibo`, `discrepancia_importe`, `proveedor_no_validado`. Esto permite reportes y reglas de aprobacion mas precisas.
4. Definir umbrales de tolerancia para diferencias de importe. Por ejemplo, diferencias mayores a 1,00 o 1% requieren conciliacion manual.
5. Crear una lista maestra de proveedores aprobados para software y suscripciones. Todo proveedor nuevo debe pasar por validacion fiscal, aprobacion del responsable y revision de recurrencia.
6. Requerir aprobacion reforzada para viajes, ya que concentra 883,80 declarados y 3 de las 5 excepciones.
7. Generar un reporte mensual de excepciones con responsable, fecha limite de resolucion y evidencia de cierre.
8. Conciliar mensualmente gastos declarados contra extractos bancarios, facturas y ordenes de compra.
9. Registrar metadatos adicionales en cada gasto: empleado, aprobador, metodo de pago, numero de factura, proveedor normalizado y hash o identificador del recibo.
10. Mantener una bitacora de cambios para ajustes posteriores, con usuario, fecha, motivo y aprobacion.

## Prioridades de remediacion

| Prioridad | Accion | Motivo |
| --- | --- | --- |
| Alta | Resolver el duplicado de Hotel Barcelona | Puede representar 210,00 registrados de mas |
| Alta | Solicitar recibo de Taxi cliente | Falta evidencia documental del gasto |
| Media | Conciliar Licencia PDF | Existe diferencia de -10,00 contra importe esperado |
| Media | Validar proveedor Suscripcion IA | Riesgo de proveedor no autorizado o gasto recurrente no controlado |
| Baja | Formalizar reporte mensual de excepciones | Mejora seguimiento y cierre de incidencias |

## Conclusion

El periodo enero-mayo presenta un nivel de excepciones relevante: 5 de 15 registros, equivalente al 33,3% del total revisado. No se observan incidencias en comidas ni oficina. Los principales focos de control deben concentrarse en viajes, software, validacion documental y deteccion preventiva de duplicados.
