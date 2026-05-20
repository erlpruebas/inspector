import json
import re

input_file_path = "D:/inspector/benchmarks/results/20260519_205916_918518/work/gemini_gemini_2_5_flash/test-03/assistant_synthetic/notas_voz.jsonl"
output_file_path = "D:/inspector/benchmarks/results/20260519_205916_918518/work/gemini_gemini_2_5_flash/test-03/resultado.md"

extracted_tasks = []

# Regex for possible deadline
deadline_pattern = re.compile(
    r"(antes del (?:jueves|viernes|lunes|martes|miercoles|sabado|domingo|\d{1,2}))|" # antes del jueves, antes del 12
    r"(el dia \d{1,2})|"                                                            # el dia 18
    r"(el (?:jueves|viernes|lunes|martes|miercoles|sabado|domingo) a las \w+(?: y \w+)?)" # el martes a las cuatro
)

# Regex for related entities (prioritized)
# This is complex due to natural language, so multiple patterns are needed.
# Pattern for PERSON_XXXX or ORG_XXXX, with optional preceding name
person_org_pattern = re.compile(r"(?:a |de |para |con |el )?([A-Z][a-z]+(?: [A-Z][a-z]+)?)?\s*(PERSON_\d{4}|ORG_\d{4}(?:l)?(?: de [A-Z][a-z]+)?)([;,.\s]|$)")

# General entity keywords/phrases. Ordered by expected specificity/length.
general_entity_patterns = [
    re.compile(r"el CSV actualizado de monitores"),
    re.compile(r"modulo de pagos"),
    re.compile(r"billete para Barcelona"),
    re.compile(r"minuta para PERSON_\d{4} con riesgos de seguridad y coste de auditoria"),
    re.compile(r"minuta para PERSON_\d{4}"),
    re.compile(r"riesgos de seguridad y coste de auditoria"),
    re.compile(r"facturas de abril"),
    re.compile(r"contrato de IberLegal"),
    re.compile(r"seguimiento con PERSON_\d{4}"),
    re.compile(r"informes en PDF y resumen ejecutivo corto"),
    re.compile(r"alternativa barata a herramienta de encuestas para GreenBox"),
    re.compile(r"pedido de licencias y confirmar direccion fiscal"),
    re.compile(r"agenda de implantacion"),
    re.compile(r"gastos de marzo"),
    re.compile(r"certificado SSL de Cobalto"),
    re.compile(r"comparativa OpenRouter contra Gemini para tareas de ofimatica"),
    re.compile(r"email amable a PERSON_\d{4}"),
    re.compile(r"propuesta de BravoSoft"),
    re.compile(r"facturas"),
    re.compile(r"lista de contactos prioritarios de Madrid"),
    re.compile(r"Apple ha subido mas que Microsoft en los ultimos seis meses"),
    re.compile(r"informe mensual de incidencias: incluir ORG_\d{4} facturacion"),
    re.compile(r"informe mensual de incidencias"),
    re.compile(r"ORG_\d{4} facturacion"),
    re.compile(r"sala para reunion interna")
]

with open(input_file_path, 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        note_id = data['id']
        transcript = data['transcript']
        current_transcript = transcript.strip()

        accion = ""
        entidad_relacionada = ""
        posible_fecha_limite = ""

        # 1. Extract posible fecha limite
        deadline_match = deadline_pattern.search(current_transcript)
        if deadline_match:
            posible_fecha_limite = deadline_match.group(0).strip()
            current_transcript = current_transcript.replace(posible_fecha_limite, "").strip()

        # 2. Extract entidad relacionada
        entity_match_found = False

        # Try PERSON/ORG pattern first
        person_org_match = person_org_pattern.search(current_transcript)
        if person_org_match:
            name_part = person_org_match.group(1)
            org_person_part = person_org_match.group(2)
            if name_part:
                entidad_relacionada = f"{name_part.strip()} {org_person_part.strip()}"
            else:
                entidad_relacionada = org_person_part.strip()
            current_transcript = current_transcript.replace(person_org_match.group(0), "").strip()
            entity_match_found = True
        else:
            # If no PERSON/ORG, try general entity patterns
            for pattern in general_entity_patterns:
                entity_match = pattern.search(current_transcript)
                if entity_match:
                    entidad_relacionada = entity_match.group(0).strip()
                    current_transcript = current_transcript.replace(entity_match.group(0), "").strip()
                    entity_match_found = True
                    break
        
        # Fallback for entidad_relacionada: capture significant noun phrases if not already found
        if not entidad_relacionada:
            obj_match = re.search(r"(?:llamar a|enviar a|comprar|preparar|pedir a|crear|agendar|buscar|poner|revisar|investigar|incluir)\s+([^,;.:]+)", current_transcript, re.IGNORECASE)
            if obj_match:
                potential_entity = obj_match.group(1).strip()
                potential_entity = re.sub(r"^(el|la|los|las|un|una|unos|unas)\s+", "", potential_entity, flags=re.IGNORECASE).strip()
                potential_entity = re.sub(r"\s+(a|de|para|con|por|y|si)$", "", potential_entity, flags=re.IGNORECASE).strip()
                if len(potential_entity.split()) > 0 and potential_entity not in ["", "para", "con", "a"]:
                    entidad_relacionada = potential_entity
                    current_transcript = current_transcript.replace(obj_match.group(0), "", 1).strip()


        # 3. Extract accion
        # This should be the remaining leading verb phrase
        action_phrases_and_verbs = [
            re.compile(r"Recordar llamar"), re.compile(r"Recordar"),
            re.compile(r"Enviar a PERSON_\d{4}"), re.compile(r"Enviar"),
            re.compile(r"Comprar billete"), re.compile(r"Comprar"),
            re.compile(r"Preparar minuta"), re.compile(r"Preparar"),
            re.compile(r"Pedir a PERSON_\d{4} facturas"), re.compile(r"Pedir"),
            re.compile(r"Crear tarea para revisar"), re.compile(r"Crear tarea"), re.compile(r"Crear"),
            re.compile(r"Agendar seguimiento con PERSON_\d{4}"), re.compile(r"Agendar seguimiento"), re.compile(r"Agendar"),
            re.compile(r"No olvidar que PERSON_\d{4} prefiere recibir informes"), re.compile(r"No olvidar"),
            re.compile(r"Buscar alternativa"), re.compile(r"Buscar"),
            re.compile(r"Llamar a PERSON_\d{4} por pedido"), re.compile(r"Llamar"),
            re.compile(r"Enviar agenda de implantacion a PERSON_\d{4}"), re.compile(r"Enviar agenda"),
            re.compile(r"Revisar gastos"), re.compile(r"Revisar"),
            re.compile(r"Poner recordatorio para renovar"), re.compile(r"Poner recordatorio"), re.compile(r"Poner"),
            re.compile(r"Preparar comparativa"),
            re.compile(r"Enviar email amable a PERSON_\d{4}"), re.compile(r"Enviar email"),
            re.compile(r"ORG_\d{4} con facturas"), # This is a tricky one, will handle it as a specific action if possible
            re.compile(r"Crear lista de contactos"), re.compile(r"Crear lista"),
            re.compile(r"Investigar si Apple ha subido mas que Microsoft"), re.compile(r"Investigar"),
            re.compile(r"Preparar informe mensual de incidencias"), re.compile(r"Preparar informe"),
            re.compile(r"Recordar reservar sala"), re.compile(r"Recordar reservar")
        ]

        accion_found = False
        for phrase_pattern in action_phrases_and_verbs:
            action_match = phrase_pattern.match(current_transcript)
            if action_match:
                accion = action_match.group(0).strip()
                accion_found = True
                break
        
        if not accion_found:
            # Fallback for action: just take the beginning of the remaining transcript
            words = current_transcript.split()
            if len(words) > 0:
                accion = " ".join(words[:min(3, len(words))]).strip()

        # Clean up any remnants from other fields in accion/entidad_relacionada
        if posible_fecha_limite and posible_fecha_limite in accion:
            accion = accion.replace(posible_fecha_limite, "").strip()
        if entidad_relacionada and entidad_relacionada in accion:
            accion = accion.replace(entidad_relacionada, "").strip()
        
        if posible_fecha_limite and posible_fecha_limite in entidad_relacionada:
            entidad_relacionada = entidad_relacionada.replace(posible_fecha_limite, "").strip()

        # Final cleanup for punctuation and extra words
        accion = re.sub(r"^(?:a|de|para|con|por|el|la|los|las|un|una|unos|unas)\s+", "", accion, flags=re.IGNORECASE).strip()
        accion = re.sub(r"\s*(?:;|\.)+?$", "", accion).strip()
        entidad_relacionada = re.sub(r"\s*(?:;|\.)+?$", "", entidad_relacionada).strip()
        
        # Specific handling for VN-016: "ORG_0008 con facturas" -> accion: "Revisar", entidad: "ORG_0008 con facturas"
        if note_id == "VN-016" and "ORG_0008 con facturas" in transcript:
            accion = "Revisar"
            entidad_relacionada = "ORG_0008 con facturas"

        extracted_tasks.append({
            "id de nota": note_id,
            "accion": accion,
            "entidad relacionada": entidad_relacionada,
            "posible fecha limite": posible_fecha_limite
        })

# Generate Markdown table
markdown_table = "| id de nota | accion | entidad relacionada | posible fecha limite |
"
markdown_table += "|---|---|---|---|
"

for task in extracted_tasks:
    # Ensure no None values for output, replace with empty string if so
    _id = task['id de nota'] if task['id de nota'] is not None else ""
    _accion = task['accion'] if task['accion'] is not None else ""
    _entidad = task['entidad relacionada'] if task['entidad relacionada'] is not None else ""
    _fecha = task['posible fecha limite'] if task['posible fecha limite'] is not None else ""
    markdown_table += f"| {_id} | {_accion} | {_entidad} | {_fecha} |
"

with open(output_file_path, 'w', encoding='utf-8') as f:
    f.write(markdown_table)

print("Task extraction complete. Results written to resultado.md")
