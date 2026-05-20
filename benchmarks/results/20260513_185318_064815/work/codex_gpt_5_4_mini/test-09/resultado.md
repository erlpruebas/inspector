Voy a revisar el CSV de marzo, identificar patrones de cargos repetidos y cuantificar el importe afectado. Después te doy una recomendación operativa clara sobre qué hacer con cada grupo de posibles duplicados.

Usaré la skill de hojas de cálculo para hacer el análisis con criterio de datos, no solo una búsqueda textual. Primero voy a inspeccionar la estructura del CSV y luego agruparé por fecha, importe y comercio para encontrar duplicados plausibles.

Ya tengo la guía de análisis. Ahora voy a revisar la estructura real del CSV para decidir qué define un duplicado en este extracto: misma fecha e importe, comercio repetido, o el mismo cargo con pequeños cambios de texto.

El archivo es muy pequeño, así que puedo dar una conclusión precisa. Estoy calculando el efecto económico como la diferencia entre el total cargado y el total esperado dentro del grupo duplicado, y luego te lo resumo con la evidencia mínima necesaria.

Encontré una matización importante: el CSV marca `importe_esperado = importe_declarado`, así que el campo “esperado” no detecta el exceso por sí solo. El impacto económico del duplicado sale de contar una sola vez el cargo repetido y tratar la segunda aparición como importe duplicado.

He detectado 1 cargo duplicado en `assistant_synthetic/gastos_2026_03.csv`.

| Fecha | Concepto | Categoría | Filas | Importe unitario | Importe duplicado |
|---|---|---:|---:|---:|---:|
| 2026-03-04 | Hotel Barcelona | viajes | 2 y 3 | 210,00 € | 210,00 € |

**Impacto económico**
- Importe legítimo: 210,00 €
- Importe registrado por duplicado: 420,00 €
- **Sobrecoste por duplicado: 210,00 €**

**Acción recomendada**
- Marcar una de las dos líneas como duplicada y conservar solo una.
- Si el cargo ya pasó a banco/tarjeta, solicitar reverso o reembolso por 210,00 €.
- Revisar el origen del alta para evitar reimportación o doble carga del mismo gasto.

No he encontrado otros duplicados en este archivo.
