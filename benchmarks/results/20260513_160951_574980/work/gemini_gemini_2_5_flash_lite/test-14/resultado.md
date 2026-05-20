BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Gemini CLI//EN
CALSCALE:GREGORIAN
BEGIN:VTIMEZONE
TZID:Europe/Madrid
BEGIN:STANDARD
DTSTART:19700101T000000
TZOFFSETFROM:-0100
TZOFFSETTO:-0100
TZNAME:CET
END:STANDARD
BEGIN:DAYLIGHT
DTSTART:19700101T000000
TZOFFSETFROM:+0100
TZOFFSETTO:+0200
TZNAME:CEST
END:DAYLIGHT
END:VTIMEZONE
BEGIN:VEVENT
UID:EVENT-CLINICA-DEMO-20260513
DTSTAMP:20260513T160951Z
DTSTART;TZID=Europe/Madrid:20260514T113000
DTEND;TZID=Europe/Madrid:20260514T123000
SUMMARY:Demo Modulo Pagos - Clinica Centro
DESCRIPTION:Demo de pagos y conciliación. Asistirá alguien de administración.
Fuente: emails_hilos.md.
Falta especificar hora exacta de fin si la demo dura más de 1h.
LOCATION:
END:VEVENT
BEGIN:VEVENT
UID:EVENT-BARNA-REUNION-20260513
DTSTAMP:20260513T160951Z
DTSTART;TZID=Europe/Madrid:20260518T100000
DTEND;TZID=Europe/Madrid:20260518T110000
SUMMARY:Reunion Tecnica - Barna Health
DESCRIPTION:Revisión de integración con SSO en Barcelona.
Fuente: emails_hilos.md.
Falta especificar hora exacta de fin.
LOCATION:Barcelona
END:VEVENT
BEGIN:VEVENT
UID:TASK-NOELIA-CALL-20260513
DTSTAMP:20260513T160951Z
DTSTART;TZID=Europe/Madrid:20260513T090000
DTEND;TZID=Europe/Madrid:20260513T091500
SUMMARY:Llamar a Noelia (Clinica Centro) para confirmar demo
DESCRIPTION:Confirmar demo modulo de pagos.
Fuente: notas_voz.jsonl.
Hora de llamada asumida a las 09:00.
Falta especificar hora exacta de fin.
LOCATION:
END:VEVENT
BEGIN:VEVENT
UID:TASK-IBERLEGAL-REVIEW-20260513
DTSTAMP:20260513T160951Z
DTSTART;TZID=Europe/Madrid:20260513T140000
DTEND;TZID=Europe/Madrid:20260513T150000
SUMMARY:Revisar Contrato IberLegal
DESCRIPTION:Revisar contrato de soporte.
Comentarios necesarios antes del 12 de mayo (fecha límite pasada).
Fuente: emails_hilos.md, notas_voz.jsonl.
Hora de revisión asumida a las 14:00.
Falta especificar hora exacta de fin.
LOCATION:
END:VEVENT
END:VCALENDAR