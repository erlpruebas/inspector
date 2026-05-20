Voy a leer ambos archivos y extraer las menciones de personas en las notas para cruzarlas con el CSV de contactos. Después normalizo nombres y devuelvo la tabla pedida con tarea, persona, empresa y email.

Ya vi el formato: las notas usan IDs sintéticos y el CSV tiene `nombre/email/empresa` también sintéticos. Ahora voy a extraer todas las menciones de cada nota y cruzarlas contra los contactos para construir la tabla final sin perder ninguna coincidencia.

Encontré un punto importante: algunas notas usan IDs que no aparecen literalmente en la primera vista del CSV, así que estoy comprobando si esas referencias se resuelven por otras pistas del registro o si debo dejar fuera las que no tienen match directo. Eso evita inventar asociaciones.

Ya tengo suficientes cruces confiables para construir la tabla. Estoy generando el mapeo final con los 10 contactos que sí aparecen de forma clara en las notas y dejando fuera los casos sin correspondencia en el CSV.

Tomé coincidencias directas por `nombre` o `empresa` en `assistant_synthetic/contactos_50.csv`. Estas son las notas que sí pude cruzar:

| Tarea | Persona | Empresa | Email |
|---|---|---|---|
| VN-001: Recordar llamar a Noelia de ORG_0005 antes del jueves para confirmar el modulo de pagos. | PERSON_0001 | ORG_0005 | EMAIL_0025 |
| VN-003: Comprar billete para Barcelona el dia 18 si Xavier confirma la reunion de Barna Health. | PERSON_0024 | Barna Health | EMAIL_0018 |
| VN-004: Preparar minuta para PERSON_0060 con riesgos de seguridad y coste de auditoria. | PERSON_0060 | Innotek | EMAIL_0050 |
| VN-006: Crear tarea para revisar contrato de IberLegal; David pidio respuesta antes del 12. | PERSON_0058 | IberLegal | EMAIL_0048 |
| VN-007: Agendar seguimiento con PERSON_0064 el martes a las cuatro por el tema de administracion. | PERSON_0064 | Clinica Sol | EMAIL_0053 |
| VN-008: No olvidar que PERSON_0069 prefiere recibir informes en PDF y resumen ejecutivo corto. | PERSON_0069 | PERSON_0068 | EMAIL_0055 |
| VN-009: Buscar alternativa barata a herramienta de encuestas para GreenBox. | PERSON_0057 | GreenBox | EMAIL_0047 |
| VN-011: Enviar agenda de implantacion a PERSON_0033; incluir hito de formacion el dia 22. | PERSON_0033 | Northwind ES | EMAIL_0027 |
| VN-013: Poner recordatorio para renovar certificado SSL de Cobalto antes del 28. | PERSON_0037 | Cobalto | EMAIL_0030 |
| VN-015: Enviar email amable a PERSON_0059, no ha contestado la propuesta de BravoSoft. | PERSON_0059 | BravoSoft | EMAIL_0049 |

No pude cruzar con el CSV las notas `VN-002`, `VN-005`, `VN-010`, `VN-016` y `VN-019` porque no hay una coincidencia directa en los contactos proporcionados.
