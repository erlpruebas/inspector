Voy a leer el JSONL local y revisar su estructura antes de extraer las tareas, para no asumir nombres de campos ni formato de fechas.

La estructura es una línea JSON por nota con `id`, `timestamp` y `transcript`. Ahora leo el conjunto completo para identificar solo acciones pendientes y normalizar fechas relativas cuando el texto lo permite.

Extraído de `assistant_synthetic/notas_voz.jsonl`:

| id nota | accion | entidad relacionada | posible fecha limite |
|---|---|---|---|
| VN-001 | Llamar para confirmar demo del modulo de pagos | Noelia, Clinica Centro | 2026-05-07 |
| VN-002 | Enviar CSV actualizado de monitores incluyendo descuento del 4% | Luis, Delta Equipos | No indicada |
| VN-003 | Comprar billete para Barcelona si se confirma la reunion | Xavier, Barna Health | 2026-05-18 |
| VN-004 | Preparar minuta con riesgos de seguridad y coste de auditoria | Sergio Campos | No indicada |
| VN-005 | Pedir facturas de abril que no aparecen en el banco | Elena Vidal | No indicada |
| VN-006 | Revisar contrato y responder | IberLegal, David | 2026-05-12 |
| VN-007 | Agendar seguimiento sobre administracion | Marta Ruiz | 2026-05-12 16:00 |
| VN-008 | Registrar preferencia de informes en PDF con resumen ejecutivo corto | Ana Lopez | No indicada |
| VN-009 | Buscar alternativa barata a herramienta de encuestas | GreenBox | No indicada |
| VN-010 | Llamar por pedido de licencias y confirmar direccion fiscal | Tomas, Zenit Food | No indicada |
| VN-011 | Enviar agenda de implantacion incluyendo hito de formacion | Laura Marin | 2026-05-22 |
| VN-012 | Revisar gastos de marzo por dos cargos duplicados de hotel | Gastos de marzo | No indicada |
| VN-013 | Renovar certificado SSL | Cobalto | 2026-05-28 |
| VN-014 | Preparar comparativa OpenRouter vs Gemini para tareas de ofimatica | OpenRouter, Gemini | No indicada |
| VN-015 | Enviar email de seguimiento sobre propuesta | Paula Ferrer, BravoSoft | No indicada |
| VN-016 | Cruzar pagos con facturas y localizar posible factura faltante de 847,50 | Norte SA | No indicada |
| VN-017 | Crear lista de contactos prioritarios de Madrid con nivel alta | Contactos de Madrid | No indicada |
| VN-018 | Investigar rendimiento de Apple frente a Microsoft en los ultimos seis meses | Apple, Microsoft | No indicada |
| VN-019 | Preparar informe mensual de incidencias incluyendo Clinica Centro y facturacion | Clinica Centro, facturacion | No indicada |
| VN-020 | Reservar sala para reunion interna | Reunion interna | 2026-05-15 09:30 |

Fechas relativas interpretadas usando el `timestamp` de cada nota.
