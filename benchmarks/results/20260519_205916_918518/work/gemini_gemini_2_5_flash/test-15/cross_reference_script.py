import json, csv

with open('assistant_synthetic/notas_voz.jsonl', 'r') as f:
    voice_notes = [json.loads(line) for line in f]

with open('assistant_synthetic/contactos_50.csv', 'r') as f:
    reader = csv.DictReader(f)
    contacts = list(reader)

results = []
for note in voice_notes:
    transcript = note['transcript']
    for contact in contacts:
        person_name = contact['nombre']
        company_name = contact['empresa']
        email = contact['email']

        if person_name in transcript or company_name in transcript:
            results.append({
                'tarea': transcript,
                'persona': person_name,
                'empresa': company_name,
                'email': email
            })

markdown_table = '''| Tarea | Persona | Empresa | Email |
|---|---|---|---|
'''
for res in results:
    task_summary = res['tarea'][:50] + '...' if len(res['tarea']) > 50 else res['tarea']
    markdown_table += f"| {task_summary} | {res['persona']} | {res['empresa']} | {res['email']} |
"

print(markdown_table)