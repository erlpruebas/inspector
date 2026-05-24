<think>
Okay, I need to generate a weekly summary of pending tasks from the provided JSONL and MD files. Let me start by understanding the data.

First, the emails_hilos.md has several threads. Each thread has a subject and dates. For example, Hilo E-001 is about a demo with Clinica Centro on May 14th. That's a specific date, so it should be prioritized. Similarly, Hilo E-004 mentions a meeting in Barcelona on May 18th. Hilo E-003 needs comments by May 12th. Hilo E-002 has a deadline of May 13th. Hilo E-006 is a pending proposal with a follow-up needed next week.

Now, the notas_voz.jsonl has voice notes. Each entry has a transcript. I need to extract tasks with specific dates or clients. For instance, VN-001 mentions confirming a demo with Noelia before Thursday (May 14). VN-002 is about sending a CSV to Luis with a 4% discount. VN-003 is buying a ticket for the Barcelona meeting on the 18th. VN-006 is reviewing a contract by May 12. VN-011 is sending an agenda with a training milestone on the 22nd. VN-015 is following up with Paula Ferrer. There's also VN-020 about reserving a room on Friday at 9:30.

I should prioritize tasks with specific dates or clients. Let me list them out, grouping similar ones. The demo with Clinica Centro is on the 14th, so confirm that. The Barcelona meeting on the 18th needs a ticket. The contract review by IberLegal is due on the 12th. The proposal for BravoSoft needs a follow-up. The CSV for Delta Equipos with the discount. The agenda for Laura Marin with the training hito. The SSL certificate renewal by May 28. Also, the payment check for Norte SA and the monthly report.

I need to structure the summary by date, starting with the nearest deadlines. May 12th is first, then 13th, 14th, 18th, 22nd, and 28th. Each task should mention the client, action, and deadline. Make sure to include both emails and voice notes. Avoid duplicates. For example, the Barcelona meeting is mentioned in both a voice note and an email, so combine them. Check all tasks for specific dates or clients. Omit tasks without clear deadlines unless they're important. Finally, format it in markdown with sections for each date and bullet points.
</think>

# Resumen semanal de tareas pendientes (2026-05-13)

## Compromisos con fecha concreta
### 2026-05-12 (Viernes)
- [IberLegal] Revisar contrato soporte (cláusulas 8 y renovación automática)  
  *Origen:* Email Hilo E-003 + Nota VN-006

### 2026-05-13 (Sábado)
- [Delta Equipos] Enviar CSV actualizado con descuento 4% en monitores 27  
  *Origen:* Email Hilo E-002 + Nota VN-002

### 2026-05-14 (Domingo)
- [Clinica Centro] Confirmar demo del módulo de pagos con Noelia  
  *Origen:* Email Hilo E-001 + Nota VN-001

### 2026-05-18 (Jueves)
- [Barna Health] Comprar billete para reunión presencial en Barcelona  
  *Origen:* Email Hilo E-004 + Nota VN-003

## Tareas con cliente concreto
### 2026-05-15 (Lunes)
- [BravoSoft] Seguimiento a Paula Ferrer sobre propuesta CRM  
  *Origen:* Nota VN-015

- [Zenit Food] Llamar a Tomas por licencias y confirmar dirección fiscal  
  *Origen:* Nota VN-010

### 2026-05-22 (Viernes)
- [Laura Marin] Enviar agenda de implantación con hito de formación  
  *Origen:* Nota VN-011

## Plazos técnicos
### 2026-05-28 (Jueves)
- [Cobalto] Renovar certificado SSL  
  *Origen:* Nota VN-013

## Pendientes sin fecha definida
- [Norte SA] Cruzar pagos con facturas (falta factura de 847,50€)  
  *Origen:* Nota VN-016

- [GreenBox] Buscar alternativa barata a herramienta de encuestas  
  *Origen:* Nota VN-009

- [Nova Iberia] Preparar informe en PDF con resumen ejecutivo  
  *Origen:* Email Hilo E-005 + Nota VN-008

- [Internos] Reservar sala para reunión del viernes a las 9:30  
  *Origen:* Nota VN-020
