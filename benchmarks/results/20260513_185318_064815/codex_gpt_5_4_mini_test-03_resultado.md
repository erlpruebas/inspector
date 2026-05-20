Voy a leer el JSONL local y extraer únicamente las notas que contengan una tarea pendiente, con su id, acción, entidad y fecha límite si aparece.

Ya tengo el contenido. Ahora voy a separar las notas que sí parecen acciones pendientes de las que solo contienen contexto o preferencias, y convertir las fechas relativas a una referencia más clara cuando sea posible.

Estoy cerrando la selección: incluiré las notas con verbo de acción claro y dejaré fuera las que solo expresan preferencias o contexto. En las que hay una referencia temporal, la voy a normalizar a fecha concreta cuando el contexto lo permite.

He extraído las tareas pendientes claras de las notas de voz. La única nota que no he incluido es la de preferencias de formato (`VN-008`), porque no es una acción pendiente.

| id de nota | acción | entidad relacionada | posible fecha límite |
|---|---|---|---|
| VN-001 | Llamar para confirmar la demo del módulo de pagos | Noelia, Clínica Centro | 2026-05-07 |
| VN-002 | Enviar el CSV actualizado de monitores con el descuento del 4% | Luis, Delta Equipos | Sin fecha explícita |
| VN-003 | Comprar billete para Barcelona | Xavier, Barna Health | 2026-05-18, si Xavier confirma la reunión |
| VN-004 | Preparar minuta sobre riesgos y coste de auditoría | Sergio Campos | Sin fecha explícita |
| VN-005 | Pedir las facturas de abril | Elena Vidal | Sin fecha explícita |
| VN-006 | Revisar el contrato | IberLegal | 2026-05-12 |
| VN-007 | Agendar seguimiento | Marta Ruiz | Probable 2026-05-12 a las 16:00 |
| VN-009 | Buscar alternativa barata a la herramienta de encuestas | GreenBox | Sin fecha explícita |
| VN-010 | Llamar para confirmar el pedido de licencias y la dirección fiscal | Tomas, Zenit Food | Sin fecha explícita |
| VN-011 | Enviar la agenda de implantación | Laura Marin | 2026-05-22 |
| VN-012 | Revisar gastos de marzo por cargos duplicados | Sin entidad concreta | Sin fecha explícita |
| VN-013 | Renovar el certificado SSL | Cobalto | 2026-05-28 |
| VN-014 | Preparar comparativa | OpenRouter vs Gemini | Sin fecha explícita |
| VN-015 | Enviar un email de seguimiento | Paula Ferrer, BravoSoft | Sin fecha explícita |
| VN-016 | Cruzar pagos con facturas | Norte SA | Sin fecha explícita |
| VN-017 | Crear una lista de contactos prioritarios | Madrid | Sin fecha explícita |
| VN-018 | Investigar una comparación de rendimiento | Apple vs Microsoft | Sin fecha explícita |
| VN-019 | Preparar informe mensual de incidencias | Clínica Centro, facturación | Sin fecha explícita |
| VN-020 | Reservar sala para la reunión interna | Sin entidad concreta | 2026-05-15 a las 09:30 |

Si quieres, puedo devolvértelo también en CSV o JSON.
