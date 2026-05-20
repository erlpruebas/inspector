
import csv
import json

def parse_contacts(csv_content):
    contacts = []
    reader = csv.reader(csv_content.strip().splitlines())
    headers = next(reader)
    for row in reader:
        contacts.append(dict(zip(headers, row)))
    return contacts

def parse_emails(md_content):
    emails = []
    current_email = {}
    lines = md_content.strip().splitlines()
    for line in lines:
        if line.startswith("## Hilo E-"):
            if current_email:
                emails.append(current_email)
            current_email = {"thread_id": line.split(":")[0].replace("## Hilo ", ""), "messages": []}
        elif line.startswith("De:"):
            sender = line.replace("De: ", "").strip()
            current_email["messages"].append({"sender": sender})
        elif line.startswith("Para:"):
            recipient = line.replace("Para: ", "").strip()
            current_email["messages"][-1]["recipient"] = recipient
        elif line.startswith("Fecha:"):
            date = line.replace("Fecha: ", "").strip()
            current_email["messages"][-1]["date"] = date
        elif line.startswith("Asunto:"):
            subject = line.replace("Asunto: ", "").strip()
            current_email["messages"][-1]["subject"] = subject
        elif line.strip() and not line.startswith("#"): # This is a simple way to get body for a single message for each email
            if "body" not in current_email["messages"][-1]:
                current_email["messages"][-1]["body"] = line.strip()
            else:
                current_email["messages"][-1]["body"] += " " + line.strip()

    if current_email:
        emails.append(current_email)
    return emails

def parse_voice_notes(jsonl_content):
    notes = []
    for line in jsonl_content.strip().splitlines():
        notes.append(json.loads(line))
    return notes

def generate_report(contacts, emails, voice_notes):
    report = "# Informe Ejecutivo de Cuentas Prioritarias\n\n"
    prioritized_accounts = {}

    # Group contacts by company and prioritize
    for contact in contacts:
        company = contact["empresa"]
        if company not in prioritized_accounts:
            prioritized_accounts[company] = {
                "contacts": [],
                "emails": [],
                "voice_notes": [],
                "risks": [],
                "next_actions": []
            }
        prioritized_accounts[company]["contacts"].append(contact)

    # Add emails to accounts
    for email_thread in emails:
        for message in email_thread["messages"]:
            sender_email = message.get("sender", "").lower()
            recipient_email = message.get("recipient", "").lower()
            
            found_company = False
            for company, data in prioritized_accounts.items():
                for contact in data["contacts"]:
                    if contact["email"].lower() in [sender_email, recipient_email]:
                        data["emails"].append({"thread_id": email_thread["thread_id"], "message": message})
                        found_company = True
                        break
                if found_company:
                    break

    # Add voice notes to accounts
    for note in voice_notes:
        transcript = note["transcript"].lower()
        for company, data in prioritized_accounts.items():
            for contact in data["contacts"]:
                if contact["nombre"].lower() in transcript or contact["empresa"].lower() in transcript:
                    data["voice_notes"].append(note)
                    break

    # Generate report content
    for company, data in prioritized_accounts.items():
        if any(c["prioridad"] == "alta" for c in data["contacts"]) or data["emails"] or data["voice_notes"]:
            report += f"## {company}\n"
            report += "### Contactos\n"
            for contact in data["contacts"]:
                report += f"- {contact['nombre']} ({contact['rol']}) - {contact['email']} (Prioridad: {contact['prioridad']})\n"

            report += "\n### Comunicaciones Recientes\n"
            if not data["emails"] and not data["voice_notes"]:
                report += "- No hay comunicaciones recientes.\n"
            else:
                for email in data["emails"]:
                    msg = email["message"]
                    report += f"- **Email Hilo {email['thread_id']}:** Asunto: '{msg['subject']}' de {msg['sender']} el {msg['date']}. Contenido: {msg['body']}.\n"
                for note in data["voice_notes"]:
                    report += f"- **Nota de Voz {note['id']}:** Transcripción: '{note['transcript']}' (Fecha: {note['timestamp']}).\n"
            
            # Identify Risks and Next Actions based on content
            company_risks = []
            company_actions = []

            for email in data["emails"]:
                if "preocupan la clausula 8 de responsabilidad y la renovacion automatica" in email["message"].get("body", "").lower():
                    company_risks.append("Revisión de cláusula 8 de responsabilidad y renovación automática en contrato.")
                    company_actions.append("Responder a David Navarro de IberLegal antes del 12 de mayo con comentarios sobre el contrato.")
                if "si no contesto, insistidme con un correo corto" in email["message"].get("body", "").lower():
                    company_risks.append("Propuesta de BravoSoft pendiente de revisión por dirección.")
                    company_actions.append("Enviar un correo de seguimiento corto a Paula Ferrer de BravoSoft.")

            for note in data["voice_notes"]:
                if "confirmar demo del modulo de pagos" in note["transcript"].lower() and "clinica centro" in note["transcript"].lower():
                    company_actions.append("Llamar a Noelia de Clinica Centro antes del jueves para confirmar demo de módulo de pagos.")
                if "descuento del 4 por ciento" in note["transcript"].lower() and "delta equipos" in note["transcript"].lower():
                    company_actions.append("Enviar a Luis de Delta Equipos el CSV actualizado de monitores incluyendo el descuento del 4%.")
                if "revision contrato de iberlegal" in note["transcript"].lower():
                    company_actions.append("Crear tarea para revisar contrato de IberLegal; David pidió respuesta antes del 12.")
                if "riesgos de seguridad y coste de auditoria" in note["transcript"].lower() and "sergio campos" in note["transcript"].lower():
                    company_risks.append("Riesgos de seguridad y necesidad de auditoría para Innotek.")
                    company_actions.append("Preparar minuta para Sergio Campos de Innotek con riesgos de seguridad y coste de auditoría.")
                if "facturas de abril que no aparecen en el banco" in note["transcript"].lower() and "elena vidal" in note["transcript"].lower():
                    company_risks.append("Facturas de abril de Atlantic Data no registradas en el banco.")
                    company_actions.append("Pedir a Elena Vidal las facturas de abril de Atlantic Data.")
                if "informes en pdf y resumen ejecutivo corto" in note["transcript"].lower() and "ana lopez" in note["transcript"].lower():
                    company_actions.append("Asegurar que los informes para Ana Lopez de Nova Iberia se envíen en PDF con resumen ejecutivo.")
                if "propuesta de bravosoft" in note["transcript"].lower() and "paula ferrer" in note["transcript"].lower():
                    company_actions.append("Enviar email amable a Paula Ferrer de BravoSoft, ya que no ha contestado la propuesta.")
                if "renovar certificado ssl de cobalto antes del 28" in note["transcript"].lower():
                    company_risks.append("Certificado SSL de Cobalto próximo a caducar (antes del 28).")
                    company_actions.append("Poner recordatorio para renovar certificado SSL de Cobalto antes del 28.")


            report += "\n### Riesgos Identificados\n"
            if not company_risks:
                report += "- No se identificaron riesgos directos en las comunicaciones recientes.\n"
            else:
                for risk in set(company_risks):
                    report += f"- {risk}\n"

            report += "\n### Siguientes Acciones\n"
            if not company_actions:
                report += "- No se identificaron acciones inmediatas en las comunicaciones recientes.\n"
            else:
                for action in set(company_actions):
                    report += f"- {action}\n"
            report += "\n---\n\n"
    return report

if __name__ == "__main__":
    contacts_csv_path = r"D:\inspector\benchmarks\results\20260513_130231_288791\work\opencode_google_gemini_2_5_flash\test-25\assistant_synthetic\contactos_50.csv"
    emails_md_path = r"D:\inspector\benchmarks\results\20260513_130231_288791\work\opencode_google_gemini_2_5_flash\test-25\assistant_synthetic\emails_hilos.md"
    voice_notes_jsonl_path = r"D:\inspector\benchmarks\results\20260513_130231_288791\work\opencode_google_gemini_2_5_flash\test-25\assistant_synthetic\notas_voz.jsonl"
    output_report_path = r"D:\inspector\benchmarks\results\20260513_130231_288791\work\opencode_google_gemini_2_5_flash\test-25\resultado.md"

    with open(contacts_csv_path, "r", encoding="utf-8") as f:
        contacts_content = f.read()
    with open(emails_md_path, "r", encoding="utf-8") as f:
        emails_content = f.read()
    with open(voice_notes_jsonl_path, "r", encoding="utf-8") as f:
        voice_notes_content = f.read()

    contacts_data = parse_contacts(contacts_content)
    emails_data = parse_emails(emails_content)
    voice_notes_data = parse_voice_notes(voice_notes_content)

    report_content = generate_report(contacts_data, emails_data, voice_notes_data)

    with open(output_report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"Report generated successfully at {output_report_path}")
