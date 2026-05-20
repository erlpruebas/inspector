# Informe de discrepancias de gastos Q1 2026

## Resumen general
| Métrica | Valor |
|---------|-------|
| Total de partidas | 9 |
| Partidas limpias | 6 |
| Partidas con discrepancia | 1 |
| Partidas duplicadas | 2 (representan 1 transacción) |
| Importe total declarado | 1 040.3 € |

## Detalle por mes

| Mes | Partidas totales | Limpias | Discrepancias | Duplicadas |
|-----|------------------|---------|---------------|------------|
| Enero | 3 | 3 | 0 | 0 |
| Febrero | 3 | 2 | 1 | 0 |
| Marzo | 3 | 1 | 0 | 2 |

### Enero 2026
| Fecha | Concepto | Categoría | Importe declarado | Importe esperado | Estado |
|-------|----------|-----------|-------------------|------------------|--------|
| 2026‑01‑08 | Hotel Madrid | viajes | 180.0 € | 180.0 € | ok |
| 2026‑01‑09 | Taxi aeropuerto | viajes | 38.5 € | 38.5 € | ok |
| 2026‑01‑15 | Software encuestas | software | 49.0 € | 49.0 € | ok |

### Febrero 2026
| Fecha | Concepto | Categoría | Importe declarado | Importe esperado | Estado |
|-------|----------|-----------|-------------------|------------------|--------|
| 2026‑02‑03 | Cena cliente | comidas | 96.2 € | 96.2 € | ok |
| 2026‑02‑14 | Tren Valencia | viajes | 62.0 € | 62.0 € | ok |
| 2026‑02‑22 | Licencia PDF | software | 19.9 € | 29.9 € | importe_discrepante |

#### Discrepancia identificada
- **Licencia PDF**: importe declarado 19.9 € vs importe esperado 29.9 € (diferencia 10.0 €).

### Marzo 2026
| Fecha | Concepto | Categoría | Importe declarado | Importe esperado | Estado |
|-------|----------|-----------|-------------------|------------------|--------|
| 2026‑03‑04 | Hotel Barcelona | viajes | 210.0 € | 210.0 € | posible_duplicado |
| 2026‑03‑04 | Hotel Barcelona | viajes | 210.0 € | 210.0 € | posible_duplicado |
| 2026‑03‑19 | Comida equipo | comidas | 134.7 € | 134.7 € | ok |

#### Duplicado identificado
- **Hotel Barcelona**: dos registros idénticos el 4 de marzo. Se considera una sola transacción de 210.0 €.

## Conclusiones
- No se detectaron discrepancias en enero ni en marzo.
- En febrero se identificó una discrepancia de 10.0 € en la licencia de software.
- En marzo se detectó un duplicado que debe ser consolidado.
- La mayor parte de las partidas (66 %) son limpias y sin anomalías.
