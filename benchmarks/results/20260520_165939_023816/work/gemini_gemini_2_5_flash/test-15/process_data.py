
import csv
import json
import re

# Read CSV content from file
with open('assistant_synthetic/contactos_50.csv', 'r', encoding='utf-8') as f:
    csv_content = f.read()

# Read JSONL content from file
with open('assistant_synthetic/notas_voz.jsonl', 'r', encoding='utf-8') as f:
    jsonl_content = f.read()

# Parse CSV content
contacts = []
csv_reader = csv.DictReader(csv_content.splitlines())
for row in csv_reader:
    contacts.append(row)

# Parse JSONL content
voice_notes = []
for line in jsonl_content.splitlines():
    if line.strip():
        voice_notes.append(json.loads(line))

results = []

for note in voice_notes:
    transcript = note['transcript']
    matched_person = "N/A"
    matched_company = "N/A"
    matched_email = "N/A"

    for contact in contacts:
        # Create regex patterns for full name, first name, and company name
        full_name_pattern = r'\b' + re.escape(contact['nombre']) + r'\b'
        first_name = contact['nombre'].split(' ')[0]
        first_name_pattern = r'\b' + re.escape(first_name) + r'\b'
        company_name_pattern = r'\b' + re.escape(contact['empresa']) + r'\b'

        if re.search(full_name_pattern, transcript, re.IGNORECASE):
            matched_person = contact['nombre']
            matched_company = contact['empresa']
            matched_email = contact['email']
            break
        elif re.search(company_name_pattern, transcript, re.IGNORECASE):
            matched_person = contact['nombre']
            matched_company = contact['empresa']
            matched_email = contact['email']
            break
        elif re.search(first_name_pattern, transcript, re.IGNORECASE):
            matched_person = contact['nombre']
            matched_company = contact['empresa']
            matched_email = contact['email']
            break

    results.append({
        'Tarea': transcript,
        'Persona': matched_person,
        'Empresa': matched_company,
        'Email': matched_email
    })

# Format as Markdown table
# Construct header first with explicit 
 escapes
markdown_header = "| Tarea | Persona | Empresa | Email |
|-------|---------|---------|-------|
"
markdown_rows = []
for result in results:
    markdown_rows.append(f"| {result['Tarea']} | {result['Persona']} | {result['Empresa']} | {result['Email']} |
")

markdown_table = markdown_header + "".join(markdown_rows)

# Write to resultado.md
with open('resultado.md', 'w', encoding='utf-8') as f:
    f.write(markdown_table)

print("resultado.md generated successfully.")
