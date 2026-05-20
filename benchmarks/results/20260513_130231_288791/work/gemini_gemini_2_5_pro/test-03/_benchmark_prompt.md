# Extraer tareas de notas de voz

Lee `benchmarks/assets/assistant_synthetic/notas_voz.jsonl` y extrae las tareas pendientes en una tabla con id de nota, accion, entidad relacionada y posible fecha limite.

Archivos locales preparados en el directorio de trabajo:
- `assistant_synthetic/notas_voz.jsonl`

Usa esas rutas relativas cuando necesites leer datos locales.

Archivo de salida esperado: resultado.md.
Devuelve el contenido final o crea ese archivo en el directorio de trabajo.

Archivos disponibles en el directorio de trabajo:

### assistant_synthetic\notas_voz.jsonl
```text
{"id": "VN-001", "timestamp": "2026-05-03 08:12", "transcript": "Recordar llamar a Noelia de Clinica Centro antes del jueves para confirmar demo del modulo de pagos."}
{"id": "VN-002", "timestamp": "2026-05-03 09:40", "transcript": "Enviar a Luis de Delta Equipos el CSV actualizado de monitores; falta incluir descuento del 4 por ciento."}
{"id": "VN-003", "timestamp": "2026-05-03 11:18", "transcript": "Comprar billete para Barcelona el dia 18 si Xavier confirma la reunion de Barna Health."}
{"id": "VN-004", "timestamp": "2026-05-04 07:55", "transcript": "Preparar minuta para Sergio Campos con riesgos de seguridad y coste de auditoria."}
{"id": "VN-005", "timestamp": "2026-05-04 12:03", "transcript": "Pedir a Elena Vidal las facturas de abril que no aparecen en el banco."}
{"id": "VN-006", "timestamp": "2026-05-05 10:34", "transcript": "Crear tarea para revisar contrato de IberLegal; David pidio respuesta antes del 12."}
{"id": "VN-007", "timestamp": "2026-05-05 17:10", "transcript": "Agendar seguimiento con Marta Ruiz el martes a las cuatro por el tema de administracion."}
{"id": "VN-008", "timestamp": "2026-05-06 08:05", "transcript": "No olvidar que Ana Lopez prefiere recibir informes en PDF y resumen ejecutivo corto."}
{"id": "VN-009", "timestamp": "2026-05-06 14:29", "transcript": "Buscar alternativa barata a herramienta de encuestas para GreenBox."}
{"id": "VN-010", "timestamp": "2026-05-07 09:00", "transcript": "Llamar a Tomas de Zenit Food por pedido de licencias y confirmar direccion fiscal."}
{"id": "VN-011", "timestamp": "2026-05-07 15:12", "transcript": "Enviar agenda de implantacion a Laura Marin; incluir hito de formacion el dia 22."}
{"id": "VN-012", "timestamp": "2026-05-08 08:43", "transcript": "Revisar gastos de marzo porque hay dos cargos duplicados de hotel."}
{"id": "VN-013", "timestamp": "2026-05-08 13:20", "transcript": "Poner recordatorio para renovar certificado SSL de Cobalto antes del 28."}
{"id": "VN-014", "timestamp": "2026-05-09 10:02", "transcript": "Preparar comparativa OpenRouter contra Gemini para tareas de ofimatica."}
{"id": "VN-015", "timestamp": "2026-05-09 16:44", "transcript": "Enviar email amable a Paula Ferrer, no ha contestado la propuesta de BravoSoft."}
{"id": "VN-016", "timestamp": "2026-05-10 09:16", "transcript": "Cruzar pagos de Norte SA con facturas, creo que falta una de 847 con cincuenta."}
{"id": "VN-017", "timestamp": "2026-05-10 11:52", "transcript": "Crear lista de contactos prioritarios de Madrid con nivel alta."}
{"id": "VN-018", "timestamp": "2026-05-10 19:30", "transcript": "Investigar si Apple ha subido mas que Microsoft en los ultimos seis meses."}
{"id": "VN-019", "timestamp": "2026-05-11 08:25", "transcript": "Preparar informe mensual de incidencias: incluir Clinica Centro y facturacion."}
{"id": "VN-020", "timestamp": "2026-05-11 10:00", "transcript": "Recordar reservar sala para reunion interna del viernes a las nueve y media."}

```