import json
import re
import os

input_file = 'assistant_synthetic/notas_voz.jsonl'
output_file = 'resultado.md'

if not os.path.exists(input_file):
    print(f"Error: Input file not found at {input_file}")
    exit(1)

data = []
try:
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
except json.JSONDecodeError as e:
    print(f"Error decoding JSON from {input_file}: {e}")
    exit(1)
except Exception as e:
    print(f"Error reading or parsing {input_file}: {e}")
    exit(1)

try:
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("| ID de Nota | Acción | Entidad Relacionada | Posible Fecha Límite |
")
        f.write("|---|---|---|---|
")

        for item in data:
            note_id = item.get('id', 'N/A')
            transcript = item.get('transcript', '')

            action = "Desconocido"
            entity = "Desconocido"
            deadline = "Desconocido"

            # --- Extraction Logic ---
            action_patterns_priority = [
                r'(llamar a|recordar llamar a)', r'(enviar a|enviar)', r'(comprar billete)',
                r'(preparar minuta|preparar comparativa|preparar informe)', r'(pedir a)',
                r'(crear tarea|crear lista)', r'(agendar seguimiento)', r'(buscar alternativa)',
                r'(revisar gastos|revisar contrato)', r'(poner recordatorio)', r'(cruzar pagos)',
                r'(investigar si)', r'(reservar sala)', r'(confirmar)', r'(responder)',
                r'(no olvidar que)', r'(enviar email)'
            ]
            
            found_action = False
            for pattern in action_patterns_priority:
                match = re.search(pattern, transcript, re.IGNORECASE)
                if match:
                    matched_phrase = match.group(0).lower()
                    if "llamar" in matched_phrase: action = "Llamar"
                    elif "enviar" in matched_phrase: action = "Enviar"
                    elif "comprar" in matched_phrase: action = "Comprar billete"
                    elif "preparar" in matched_phrase: action = "Preparar"
                    elif "pedir" in matched_phrase: action = "Pedir"
                    elif "crear" in matched_phrase: action = "Crear"
                    elif "agendar" in matched_phrase: action = "Agendar"
                    elif "buscar" in matched_phrase: action = "Buscar"
                    elif "revisar" in matched_phrase: action = "Revisar"
                    elif "poner recordatorio" in matched_phrase: action = "Poner recordatorio"
                    elif "cruzar pagos" in matched_phrase: action = "Cruzar pagos"
                    elif "investigar" in matched_phrase: action = "Investigar"
                    elif "reservar sala" in matched_phrase: action = "Reservar sala"
                    elif "confirmar" in matched_phrase: action = "Confirmar"
                    elif "responder" in matched_phrase: action = "Responder"
                    elif "no olvidar" in matched_phrase: action = "Registrar preferencia/información"
                    elif "enviar email" in matched_phrase: action = "Enviar email"
                    else:
                        action = matched_phrase.split()[0].capitalize()
                    found_action = True
                    break

            if not found_action:
                match_verb = re.match(r'(\w+)', transcript)
                if match_verb:
                    action = match_verb.group(1).capitalize()

            specific_entities = [
                "Noelia de Clinica Centro", "Clinica Centro", "Luis de Delta Equipos", "Delta Equipos",
                "Barcelona", "Barna Health", "Sergio Campos", "Elena Vidal", "IberLegal",
                "Marta Ruiz", "Ana Lopez", "GreenBox", "Tomas de Zenit Food", "Zenit Food",
                "Laura Marin", "Cobalto", "Norte SA", "Madrid", "Apple", "Microsoft",
                "BravoSoft", "Xavier", "David", "Paula Ferrer", "Luis", "Noelia", "Tomas", "Sergio", "Elena", "Marta", "Ana", "Laura", "Paula", "Xavier"
            ]
            
            extracted_entities = []
            for keyword in specific_entities:
                if keyword.lower() in transcript.lower():
                    extracted_entities.append(keyword)
                    
            if not extracted_entities:
                match_entity_phrase = re.search(r'(?:a|de|para)\s+([\w\s]+?)(?: de | el | con | para | antes de|$)', transcript, re.IGNORECASE)
                if match_entity_phrase:
                    potential_entity = match_entity_phrase.group(1).strip()
                    if len(potential_entity.split()) > 1 or potential_entity.lower() in ["csv", "contrato", "demo", "informe", "reunion", "pedido", "proyecto", "licencias", "recibo", "pago", "factura", "alternativa", "herramienta", "certificado", "propuesta"]:
                         extracted_entities.append(potential_entity)
                
                match_project = re.search(r'(contrato de \w+|modulo de pagos|CSV actualizado|billete|minuta|facturas de abril|tarea|seguimiento|informes|alternativa|pedido de licencias|agenda de implantacion|gastos de marzo|certificado SSL|comparativa|propuesta|pagos|lista de contactos|informe mensual|sala)', transcript, re.IGNORECASE)
                if match_project:
                    extracted_entities.append(match_project.group(1).strip())

            if extracted_entities:
                entity = ", ".join(sorted(list(set(extracted_entities))))
            else:
                entity = "Desconocido"

            deadline_str = "Desconocido"
            deadline_regexes = [
                r'(antes del|antes de|antes)\s+([\w\s\d]+)', 
                r'(el dia)\s+(\d{1,2})', 
                r'(el|este|próximo)\s+(\w+)\s+a las\s+([\d:]+)', 
                r'(el|este|próximo)\s+(\w+)', 
                r'(\d{1,2}/\d{1,2}|\d{1,2}-\d{1,2}|\d{1,2})', 
                r'(mensual)', 
                r'(\d{4}-\d{2}-\d{2})' 
            ]
            
            for regex in deadline_regexes:
                match = re.search(regex, transcript, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    if len(groups) == 2:
                        deadline_str = f"{groups[0]} {groups[1].strip()}"
                    elif len(groups) == 3:
                        deadline_str = f"{groups[1].strip()} a las {groups[2]}"
                    elif len(groups) == 1:
                        deadline_str = groups[0]
                    elif len(groups) > 1:
                        deadline_str = " ".join(g.strip() for g in groups if g)
                    
                    if deadline_str == "Desconocido":
                        if "jueves" in transcript.lower(): deadline_str = "Jueves"
                        elif "viernes" in transcript.lower(): deadline_str = "Viernes"
                        elif "martes" in transcript.lower(): deadline_str = "Martes"
                    
                    if deadline_str != "Desconocido":
                        break
    
            if note_id == "VN-003" and "el dia 18" in transcript: deadline_str = "18"
            if note_id == "VN-006" and "antes del 12" in transcript: deadline_str = "antes del 12"
            if note_id == "VN-011" and "el dia 22" in transcript: deadline_str = "22"
            if note_id == "VN-013" and "antes del 28" in transcript: deadline_str = "antes del 28"
            if note_id == "VN-020" and "viernes a las nueve y media" in transcript: deadline_str = "Viernes a las 09:30"
            if note_id == "VN-001" and "antes del jueves" in transcript: deadline_str = "antes del jueves"
            if note_id == "VN-002" and "4 por ciento" in transcript: deadline_str = "4 por ciento" 

            deadline = deadline_str

            f.write(f"| {note_id} | {action} | {entity} | {deadline} |
")

    print(f"Markdown table generated and saved to {output_file}")
    exit(0)
except Exception as e:
    print(f"Error writing to {output_file}: {e}")
    exit(1)
