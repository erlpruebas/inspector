import json
import re
from datetime import date, timedelta

current_date = date(2026, 5, 20) # Wednesday

def get_next_or_current_weekday(start_date, weekday_name):
    weekdays = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
    target_weekday_num = weekdays.index(weekday_name.lower())
    days_ahead = target_weekday_num - start_date.weekday()
    if days_ahead < 0:  # If the target weekday has already passed this week
        days_ahead += 7
    return start_date + timedelta(days=days_ahead)

def resolve_date_limit(transcript):
    limit = ""
    
    # "el dia X"
    day_match = re.search(r"el dia (\d{1,2})", transcript)
    if day_match:
        day = int(day_match.group(1))
        # Assuming current month and year
        possible_date = date(current_date.year, current_date.month, day)
        if possible_date >= current_date:
            limit = possible_date.strftime("%Y-%m-%d")
        else: # If day is in the past this month, check next month
            if current_date.month == 12:
                possible_date = date(current_date.year + 1, 1, day)
            else:
                possible_date = date(current_date.year, current_date.month + 1, day)
            limit = possible_date.strftime("%Y-%m-%d")

    # "antes del X" deadlines
    if "antes del jueves" in transcript and not limit:
        target_day = get_next_or_current_weekday(current_date, "jueves")
        limit = target_day.strftime("%Y-%m-%d")
    elif "antes del 12" in transcript and not limit: # May 12, 2026
        target_date = date(current_date.year, current_date.month, 12)
        if target_date >= current_date:
            limit = target_date.strftime("%Y-%m-%d")
        else:
            limit = "" # Already passed
    elif "antes del 28" in transcript and not limit: # May 28, 2026
        target_date = date(current_date.year, current_date.month, 28)
        if target_date >= current_date:
            limit = target_date.strftime("%Y-%m-%d")
        else:
            if current_date.month == 12:
                target_date = date(current_date.year + 1, 1, 28)
            else:
                target_date = date(current_date.year, current_date.month + 1, 28)
            limit = target_date.strftime("%Y-%m-%d")

    # Day of week
    elif "el martes" in transcript and not limit:
        next_tuesday = get_next_or_current_weekday(current_date, "martes")
        limit = next_tuesday.strftime("%Y-%m-%d")
    elif "el viernes" in transcript and not limit:
        next_friday = get_next_or_current_weekday(current_date, "viernes")
        limit = next_friday.strftime("%Y-%m-%d")
            
    return limit

def process_transcript(transcript):
    accion = ""
    entidad_relacionada = ""
    posible_fecha_limite = resolve_date_limit(transcript)

    if "Recordar llamar a " in transcript:
        match = re.search(r"Recordar llamar a (.*?) de (.*?) (?:antes del|para confirmar)", transcript)
        if match:
            person = match.group(1)
            company = match.group(2).split(" ")[0]
            accion = f"Llamar a {person}"
            entidad_relacionada = f"{person} ({company})"
        else: # Fallback if no company is mentioned
             match = re.search(r"Recordar llamar a (.*?) (?:antes del|para confirmar)", transcript)
             if match:
                 person = match.group(1).strip()
                 accion = f"Llamar a {person}"
                 entidad_relacionada = person
    elif "Enviar a " in transcript and " el CSV actualizado de " in transcript:
        match = re.search(r"Enviar a (.*?) de (.*?) el CSV actualizado de (.*?);", transcript)
        if match:
            person = match.group(1)
            company = match.group(2)
            item = match.group(3).split(";")[0]
            accion = f"Enviar {item} a {person}"
            entidad_relacionada = f"{person} ({company})"
    elif "Comprar billete para " in transcript and " si " in transcript:
        match = re.search(r"Comprar billete para (.*?) el dia (\d{1,2}) si (.*?) confirma la reunion de (.*?)\.", transcript)
        if match:
            city = match.group(1)
            person = match.group(3)
            company = match.group(4)
            accion = f"Comprar billete para {city}"
            entidad_relacionada = f"{person} ({company})"
    elif "Preparar minuta para " in transcript:
        match = re.search(r"Preparar minuta para (.*?) con (.*?)\.", transcript)
        if match:
            person = match.group(1)
            accion = f"Preparar minuta para {person}"
            entidad_relacionada = person
    elif "Pedir a " in transcript and " las facturas de abril" in transcript:
        match = re.search(r"Pedir a (.*?) las facturas de abril que no aparecen en el banco\.", transcript)
        if match:
            person = match.group(1)
            accion = f"Pedir facturas de abril a {person}"
            entidad_relacionada = person
    elif "Crear tarea para revisar contrato de " in transcript:
        match = re.search(r"Crear tarea para revisar contrato de (.*?); (.*?) pidio respuesta", transcript)
        if match:
            company = match.group(1)
            person = match.group(2).split(" ")[0]
            accion = f"Revisar contrato de {company}"
            entidad_relacionada = f"{company} (contacto: {person})"
    elif "Agendar seguimiento con " in transcript:
        match = re.search(r"Agendar seguimiento con (.*?) el (.*?) a las (.*?) por el tema de (.*?)\.", transcript)
        if match:
            person = match.group(1)
            accion = f"Agendar seguimiento con {person}"
            entidad_relacionada = person
    elif "No olvidar que " in transcript and " prefiere recibir informes" in transcript:
        match = re.search(r"No olvidar que (.*?) prefiere recibir informes en PDF y resumen ejecutivo corto\.", transcript)
        if match:
            person = match.group(1)
            accion = f"Recordar preferencias de {person}"
            entidad_relacionada = person
    elif "Buscar alternativa barata a herramienta de encuestas para " in transcript:
        match = re.search(r"Buscar alternativa barata a herramienta de encuestas para (.*?)\.", transcript)
        if match:
            company = match.group(1)
            accion = "Buscar alternativa a herramienta de encuestas"
            entidad_relacionada = company
    elif "Llamar a " in transcript and " por pedido de licencias" in transcript:
        match = re.search(r"Llamar a (.*?) de (.*?) por pedido de licencias y confirmar direccion fiscal\.", transcript)
        if match:
            person = match.group(1)
            company = match.group(2)
            accion = f"Llamar a {person} de {company}"
            entidad_relacionada = f"{person} ({company})"
    elif "Enviar agenda de implantacion a " in transcript:
        match = re.search(r"Enviar agenda de implantacion a (.*?); incluir hito de formacion el dia (\d{1,2})\.", transcript)
        if match:
            person = match.group(1)
            accion = f"Enviar agenda de implantacion a {person}"
            entidad_relacionada = person
    elif "Revisar gastos de marzo" in transcript:
        accion = "Revisar gastos de marzo"
        entidad_relacionada = ""
    elif "Poner recordatorio para renovar certificado SSL de " in transcript:
        match = re.search(r"Poner recordatorio para renovar certificado SSL de (.*?) antes del (\d{1,2})\.", transcript)
        if match:
            company = match.group(1)
            accion = f"Renovar certificado SSL de {company}"
            entidad_relacionada = company
    elif "Preparar comparativa " in transcript and " contra " in transcript:
        match = re.search(r"Preparar comparativa (.*?) contra (.*?) para tareas de ofimatica\.", transcript)
        if match:
            entity1 = match.group(1)
            entity2 = match.group(2)
            accion = f"Preparar comparativa {entity1} contra {entity2}"
            entidad_relacionada = f"{entity1}, {entity2}"
    elif "Enviar email amable a " in transcript:
        match = re.search(r"Enviar email amable a (.*?), no ha contestado la propuesta de (.*?)\.", transcript)
        if match:
            person = match.group(1)
            company = match.group(2)
            accion = f"Enviar email a {person}"
            entidad_relacionada = f"{person} ({company})"
    elif "Cruzar pagos de " in transcript and " con facturas" in transcript:
        match = re.search(r"Cruzar pagos de (.*?) con facturas, creo que falta una de (.*?) con cincuenta\.", transcript)
        if match:
            company = match.group(1)
            accion = f"Cruzar pagos de {company} con facturas"
            entidad_relacionada = company
    elif "Crear lista de contactos prioritarios de " in transcript:
        match = re.search(r"Crear lista de contactos prioritarios de (.*?) con nivel alta\.", transcript)
        if match:
            city = match.group(1)
            accion = f"Crear lista de contactos prioritarios de {city}"
            entidad_relacionada = city
    elif "Investigar si " in transcript and " ha subido mas que " in transcript:
        match = re.search(r"Investigar si (.*?) ha subido mas que (.*?) en los ultimos seis meses\.", transcript)
        if match:
            company1 = match.group(1)
            company2 = match.group(2)
            accion = f"Investigar subida de {company1} y {company2}"
            entidad_relacionada = f"{company1}, {company2}"
    elif "Preparar informe mensual de incidencias: incluir " in transcript:
        match = re.search(r"Preparar informe mensual de incidencias: incluir (.*?) y facturacion\.", transcript)
        if match:
            entities = match.group(1) # "Clinica Centro"
            accion = "Preparar informe mensual de incidencias"
            entidad_relacionada = entities
    elif "Recordar reservar sala para reunion interna del viernes" in transcript:
        accion = "Reservar sala para reunion interna"
        entidad_relacionada = ""

    return accion, entidad_relacionada, posible_fecha_limite

# Read the content of the JSONL file
with open("D:/inspector/benchmarks/results/20260520_165939_023816/work/gemini_gemini_2_5_flash/test-03/assistant_synthetic/notas_voz.jsonl", "r") as f:
    file_content = f.read()

output_lines = []
output_lines.append("| id de nota | accion | entidad relacionada | posible fecha limite |")
output_lines.append("|---|---|---|---|")

for line in file_content.strip().split('
'):
    data = json.loads(line)
    note_id = data["id"]
    transcript = data["transcript"]
    accion, entidad_relacionada, posible_fecha_limite = process_transcript(transcript)
    output_lines.append(f"| {note_id} | {accion} | {entidad_relacionada} | {posible_fecha_limite} |")

markdown_table = "
".join(output_lines)

with open("D:/inspector/benchmarks/results/20260520_165939_023816/work/gemini_gemini_2_5_flash/test-03/resultado.md", "w") as f:
    f.write(markdown_table)

print("Markdown table generated and saved to resultado.md")
