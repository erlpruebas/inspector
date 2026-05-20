Voy a leer ambos archivos para extraer fechas, horas, asistentes y cualquier dato incompleto antes de componer el ICS.

```ics
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Codex//Compromisos extraidos//ES
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Compromisos extraidos
X-WR-TIMEZONE:Europe/Madrid

BEGIN:VEVENT
UID:demo-pagos-20260514T113000@codex.local
DTSTAMP:20260520T000000Z
DTSTART;TZID=Europe/Madrid:20260514T113000
DTEND;TZID=Europe/Madrid:20260514T123000
SUMMARY:Demo modulo de pagos
DESCRIPTION:Fuente: emails_hilos.md y notas_voz.jsonl. ORG_0006 solicita demo centrada en conciliacion y estado de pagos. Debe asistir alguien de administracion. Falta dato: duracion exacta, ubicacion/enlace y nombre de la persona de administracion.
END:VEVENT

BEGIN:VTODO
UID:oferta-monitores-20260513@codex.local
DTSTAMP:20260520T000000Z
DUE;VALUE=DATE:20260513
SUMMARY:Cerrar oferta de monitores con descuento
DESCRIPTION:Fuente: emails_hilos.md y notas_voz.jsonl. PERSON_0066 indica que si se cierra antes del dia 13 aplica 4% de descuento sobre monitores 27. Enviar a PERSON_0074 el CSV actualizado de monitores incluyendo descuento del 4%. Falta dato: hora limite y destinatario email real.
END:VTODO

BEGIN:VTODO
UID:revision-iberlegal-20260512@codex.local
DTSTAMP:20260520T000000Z
DUE;VALUE=DATE:20260512
SUMMARY:Enviar comentarios del contrato IberLegal
DESCRIPTION:Fuente: emails_hilos.md y notas_voz.jsonl. PERSON_0058 necesita comentarios antes del 12 de mayo. Revisar clausula 8 de responsabilidad y renovacion automatica. David pidio respuesta antes del 12. Falta dato: hora limite y canal de envio.
END:VTODO

BEGIN:VEVENT
UID:barna-health-20260518T100000@codex.local
DTSTAMP:20260520T000000Z
DTSTART;TZID=Europe/Madrid:20260518T100000
DTEND;TZID=Europe/Madrid:20260518T110000
SUMMARY:Reunion tecnica Barna Health en Barcelona
LOCATION:Barcelona
DESCRIPTION:Fuente: emails_hilos.md y notas_voz.jsonl. Reunion presencial confirmada para revisar integracion con SSO. Nota relacionada: comprar billete para Barcelona el dia 18. Falta dato: duracion exacta, direccion concreta y confirmacion de Xavier en la nota de voz.
END:VEVENT

END:VCALENDAR
```
