import json
import re
from datetime import datetime

notas_voz_content = r"""{"id": "VN-001", "timestamp": "2026-05-03 08:12", "transcript": "Recordar llamar a Noelia de Clinica Centro antes del jueves para confirmar demo del modulo de pagos."}
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
"""

emails_content = r"""# Historial de correos sinteticos

## Hilo E-001: Clinica Centro - demo pagos
De: Noelia Castro <noelia.castro@clinicacentro.es>
Para: equipo@inspector.local
Fecha: 2026-05-06 09:12
Asunto: Demo modulo de pagos

Podemos ver la demo el jueves 14 de mayo a las 11:30? Necesito que venga alguien de administracion.

De: equipo@inspector.local
Para: Noelia Castro <noelia.castro@clinicacentro.es>
Fecha: 2026-05-06 10:04

Confirmo disponibilidad. Prepararemos una demo centrada en conciliacion y estado de pagos.

## Hilo E-002: Delta Equipos - descuento monitores
De: Luis Martin <luis.martin@deltaequipos.es>
Fecha: 2026-05-05 12:40
Asunto: Oferta monitores

Si cerramos antes del dia 13 puedo aplicar un 4% de descuento sobre los monitores 27.

## Hilo E-003: IberLegal - contrato
De: David Navarro <david.navarro@iberlegal.es>
Fecha: 2026-05-04 17:15
Asunto: Revision contrato soporte

Necesito comentarios antes del 12 de mayo. Me preocupan la clausula 8 de responsabilidad y la renovacion automatica.

## Hilo E-004: Barna Health - visita Barcelona
De: Xavier Puig <xavier.puig@barnahealth.es>
Fecha: 2026-05-07 18:22
Asunto: Reunion tecnica

Confirmo reunion presencial en Barcelona el 18 de mayo a las 10:00. Revisaremos integracion con SSO.

## Hilo E-005: Nova Iberia - informe ejecutivo
De: Ana Lopez <ana.lopez@novaiberia.es>
Fecha: 2026-05-08 08:10
Asunto: Formato informes

Por favor, enviadme siempre PDF con una pagina de resumen ejecutivo y anexos separados.

## Hilo E-006: BravoSoft - propuesta pendiente
De: Paula Ferrer <paula.ferrer@bravosoft.es>
Fecha: 2026-05-02 13:35
Asunto: Re: propuesta CRM

Lo reviso con direccion y os digo algo la semana que viene. Si no contesto, insistidme con un correo corto.
"""

today = datetime(2026, 5, 21)

tasks = []

for line in notas_voz_content.strip().splitlines():
    if line:
        data = json.loads(line)
        transcript = data['transcript']
        task = {"source": "nota_voz", "description": transcript, "date": None, "client": None, "priority": 0}

        date_match = re.search(r'(el|dia|antes del|para el) (jueves|martes|\d{1,2}(?: de \w+)?(?: de \d{4})?)', transcript, re.IGNORECASE)

        if date_match:
            date_str = date_match.group(2)
            try:
                if "de" in date_str:
                    task_date = datetime.strptime(date_str + " 2026", "%d de %B %Y")
                    task["date"] = task_date
                else:
                    task_date = datetime.strptime(date_str + " de mayo 2026", "%d de %B %Y")
                    task["date"] = task_date
            except ValueError:
                pass

        client_match = re.search(r'(a|de) (Noelia de Clinica Centro|Luis de Delta Equipos|Xavier de Barna Health|David de IberLegal|Ana Lopez|Paula Ferrer|Tomas de Zenit Food|Laura Marin|Sergio Campos|Elena Vidal|Marta Ruiz|GreenBox|Cobalto|Norte SA)', transcript, re.IGNORECASE)
        if client_match:
            client_name_raw = client_match.group(2)
            if "de " in client_name_raw:
                task["client"] = client_name_raw.split("de ")[-1].strip()
            elif "a " in client_name_raw:
                task["client"] = client_name_raw.split("a ")[-1].strip()
            else:
                task["client"] = client_name_raw.strip()

        tasks.append(task)

email_threads = re.split(r'## Hilo E-\d{3}: ', emails_content)[1:]
for thread_content in email_threads:
    subject_match = re.search(r'Asunto: (.*)', thread_content)
    date_match = re.search(r'Fecha: (\d{4}-\d{2}-\d{2})', thread_content)
    from_match = re.search(r'De: (.*?) <', thread_content)
    to_match = re.search(r'Para: (.*?) <', thread_content)

    subject = subject_match.group(1).strip() if subject_match else "N/A"
    email_date_str = date_match.group(1).strip() if date_match else None
    email_date = datetime.strptime(email_date_str, "%Y-%m-%d") if email_date_str else None
    
    client = "N/A"
    if from_match:
        client_name = from_match.group(1).strip()
        if client_name != "equipo@inspector.local":
            client = client_name
    elif to_match:
        client_name = to_match.group(1).strip()
        if client_name != "equipo@inspector.local":
            client = client_name

    task_description = subject
    task_date_from_body = None
    
    if "Podemos ver la demo el jueves 14 de mayo a las 11:30" in thread_content:
        task_description = "Confirmar demo pagos Clinica Centro el jueves 14 de mayo a las 11:30"
        task_date_from_body = datetime(2026, 5, 14)
        client = "Clinica Centro"
    elif "Si cerramos antes del dia 13 puedo aplicar un 4% de descuento" in thread_content:
        task_description = "Cerrar oferta monitores Delta Equipos antes del dia 13 para aplicar 4% descuento"
        task_date_from_body = datetime(2026, 5, 13)
        client = "Delta Equipos"
    elif "Necesito comentarios antes del 12 de mayo" in thread_content:
        task_description = "Enviar comentarios de contrato IberLegal antes del 12 de mayo"
        task_date_from_body = datetime(2026, 5, 12)
        client = "IberLegal"
    elif "Confirmo reunion presencial en Barcelona el 18 de mayo a las 10:00" in thread_content:
        task_description = "Reunion presencial Barna Health en Barcelona el 18 de mayo a las 10:00"
        task_date_from_body = datetime(2026, 5, 18)
        client = "Barna Health"
    elif "enviadme siempre PDF con una pagina de resumen ejecutivo" in thread_content:
        task_description = "Enviar informes a Nova Iberia en PDF con resumen ejecutivo"
        client = "Nova Iberia"
    elif "Si no contesto, insistidme con un correo corto." in thread_content:
        task_description = "Seguimiento propuesta CRM BravoSoft (insistir si no hay respuesta)"
        client = "BravoSoft"

    task = {"source": "email", "description": task_description, "date": task_date_from_body if task_date_from_body else email_date, "client": client, "priority": 0}
    tasks.append(task)

# Prioritize tasks
# Priority 1: Has a specific date in the future or current week AND a client.
# Priority 2: Has a specific date in the future or current week (but no specific client). 
# Priority 3: Has a specific client (but no specific date).
# Priority 4: General tasks.

priority_tasks_with_client_and_date = []
priority_tasks_with_date_only = []
priority_tasks_with_client_only = []
general_tasks = []

for task in tasks:
    has_date = task["date"] and task["date"] >= today
    has_client = task["client"] and task["client"] != "N/A" and task["client"] != "equipo@inspector.local"

    if has_date and has_client:
        task["priority"] = 1
        priority_tasks_with_client_and_date.append(task)
    elif has_date:
        task["priority"] = 2
        priority_tasks_with_date_only.append(task)
    elif has_client:
        task["priority"] = 3
        priority_tasks_with_client_only.append(task)
    else:
        task["priority"] = 4
        general_tasks.append(task)

# Sort tasks within each priority group
priority_tasks_with_client_and_date.sort(key=lambda x: x["date"])
priority_tasks_with_date_only.sort(key=lambda x: x["date"])
priority_tasks_with_client_only.sort(key=lambda x: x["client"])


# Compile the summary using a list of lines
summary_lines = []
summary_lines.append("# Resumen semanal de tareas pendientes

")

summary_lines.append("## Tareas prioritarias (con fecha y cliente concreto)

")
for task in priority_tasks_with_client_and_date:
    date_str = task["date"].strftime("%d de %B") if task["date"] else "Sin fecha"
    client_str = f" - Cliente: {task['client']}" if task["client"] and task["client"] != "N/A" else ""
    summary_lines.append(f"- [ ] {task['description']} (Fecha: {date_str}{client_str})
")

summary_lines.append("
## Tareas prioritarias (con fecha especifica)

")
for task in priority_tasks_with_date_only:
    date_str = task["date"].strftime("%d de %B") if task["date"] else "Sin fecha"
    summary_lines.append(f"- [ ] {task['description']} (Fecha: {date_str})
")

summary_lines.append("
## Tareas con cliente (sin fecha especifica)

")
for task in priority_tasks_with_client_only:
    client_str = f" - Cliente: {task['client']}" if task["client"] and task["client"] != "N/A" else ""
    summary_lines.append(f"- [ ] {task['description']}{client_str}
")

summary_lines.append("
## Otras tareas

")
for task in general_tasks:
    summary_lines.append(f"- [ ] {task['description']}
")

summary_content = "".join(summary_lines)

with open("resultado.md", "w", encoding="utf-8") as f:
    f.write(summary_content)

print("Summary generated in resultado.md")