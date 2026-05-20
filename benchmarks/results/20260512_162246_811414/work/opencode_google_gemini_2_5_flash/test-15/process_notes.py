
import json
import csv
import re

def process_voice_notes(notas_voz_path, contactos_path):
    # Load voice notes
    voice_notes = []
    with open(notas_voz_path, 'r', encoding='utf-8') as f:
        for line in f:
            voice_notes.append(json.loads(line))

    # Load contacts
    contacts = []
    with open(contactos_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            contacts.append(row)

    results = []
    for note in voice_notes:
        transcript = note['transcript']
        found_person = 'N/A'
        found_company = 'N/A'
        found_email = 'N/A'

        best_match_found = False

        # First, try to find a strict match (full name and company)
        for contact in contacts:
            nombre_lower = contact['nombre'].lower()
            empresa_lower = contact['empresa'].lower()
            
            if nombre_lower in transcript.lower() and empresa_lower in transcript.lower():
                found_person = contact['nombre']
                found_company = contact['empresa']
                found_email = contact['email']
                best_match_found = True
                break
        
        # If no strict match, try a partial name match (first name and company)
        if not best_match_found:
            for contact in contacts:
                nombre_parts = contact['nombre'].split(' ')
                first_name_lower = nombre_parts[0].lower()
                empresa_lower = contact['empresa'].lower()

                if first_name_lower in transcript.lower() and empresa_lower in transcript.lower():
                    # Check if the full name (starting with first name) is in the transcript
                    # or if the first name plus the company is a reasonable match
                    found_person = contact['nombre'] # Assign the full name from contact
                    found_company = contact['empresa']
                    found_email = contact['email']
                    best_match_found = True
                    break
        
        # If no strict or partial name/company match, try to find just a person or just a company
        # This is a fallback if no specific person-company pair is identified
        if not best_match_found:
            for contact in contacts:
                # Try to find full name
                if contact['nombre'].lower() in transcript.lower():
                    found_person = contact['nombre']
                    # No email or company unless a full pair is found
                    break
                
                # Try to find company name
                if contact['empresa'].lower() in transcript.lower():
                    found_company = contact['empresa']
                    # No email or person unless a full pair is found
                    break

        results.append({
            'tarea': transcript,
            'persona': found_person,
            'empresa': found_company,
            'email': found_email
        })

    # Generate Markdown table
    markdown_output = "| Tarea | Persona | Empresa | Email |\n"
    markdown_output += "|---|---|---|---|\n"
    for item in results:
        # Escape pipe characters in the transcript to avoid breaking the markdown table
        escaped_tarea = item['tarea'].replace('|', '\\|')
        markdown_output += f"| {escaped_tarea} | {item['persona']} | {item['empresa']} | {item['email']} |\n"
    
    return markdown_output

if __name__ == "__main__":
    output_path = "resultado.md"
    notas_voz_file = "assistant_synthetic/notas_voz.jsonl"
    contactos_file = "assistant_synthetic/contactos_50.csv"

    markdown_table = process_voice_notes(notas_voz_file, contactos_file)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_table)
