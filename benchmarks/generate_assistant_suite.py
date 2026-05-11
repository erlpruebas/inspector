from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ASSET_ROOT = ROOT / "assets" / "assistant_synthetic"
SUITE_ROOT = ROOT / "tasks" / "assistant_suite"


CONTACTS = [
    ("Ana Lopez", "ana.lopez@novaiberia.es", "+34 600 100 001", "Madrid", "Nova Iberia", "Directora Operaciones", "cliente", "alta"),
    ("Luis Martin", "luis.martin@deltaequipos.es", "+34 600 100 002", "Valencia", "Delta Equipos", "Compras", "proveedor", "media"),
    ("Marta Ruiz", "marta.ruiz@clinicasol.es", "+34 600 100 003", "Sevilla", "Clinica Sol", "Administracion", "cliente", "alta"),
    ("Jorge Soler", "jorge.soler@logimedit.es", "+34 600 100 004", "Bilbao", "Logimedit", "Logistica", "partner", "media"),
    ("Elena Vidal", "elena.vidal@atlanticdata.es", "+34 600 100 005", "A Coruna", "Atlantic Data", "Finanzas", "cliente", "alta"),
    ("Sergio Campos", "sergio.campos@innotek.es", "+34 600 100 006", "Zaragoza", "Innotek", "CTO", "cliente", "alta"),
    ("Paula Ferrer", "paula.ferrer@bravosoft.es", "+34 600 100 007", "Malaga", "BravoSoft", "Ventas", "prospecto", "media"),
    ("David Navarro", "david.navarro@iberlegal.es", "+34 600 100 008", "Madrid", "IberLegal", "Legal", "proveedor", "media"),
    ("Clara Molina", "clara.molina@greenbox.es", "+34 600 100 009", "Barcelona", "GreenBox", "Marketing", "cliente", "baja"),
    ("Ruben Ortega", "ruben.ortega@metalsur.es", "+34 600 100 010", "Murcia", "MetalSur", "Gerencia", "cliente", "alta"),
    ("Teresa Blanco", "teresa.blanco@aquanet.es", "+34 600 100 011", "Vigo", "AquaNet", "Soporte", "cliente", "media"),
    ("Hector Mora", "hector.mora@finansys.es", "+34 600 100 012", "Madrid", "FinanSys", "Producto", "partner", "alta"),
    ("Lucia Torres", "lucia.torres@solucionesmar.es", "+34 600 100 013", "Cadiz", "Soluciones Mar", "Direccion", "cliente", "alta"),
    ("Marcos Gil", "marcos.gil@tecnoria.es", "+34 600 100 014", "Valladolid", "Tecnoria", "IT", "proveedor", "media"),
    ("Nuria Vega", "nuria.vega@almacenesnorte.es", "+34 600 100 015", "Santander", "Almacenes Norte", "Compras", "cliente", "media"),
    ("Oscar Prieto", "oscar.prieto@consultia.es", "+34 600 100 016", "Madrid", "Consultia", "Consultor", "partner", "baja"),
    ("Irene Sanz", "irene.sanz@biocentro.es", "+34 600 100 017", "Granada", "BioCentro", "Calidad", "cliente", "alta"),
    ("Victor Leon", "victor.leon@urbanlift.es", "+34 600 100 018", "Barcelona", "UrbanLift", "Operaciones", "cliente", "media"),
    ("Raquel Cano", "raquel.cano@nodalabs.es", "+34 600 100 019", "Madrid", "Noda Labs", "Data", "prospecto", "alta"),
    ("Adrian Pons", "adrian.pons@mediatres.es", "+34 600 100 020", "Palma", "MediaTres", "Cuentas", "cliente", "baja"),
    ("Beatriz Costa", "beatriz.costa@orionretail.es", "+34 600 100 021", "Barcelona", "Orion Retail", "Retail", "cliente", "alta"),
    ("Daniel Rios", "daniel.rios@ferrovia.es", "+34 600 100 022", "Oviedo", "Ferrovia", "Compras", "proveedor", "media"),
    ("Eva Roman", "eva.roman@kairon.es", "+34 600 100 023", "Madrid", "Kairon", "People", "cliente", "media"),
    ("Gonzalo Pardo", "gonzalo.pardo@mintcloud.es", "+34 600 100 024", "Valencia", "MintCloud", "Cloud", "partner", "alta"),
    ("Helena Suarez", "helena.suarez@puravida.es", "+34 600 100 025", "Alicante", "PuraVida", "Expansion", "prospecto", "media"),
    ("Ivan Duran", "ivan.duran@cobalto.es", "+34 600 100 026", "Madrid", "Cobalto", "Seguridad", "proveedor", "alta"),
    ("Julia Iglesias", "julia.iglesias@tresnaves.es", "+34 600 100 027", "Sevilla", "Tres Naves", "Direccion", "cliente", "alta"),
    ("Kevin Ramos", "kevin.ramos@aurea.es", "+34 600 100 028", "Barcelona", "Aurea", "Finanzas", "cliente", "media"),
    ("Laura Marin", "laura.marin@northwind.es", "+34 600 100 029", "Bilbao", "Northwind ES", "Ventas", "cliente", "alta"),
    ("Miguel Santos", "miguel.santos@argentalia.es", "+34 600 100 030", "Madrid", "Argentalia", "Inversiones", "prospecto", "media"),
    ("Noelia Castro", "noelia.castro@clinicacentro.es", "+34 600 100 031", "Madrid", "Clinica Centro", "Administracion", "cliente", "alta"),
    ("Pablo Herrero", "pablo.herrero@navilux.es", "+34 600 100 032", "Valencia", "Navilux", "Operaciones", "cliente", "media"),
    ("Rocio Nieto", "rocio.nieto@pixelarte.es", "+34 600 100 033", "Malaga", "PixelArte", "Diseno", "proveedor", "baja"),
    ("Samuel Ibanez", "samuel.ibanez@quantica.es", "+34 600 100 034", "Madrid", "Quantica", "Analitica", "partner", "alta"),
    ("Silvia Rey", "silvia.rey@transmed.es", "+34 600 100 035", "Zaragoza", "TransMed", "Logistica", "cliente", "media"),
    ("Tomas Vega", "tomas.vega@zenitfood.es", "+34 600 100 036", "Barcelona", "Zenit Food", "Compras", "cliente", "alta"),
    ("Valeria Navas", "valeria.navas@rednova.es", "+34 600 100 037", "Madrid", "RedNova", "Marketing", "prospecto", "media"),
    ("Xavier Puig", "xavier.puig@barnahealth.es", "+34 600 100 038", "Barcelona", "Barna Health", "IT", "cliente", "alta"),
    ("Yolanda Cruz", "yolanda.cruz@serconta.es", "+34 600 100 039", "Toledo", "SerConta", "Contabilidad", "proveedor", "media"),
    ("Alberto Saez", "alberto.saez@omniplus.es", "+34 600 100 040", "Madrid", "OmniPlus", "Direccion", "cliente", "alta"),
    ("Belen Arias", "belen.arias@vetor.es", "+34 600 100 041", "Gijon", "Vetor", "Soporte", "cliente", "baja"),
    ("Carlos Benitez", "carlos.benitez@solardesk.es", "+34 600 100 042", "Sevilla", "SolarDesk", "Operaciones", "cliente", "alta"),
    ("Diana Estevez", "diana.estevez@bluecargo.es", "+34 600 100 043", "Valencia", "BlueCargo", "Logistica", "cliente", "media"),
    ("Esteban Lozano", "esteban.lozano@helixia.es", "+34 600 100 044", "Madrid", "Helixia", "CTO", "partner", "alta"),
    ("Fabiola Mendez", "fabiola.mendez@optired.es", "+34 600 100 045", "Murcia", "OptiRed", "Ventas", "prospecto", "media"),
    ("Guillermo Casas", "guillermo.casas@neotaller.es", "+34 600 100 046", "Valladolid", "NeoTaller", "Gerencia", "cliente", "alta"),
    ("Ines Robles", "ines.robles@marketuno.es", "+34 600 100 047", "Madrid", "MarketUno", "Marketing", "cliente", "media"),
    ("Jaime Pastor", "jaime.pastor@alboran.es", "+34 600 100 048", "Malaga", "Alboran", "Legal", "proveedor", "media"),
    ("Lorena Vidal", "lorena.vidal@civitas.es", "+34 600 100 049", "Barcelona", "Civitas", "Producto", "cliente", "alta"),
    ("Manuel Fuentes", "manuel.fuentes@dueroapps.es", "+34 600 100 050", "Salamanca", "Duero Apps", "Direccion", "cliente", "media"),
]


VOICE_NOTES = [
    ("VN-001", "2026-05-03 08:12", "Recordar llamar a Noelia de Clinica Centro antes del jueves para confirmar demo del modulo de pagos."),
    ("VN-002", "2026-05-03 09:40", "Enviar a Luis de Delta Equipos el CSV actualizado de monitores; falta incluir descuento del 4 por ciento."),
    ("VN-003", "2026-05-03 11:18", "Comprar billete para Barcelona el dia 18 si Xavier confirma la reunion de Barna Health."),
    ("VN-004", "2026-05-04 07:55", "Preparar minuta para Sergio Campos con riesgos de seguridad y coste de auditoria."),
    ("VN-005", "2026-05-04 12:03", "Pedir a Elena Vidal las facturas de abril que no aparecen en el banco."),
    ("VN-006", "2026-05-05 10:34", "Crear tarea para revisar contrato de IberLegal; David pidio respuesta antes del 12."),
    ("VN-007", "2026-05-05 17:10", "Agendar seguimiento con Marta Ruiz el martes a las cuatro por el tema de administracion."),
    ("VN-008", "2026-05-06 08:05", "No olvidar que Ana Lopez prefiere recibir informes en PDF y resumen ejecutivo corto."),
    ("VN-009", "2026-05-06 14:29", "Buscar alternativa barata a herramienta de encuestas para GreenBox."),
    ("VN-010", "2026-05-07 09:00", "Llamar a Tomas de Zenit Food por pedido de licencias y confirmar direccion fiscal."),
    ("VN-011", "2026-05-07 15:12", "Enviar agenda de implantacion a Laura Marin; incluir hito de formacion el dia 22."),
    ("VN-012", "2026-05-08 08:43", "Revisar gastos de marzo porque hay dos cargos duplicados de hotel."),
    ("VN-013", "2026-05-08 13:20", "Poner recordatorio para renovar certificado SSL de Cobalto antes del 28."),
    ("VN-014", "2026-05-09 10:02", "Preparar comparativa OpenRouter contra Gemini para tareas de ofimatica."),
    ("VN-015", "2026-05-09 16:44", "Enviar email amable a Paula Ferrer, no ha contestado la propuesta de BravoSoft."),
    ("VN-016", "2026-05-10 09:16", "Cruzar pagos de Norte SA con facturas, creo que falta una de 847 con cincuenta."),
    ("VN-017", "2026-05-10 11:52", "Crear lista de contactos prioritarios de Madrid con nivel alta."),
    ("VN-018", "2026-05-10 19:30", "Investigar si Apple ha subido mas que Microsoft en los ultimos seis meses."),
    ("VN-019", "2026-05-11 08:25", "Preparar informe mensual de incidencias: incluir Clinica Centro y facturacion."),
    ("VN-020", "2026-05-11 10:00", "Recordar reservar sala para reunion interna del viernes a las nueve y media."),
]


EMAIL_THREADS = """# Historial de correos sinteticos

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


EXPENSES = {
    "gastos_2026_01.csv": [
        ("2026-01-08", "Hotel Madrid", "viajes", 180.00, 180.00, "ok"),
        ("2026-01-09", "Taxi aeropuerto", "viajes", 38.50, 38.50, "ok"),
        ("2026-01-15", "Software encuestas", "software", 49.00, 49.00, "ok"),
    ],
    "gastos_2026_02.csv": [
        ("2026-02-03", "Cena cliente", "comidas", 96.20, 96.20, "ok"),
        ("2026-02-14", "Tren Valencia", "viajes", 62.00, 62.00, "ok"),
        ("2026-02-22", "Licencia PDF", "software", 19.90, 29.90, "importe_discrepante"),
    ],
    "gastos_2026_03.csv": [
        ("2026-03-04", "Hotel Barcelona", "viajes", 210.00, 210.00, "posible_duplicado"),
        ("2026-03-04", "Hotel Barcelona", "viajes", 210.00, 210.00, "posible_duplicado"),
        ("2026-03-19", "Comida equipo", "comidas", 134.70, 134.70, "ok"),
    ],
    "gastos_2026_04.csv": [
        ("2026-04-02", "Dominio anual", "software", 14.99, 14.99, "ok"),
        ("2026-04-11", "Taxi cliente", "viajes", 28.30, 28.30, "sin_recibo"),
        ("2026-04-25", "Material oficina", "oficina", 73.40, 73.40, "ok"),
    ],
    "gastos_2026_05.csv": [
        ("2026-05-01", "Vuelo Barcelona", "viajes", 155.00, 155.00, "ok"),
        ("2026-05-03", "Suscripcion IA", "software", 120.00, 120.00, "revisar_proveedor"),
        ("2026-05-05", "Cafe reunion", "comidas", 18.40, 18.40, "ok"),
    ],
}


TASKS = [
    ("test-01", "Recordar cita de Clinica Centro", 1, ["agenda", "data_extraction"], ["assistant_synthetic/emails_hilos.md", "assistant_synthetic/contactos_50.csv"], ["Noelia Castro", "Clinica Centro", "14 de mayo", "11:30"]),
    ("test-02", "Crear lista de contactos prioritarios de Madrid", 1, ["data_filtering", "contacts"], ["assistant_synthetic/contactos_50.csv"], ["Madrid", "prioridad alta", "Ana Lopez", "Sergio Campos"]),
    ("test-03", "Extraer tareas de notas de voz", 1, ["task_extraction", "summarization"], ["assistant_synthetic/notas_voz.jsonl"], ["llamar", "enviar", "agendar", "reservar"]),
    ("test-04", "Redactar email de seguimiento a BravoSoft", 1, ["email_drafting", "tone_control"], ["assistant_synthetic/emails_hilos.md", "assistant_synthetic/contactos_50.csv"], ["Paula Ferrer", "BravoSoft", "correo corto", "propuesta CRM"]),
    ("test-05", "Detectar gasto discrepante de febrero", 1, ["expense_audit", "data_extraction"], ["assistant_synthetic/gastos_2026_02.csv"], ["Licencia PDF", "19.90", "29.90", "importe_discrepante"]),
    ("test-06", "Preparar agenda de viaje a Barcelona", 2, ["agenda", "synthesis"], ["assistant_synthetic/emails_hilos.md", "assistant_synthetic/notas_voz.jsonl"], ["Xavier Puig", "Barna Health", "18 de mayo", "10:00"]),
    ("test-07", "Conciliar preferencias de informe de Nova Iberia", 2, ["preference_extraction", "reporting"], ["assistant_synthetic/emails_hilos.md", "assistant_synthetic/contactos_50.csv"], ["Ana Lopez", "PDF", "resumen ejecutivo", "anexos"]),
    ("test-08", "Resumen semanal de tareas pendientes", 2, ["summarization", "prioritization"], ["assistant_synthetic/notas_voz.jsonl", "assistant_synthetic/emails_hilos.md"], ["IberLegal", "Clinica Centro", "Delta Equipos", "SSL"]),
    ("test-09", "Auditar duplicados de marzo", 2, ["expense_audit", "duplicate_detection"], ["assistant_synthetic/gastos_2026_03.csv"], ["Hotel Barcelona", "duplicado", "420.00", "210.00"]),
    ("test-10", "Crear CSV de proveedores", 2, ["data_filtering", "csv_generation"], ["assistant_synthetic/contactos_50.csv"], ["proveedor", "IberLegal", "Tecnoria", "SerConta"]),
    ("test-11", "Priorizar clientes de alta prioridad", 2, ["data_filtering", "prioritization"], ["assistant_synthetic/contactos_50.csv"], ["alta", "cliente", "Nova Iberia", "Clinica Centro"]),
    ("test-12", "Preparar minuta de contrato IberLegal", 2, ["email_analysis", "risk_extraction"], ["assistant_synthetic/emails_hilos.md", "assistant_synthetic/notas_voz.jsonl"], ["clausula 8", "responsabilidad", "renovacion automatica", "12 de mayo"]),
    ("test-13", "Informe de discrepancias de gastos Q1", 3, ["expense_audit", "multi_file_analysis"], ["assistant_synthetic/gastos_2026_01.csv", "assistant_synthetic/gastos_2026_02.csv", "assistant_synthetic/gastos_2026_03.csv"], ["Licencia PDF", "Hotel Barcelona", "duplicado", "febrero"]),
    ("test-14", "Crear calendario ICS de cuatro compromisos", 3, ["calendar_generation", "data_extraction"], ["assistant_synthetic/notas_voz.jsonl", "assistant_synthetic/emails_hilos.md"], ["Clinica Centro", "Barna Health", "sala", "viernes 09:30"]),
    ("test-15", "Cruzar notas de voz con contactos", 3, ["entity_resolution", "contacts"], ["assistant_synthetic/notas_voz.jsonl", "assistant_synthetic/contactos_50.csv"], ["Noelia Castro", "Luis Martin", "Tomas Vega", "Laura Marin"]),
    ("test-16", "Preparar briefing de seguridad para Innotek", 3, ["briefing", "synthesis"], ["assistant_synthetic/notas_voz.jsonl", "assistant_synthetic/contactos_50.csv"], ["Sergio Campos", "Innotek", "riesgos de seguridad", "auditoria"]),
    ("test-17", "Resumen financiero de gastos enero-mayo", 3, ["expense_audit", "aggregation"], list(f"assistant_synthetic/{name}" for name in EXPENSES), ["total mensual", "discrepancias", "sin_recibo", "revisar_proveedor"]),
    ("test-18", "Segmentar prospectos para campana", 3, ["contacts", "segmentation"], ["assistant_synthetic/contactos_50.csv"], ["prospecto", "BravoSoft", "Noda Labs", "RedNova"]),
    ("test-19", "Plan de seguimiento de implantacion", 3, ["planning", "timeline"], ["assistant_synthetic/notas_voz.jsonl", "assistant_synthetic/emails_hilos.md"], ["Laura Marin", "formacion", "dia 22", "hitos"]),
    ("test-20", "Informe de incidencias de Clinica Centro", 3, ["synthesis", "client_context"], ["assistant_synthetic/notas_voz.jsonl", "assistant_synthetic/emails_hilos.md", "assistant_synthetic/contactos_50.csv"], ["Clinica Centro", "Noelia Castro", "modulo de pagos", "facturacion"]),
    ("test-21", "Buscar alternativa a herramienta de encuestas", 4, ["web_search", "comparison", "reporting"], ["assistant_synthetic/notas_voz.jsonl"], ["GreenBox", "encuestas", "precio", "fuentes"]),
    ("test-22", "Comparar Apple y Microsoft seis meses", 4, ["web_search", "financial_analysis", "synthesis"], ["assistant_synthetic/notas_voz.jsonl"], ["Apple", "Microsoft", "seis meses", "fecha de consulta"]),
    ("test-23", "Investigar proveedor de SSO para Barna Health", 4, ["web_search", "technical_report", "client_context"], ["assistant_synthetic/emails_hilos.md", "assistant_synthetic/contactos_50.csv"], ["Barna Health", "SSO", "Xavier Puig", "fuentes"]),
    ("test-24", "Validar descuento Delta Equipos con mercado", 4, ["web_search", "local_data_crosscheck"], ["assistant_synthetic/emails_hilos.md", "assistant_synthetic/notas_voz.jsonl"], ["Delta Equipos", "monitores 27", "4%", "comparativa"]),
    ("test-25", "Informe ejecutivo de cuentas prioritarias", 4, ["synthesis", "contacts", "executive_report"], ["assistant_synthetic/contactos_50.csv", "assistant_synthetic/emails_hilos.md", "assistant_synthetic/notas_voz.jsonl"], ["clientes alta", "riesgos", "siguientes acciones", "Madrid"]),
    ("test-26", "Auditoria completa de gastos con recomendaciones", 4, ["expense_audit", "multi_file_analysis", "recommendations"], list(f"assistant_synthetic/{name}" for name in EXPENSES), ["duplicado", "sin_recibo", "importe_discrepante", "revisar_proveedor"]),
    ("test-27", "Preparar tablero de acciones por responsable", 4, ["task_extraction", "entity_resolution", "planning"], ["assistant_synthetic/notas_voz.jsonl", "assistant_synthetic/contactos_50.csv", "assistant_synthetic/emails_hilos.md"], ["responsable", "fecha limite", "cliente", "prioridad"]),
    ("test-28", "Investigacion web y propuesta CRM para BravoSoft", 5, ["web_search", "email_drafting", "business_analysis"], ["assistant_synthetic/emails_hilos.md", "assistant_synthetic/contactos_50.csv"], ["BravoSoft", "CRM", "Paula Ferrer", "fuentes"]),
    ("test-29", "Informe mensual combinado operaciones-finanzas", 5, ["multi_file_analysis", "executive_report", "risk_synthesis"], ["assistant_synthetic/notas_voz.jsonl", "assistant_synthetic/emails_hilos.md", "assistant_synthetic/contactos_50.csv", *[f"assistant_synthetic/{name}" for name in EXPENSES]], ["gastos", "tareas pendientes", "clientes prioritarios", "riesgos"]),
    ("test-30", "Investigacion profunda y plan ejecutivo de IA ofimatica", 5, ["web_search", "local_data_crosscheck", "executive_report", "strategy"], ["assistant_synthetic/notas_voz.jsonl", "assistant_synthetic/emails_hilos.md", "assistant_synthetic/contactos_50.csv"], ["OpenRouter", "Gemini", "ofimatica", "coste", "recomendacion ejecutiva"]),
]


TASK_PROMPTS = {
    "test-01": "Revisa `benchmarks/assets/assistant_synthetic/emails_hilos.md` y `benchmarks/assets/assistant_synthetic/contactos_50.csv`. Crea una nota breve con la cita de Clinica Centro: persona, empresa, fecha, hora y objetivo. No inventes datos.",
    "test-02": "Usa `benchmarks/assets/assistant_synthetic/contactos_50.csv` para generar una lista de contactos ubicados en Madrid con prioridad alta. Incluye nombre, empresa, rol y email.",
    "test-03": "Lee `benchmarks/assets/assistant_synthetic/notas_voz.jsonl` y extrae las tareas pendientes en una tabla con id de nota, accion, entidad relacionada y posible fecha limite.",
    "test-04": "Con `benchmarks/assets/assistant_synthetic/emails_hilos.md` y `benchmarks/assets/assistant_synthetic/contactos_50.csv`, redacta un email breve y amable a Paula Ferrer para seguimiento de la propuesta CRM.",
    "test-05": "Audita `benchmarks/assets/assistant_synthetic/gastos_2026_02.csv` e identifica la discrepancia de importe. Devuelve concepto, importe declarado, importe esperado y recomendacion.",
    "test-06": "Cruza `emails_hilos.md` y `notas_voz.jsonl` para preparar una agenda de viaje a Barcelona relacionada con Barna Health. Incluye motivo, fecha, hora y contacto.",
    "test-07": "Extrae la preferencia de formato de informes de Nova Iberia usando `emails_hilos.md` y confirma el contacto correcto en `contactos_50.csv`.",
    "test-08": "Genera un resumen semanal de tareas pendientes a partir de `notas_voz.jsonl` y `emails_hilos.md`, priorizando compromisos con fecha o cliente concreto.",
    "test-09": "Analiza `gastos_2026_03.csv` y detecta cargos duplicados. Calcula el impacto economico y la accion recomendada.",
    "test-10": "Desde `contactos_50.csv`, crea un CSV de proveedores con columnas Nombre, Empresa, Rol, Email, Ciudad y Prioridad.",
    "test-11": "Lista los clientes con prioridad alta en `contactos_50.csv`. Agrupa por ciudad y recomienda tres acciones comerciales.",
    "test-12": "Prepara una minuta de revision del contrato de IberLegal usando `emails_hilos.md` y `notas_voz.jsonl`. Incluye fecha limite y puntos de riesgo.",
    "test-13": "Audita los gastos de enero, febrero y marzo en los CSV correspondientes. Resume discrepancias, duplicados y partidas limpias.",
    "test-14": "A partir de `notas_voz.jsonl` y `emails_hilos.md`, crea el contenido de un archivo ICS con cuatro compromisos claros. Si falta algun dato, indicalo en descripcion.",
    "test-15": "Cruza notas de voz con contactos para identificar personas mencionadas y sus empresas. Devuelve una tabla con tarea, persona, empresa y email.",
    "test-16": "Prepara un briefing para Sergio Campos de Innotek sobre riesgos de seguridad y auditoria usando los recursos locales disponibles.",
    "test-17": "Agrega los gastos de enero a mayo. Calcula total por mes, categorias principales y lista de anomalias.",
    "test-18": "Segmenta los contactos tipo prospecto para una campana. Incluye empresa, ciudad, responsable sugerido y motivo de prioridad.",
    "test-19": "Convierte las referencias a implantacion y formacion en un plan de seguimiento con hitos, responsables y dependencias.",
    "test-20": "Elabora un informe de incidencias y oportunidades para Clinica Centro usando notas, emails y contactos.",
    "test-21": "Usa busqueda web y `notas_voz.jsonl` para proponer alternativas economicas a una herramienta de encuestas para GreenBox. Incluye fuentes.",
    "test-22": "Usa busqueda web para comparar el rendimiento de Apple y Microsoft en los ultimos seis meses. Cruza el resultado con la nota de voz que lo solicita.",
    "test-23": "Investiga opciones actuales de SSO adecuadas para Barna Health. Usa datos locales para contextualizar contacto, fecha y necesidad tecnica.",
    "test-24": "Valida si el descuento del 4% ofrecido por Delta Equipos para monitores 27 parece competitivo frente a referencias web actuales.",
    "test-25": "Genera un informe ejecutivo de cuentas prioritarias combinando contactos, correos y notas. Debe incluir riesgos y siguientes acciones.",
    "test-26": "Audita todos los gastos de enero a mayo y genera recomendaciones de control interno para evitar duplicados, recibos faltantes y discrepancias.",
    "test-27": "Crea un tablero de acciones por responsable combinando notas de voz, correos y contactos. Incluye prioridad y fecha limite cuando exista.",
    "test-28": "Investiga opciones actuales de CRM para pymes y redacta una propuesta de seguimiento para BravoSoft usando el contexto local de Paula Ferrer.",
    "test-29": "Elabora un informe mensual combinado de operaciones y finanzas cruzando contactos, emails, notas y gastos. Debe separar hechos locales, riesgos e inferencias.",
    "test-30": "Investiga el estado actual de herramientas de IA para ofimatica y agentes CLI. Cruza esa investigacion con los datos locales sobre OpenRouter/Gemini y genera una recomendacion ejecutiva.",
}


def main() -> int:
    ASSET_ROOT.mkdir(parents=True, exist_ok=True)
    SUITE_ROOT.mkdir(parents=True, exist_ok=True)
    write_contacts()
    write_voice_notes()
    write_email_threads()
    write_expenses()
    write_tests()
    write_index()
    print(f"resources={ASSET_ROOT}")
    print(f"tests={SUITE_ROOT}")
    print(f"count={len(TASKS)}")
    return 0


def write_contacts() -> None:
    path = ASSET_ROOT / "contactos_50.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["nombre", "email", "telefono", "ciudad", "empresa", "rol", "tipo", "prioridad"])
        writer.writerows(CONTACTS)


def write_voice_notes() -> None:
    path = ASSET_ROOT / "notas_voz.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for note_id, timestamp, text in VOICE_NOTES:
            handle.write(json.dumps({"id": note_id, "timestamp": timestamp, "transcript": text}, ensure_ascii=False) + "\n")


def write_email_threads() -> None:
    (ASSET_ROOT / "emails_hilos.md").write_text(EMAIL_THREADS, encoding="utf-8")


def write_expenses() -> None:
    for filename, rows in EXPENSES.items():
        with (ASSET_ROOT / filename).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["fecha", "concepto", "categoria", "importe_declarado", "importe_esperado", "estado"])
            writer.writerows(rows)


def write_tests() -> None:
    for test_id, title, difficulty, skills, required_files, expected_keys in TASKS:
        folder = SUITE_ROOT / test_id
        folder.mkdir(parents=True, exist_ok=True)
        task_text = f"# {title}\n\n{TASK_PROMPTS[test_id]}\n"
        (folder / "task.md").write_text(task_text, encoding="utf-8")
        metadata = {
            "id": test_id,
            "title": title,
            "required_files": required_files,
            "skills": skills,
            "difficulty": difficulty,
            "expected_keys": expected_keys,
        }
        (folder / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def write_index() -> None:
    titles = [{"id": test_id, "title": title, "difficulty": difficulty} for test_id, title, difficulty, _, _, _ in TASKS]
    (SUITE_ROOT / "index.json").write_text(json.dumps(titles, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
