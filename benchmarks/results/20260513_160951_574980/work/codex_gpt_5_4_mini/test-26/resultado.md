Voy a revisar los CSV de enero a mayo, calcular duplicados, faltantes de recibos y discrepancias, y luego te devuelvo una auditoría con recomendaciones de control interno.

Estoy localizando la guía de trabajo del skill de hojas de cálculo y, en paralelo, reviso qué columnas traen los CSV para definir las pruebas de duplicados y conciliación.

Estoy extrayendo la estructura de cada CSV para identificar campos de fecha, importe, proveedor y estado del recibo antes de calcular las anomalías.

Ya confirmé el esquema: `fecha`, `concepto`, `categoria`, `importe_declarado`, `importe_esperado` y `estado`. Ahora estoy calculando la conciliación total y marcando duplicados por combinación de fecha-concepto-importe.

Ya tengo los casos anómalos. Sigo con el desglose financiero por mes y categoría para cuantificar el impacto y dejar el informe listo para revisión.

He encontrado que no hay `node_modules` en el workspace, así que estoy comprobando si la dependencia de artefactos está disponible en la caché de Codex para poder empaquetar el informe en XLSX.

La ruta de artefactos no está disponible, así que verifico si puedo generar el XLSX con la librería de hojas ya instalada en Python. Si no, dejo el análisis en texto con el detalle completo.

**Resumen ejecutivo**
- Revisé los 5 CSV de enero a mayo y encontré 15 gastos en total.
- Total declarado: `1.410,39`; total esperado: `1.420,39`; diferencia neta: `-10,00`.
- Detecté 4 incidentes de control que afectan a 5 filas:
  - 1 discrepancia de importe
  - 1 duplicado exacto de 2 filas
  - 1 gasto sin recibo
  - 1 gasto con revisión de proveedor

**Hallazgos**
| Fecha | Concepto | Hallazgo | Impacto |
|---|---|---:|---:|
| 2026-02-22 | Licencia PDF | Importe declarado `19,90` vs esperado `29,90` | Diferencia de `10,00` |
| 2026-03-04 | Hotel Barcelona | Duplicado exacto en dos líneas idénticas | Riesgo de duplicar `210,00` |
| 2026-04-11 | Taxi cliente | Sin recibo | Riesgo de incumplimiento documental |
| 2026-05-03 | Suscripcion IA | Revisar proveedor | Riesgo de validación/alta de proveedor |

**Lectura por mes**
- Enero: 3 gastos, sin incidencias.
- Febrero: 3 gastos, 1 discrepancia.
- Marzo: 3 gastos, 1 duplicado exacto.
- Abril: 3 gastos, 1 sin recibo.
- Mayo: 3 gastos, 1 caso de revisión de proveedor.

**Lectura por categoría**
- `viajes`: `883,80` declarados y `883,80` esperados.
- `comidas`: `249,30` declarados y `249,30` esperados.
- `oficina`: `73,40` declarados y `73,40` esperados.
- `software`: `203,89` declarados y `213,89` esperados; aquí está la discrepancia neta de `10,00`.

**Recomendaciones de control interno**
- Duplicados:
  - Bloquear envíos idénticos con una regla de unicidad por `fecha + concepto + importe + categoría + proveedor`.
  - Exigir un ID único de gasto y rechazar reenvíos exactos.
  - Revisar semanalmente una cola de excepciones de duplicado antes de aprobar reembolsos.
- Recibos faltantes:
  - Hacer obligatoria la carga del recibo antes de registrar el gasto como aprobable.
  - Marcar como pendiente cualquier gasto sin justificante y escalarlo si no se completa en un plazo corto.
  - Medir un KPI de `% gastos sin recibo` por empleado y por mes.
- Discrepancias de importe:
  - Conciliar automáticamente `importe_declarado` contra `importe_esperado` al cargar el gasto.
  - Bloquear o requerir justificación cuando la diferencia supere un umbral fijo.
  - Mantener una tabla de tarifas o precios esperados para proveedores recurrentes.
- Revisión de proveedores:
  - Validar altas o cambios de proveedor con un flujo de aprobación.
  - Revisar suscripciones y renovaciones para detectar cambios de precio no autorizados.
- Monitoreo:
  - Crear un panel mensual con 4 métricas: duplicados, recibos faltantes, discrepancias y gastos en revisión.
  - Revisar excepciones por tipo de gasto para identificar patrones repetitivos.

Si quieres, puedo convertir esta auditoría en una plantilla de control mensual con columnas de validación y alertas.
