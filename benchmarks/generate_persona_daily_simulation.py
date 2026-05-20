from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ASSET_DIR = ROOT / "assets" / "persona_daily_simulation"
TASKS_FILE = ROOT / "tasks" / "persona_daily_tasks.json"
REPORT_FILE = ROOT / "results" / "persona_daily_simulation_strategy.html"


PERSONAS = [
    {
        "id": "p01_inmobiliaria",
        "name": "Clara Benavides",
        "profession": "Agente inmobiliaria",
        "tone": "directa, comercial, muy orientada a cerrar visitas",
        "daily_tools": ["agenda", "email", "CRM", "comparativa de inmuebles"],
        "risk": "Puede mezclar datos de inmuebles parecidos si la respuesta no cita fuente local.",
    },
    {
        "id": "p02_informatico",
        "name": "Nicolas Ortega",
        "profession": "Responsable informatico / DevOps",
        "tone": "tecnico, conciso, pide pasos ejecutables",
        "daily_tools": ["tickets", "logs", "scripts", "documentacion tecnica"],
        "risk": "Necesita distinguir diagnostico probable de accion destructiva.",
    },
    {
        "id": "p03_cientifica",
        "name": "Dra. Irene Salvatierra",
        "profession": "Cientifica biomedica",
        "tone": "prudente, metodica, pide trazabilidad",
        "daily_tools": ["notas de laboratorio", "papers", "tablas", "resumen ejecutivo"],
        "risk": "No debe inventar resultados ni referencias.",
    },
    {
        "id": "p04_ingeniero",
        "name": "Marcos Valcarce",
        "profession": "Ingeniero industrial",
        "tone": "operativo, orientado a costes, seguridad y plazos",
        "daily_tools": ["partes de obra", "presupuestos", "checklists", "planificacion"],
        "risk": "Requiere calculos transparentes y alertas de seguridad.",
    },
    {
        "id": "p05_abogada",
        "name": "Laura Montalban",
        "profession": "Abogada laboralista",
        "tone": "formal, precisa, evita afirmaciones juridicas tajantes",
        "daily_tools": ["contratos", "emails", "plazos", "minutas"],
        "risk": "Debe separar resumen documental de asesoramiento legal definitivo.",
    },
    {
        "id": "p06_finanzas",
        "name": "Hector Rivas",
        "profession": "Consultor financiero para pymes",
        "tone": "ejecutivo, numerico, con foco en caja y riesgo",
        "daily_tools": ["CSV", "facturas", "reportes", "email ejecutivo"],
        "risk": "Los totales y discrepancias tienen que cuadrar.",
    },
]


MESSAGES = [
    ("msg-001", "p01_inmobiliaria", "2026-05-18 08:12", "Busca en mis inmuebles cual puedo ensenar hoy a una pareja con presupuesto 310k, 3 dormitorios y colegio cerca. Mandame un resumen para WhatsApp.", "L2", ["Piso Olivo", "305000", "3 dormitorios", "Colegio Albor"], ["data_filtering", "client_response"]),
    ("msg-002", "p01_inmobiliaria", "2026-05-18 11:40", "El cliente de ayer pregunta si el atico de Ronda Norte acepta rebaja. Mira notas y prepara respuesta prudente, sin prometer nada.", "L2", ["Atico Ronda Norte", "385000", "margen 2%", "no prometer"], ["synthesis", "tone_control"]),
    ("msg-003", "p01_inmobiliaria", "2026-05-19 09:05", "Tengo 4 visitas el jueves. Ordenamelas por zona y dame ruta logica empezando en la oficina.", "L3", ["jueves", "Centro", "Ronda Norte", "Vallecas", "ruta"], ["planning", "agenda"]),
    ("msg-004", "p01_inmobiliaria", "2026-05-19 16:22", "Redacta email a propietario de Local Sur explicando por que no conviene subir el precio ahora.", "L3", ["Local Sur", "precio", "demanda baja", "email"], ["email_drafting", "market_reasoning"]),
    ("msg-005", "p01_inmobiliaria", "2026-05-20 10:15", "Compara mis tres mejores opciones para inversor: rentabilidad, reforma y riesgo de vacancia.", "L4", ["rentabilidad", "reforma", "vacancia", "recomendacion"], ["comparison", "financial_reasoning"]),
    ("msg-006", "p01_inmobiliaria", "2026-05-20 18:45", "Genera un informe semanal de oportunidades y avisos urgentes para manana.", "L4", ["oportunidades", "avisos", "visitas", "propietarios"], ["executive_report", "prioritization"]),
    ("msg-007", "p02_informatico", "2026-05-18 07:55", "Mira los logs sinteticos y dime por que puede estar fallando el login de clientes desde las 7:30.", "L2", ["login", "07:31", "timeout OAuth", "clientes"], ["log_analysis", "incident_triage"]),
    ("msg-008", "p02_informatico", "2026-05-18 12:05", "Prepara un mensaje para soporte explicando la incidencia sin asustar al equipo comercial.", "L2", ["incidencia", "OAuth", "sin perdida de datos", "equipo comercial"], ["communication", "tone_control"]),
    ("msg-009", "p02_informatico", "2026-05-19 08:30", "Haz checklist para rotar la clave API del proveedor SSO sin romper produccion.", "L3", ["backup", "staging", "rollback", "ventana"], ["technical_planning", "risk_control"]),
    ("msg-010", "p02_informatico", "2026-05-19 15:00", "Convierte los tickets pendientes en una tabla por prioridad y responsable.", "L3", ["TCK-104", "alta", "Marta", "responsable"], ["data_extraction", "table_generation"]),
    ("msg-011", "p02_informatico", "2026-05-20 09:20", "Escribe un pequeno script o pseudocodigo para detectar errores 5xx por minuto en access.log.", "L4", ["5xx", "por minuto", "access.log", "script"], ["code_generation", "log_analysis"]),
    ("msg-012", "p02_informatico", "2026-05-20 17:40", "Informe postmortem corto: causa, impacto, mitigacion y acciones preventivas.", "L4", ["causa", "impacto", "mitigacion", "acciones preventivas"], ["incident_report", "synthesis"]),
    ("msg-013", "p03_cientifica", "2026-05-18 08:40", "Resume las notas de laboratorio de la semana y separa observaciones de hipotesis.", "L2", ["observaciones", "hipotesis", "muestra B17", "control"], ["summarization", "scientific_caution"]),
    ("msg-014", "p03_cientifica", "2026-05-18 13:10", "Prepara email al comite pidiendo ampliar muestra, con tono prudente.", "L2", ["comite", "ampliar muestra", "prudente", "B17"], ["email_drafting", "tone_control"]),
    ("msg-015", "p03_cientifica", "2026-05-19 10:35", "Ordena resultados por marcador y senala anomalias sin concluir causalidad.", "L3", ["IL-6", "CRP", "anomalia", "sin causalidad"], ["data_analysis", "scientific_caution"]),
    ("msg-016", "p03_cientifica", "2026-05-19 18:05", "Haz una lista de preguntas para discutir con estadistica antes de enviar abstract.", "L3", ["potencia", "sesgo", "outliers", "abstract"], ["planning", "research_methods"]),
    ("msg-017", "p03_cientifica", "2026-05-20 09:00", "Cruza notas y tabla de resultados para preparar resumen ejecutivo de 1 pagina.", "L4", ["muestra B17", "marcadores", "limitaciones", "siguiente paso"], ["multi_file_analysis", "executive_report"]),
    ("msg-018", "p03_cientifica", "2026-05-20 16:55", "Necesito un briefing para direccion: que sabemos, que no sabemos y decision recomendada.", "L4", ["sabemos", "no sabemos", "decision", "riesgo"], ["decision_brief", "synthesis"]),
    ("msg-019", "p04_ingeniero", "2026-05-18 07:30", "Revisa el parte de obra y dime que dos riesgos debo mirar hoy primero.", "L2", ["vibracion", "suministro", "seguridad", "prioridad"], ["risk_detection", "prioritization"]),
    ("msg-020", "p04_ingeniero", "2026-05-18 12:30", "Redacta aviso para el proveedor por retraso de valvulas sin romper la relacion.", "L2", ["valvulas", "retraso", "proveedor", "tono firme"], ["email_drafting", "operations"]),
    ("msg-021", "p04_ingeniero", "2026-05-19 08:15", "Calcula desviacion de coste entre presupuesto y real de los ultimos hitos.", "L3", ["Hito 2", "desviacion", "coste real", "presupuesto"], ["cost_analysis", "calculation"]),
    ("msg-022", "p04_ingeniero", "2026-05-19 14:45", "Prepara checklist de seguridad para la visita de inspeccion del miercoles.", "L3", ["EPI", "bloqueo", "senalizacion", "miercoles"], ["checklist", "safety"]),
    ("msg-023", "p04_ingeniero", "2026-05-20 11:10", "Dame plan de recuperacion si las valvulas llegan 3 dias tarde.", "L4", ["3 dias", "plan B", "hitos", "impacto"], ["contingency_planning", "operations"]),
    ("msg-024", "p04_ingeniero", "2026-05-20 19:05", "Haz informe para direccion con estado, desviaciones y decisiones pendientes.", "L4", ["estado", "desviaciones", "decisiones pendientes", "direccion"], ["executive_report", "project_control"]),
    ("msg-025", "p05_abogada", "2026-05-18 09:10", "Resume este hilo del despido disciplinario y dime que documentos faltan.", "L2", ["despido disciplinario", "carta", "pruebas", "documentos faltan"], ["legal_summary", "document_check"]),
    ("msg-026", "p05_abogada", "2026-05-18 13:35", "Prepara respuesta al cliente: formal, sin prometer resultado judicial.", "L2", ["formal", "sin prometer", "plazos", "documentacion"], ["email_drafting", "legal_caution"]),
    ("msg-027", "p05_abogada", "2026-05-19 10:00", "Extrae plazos y riesgos de los contratos pendientes.", "L3", ["plazos", "riesgos", "renovacion", "periodo prueba"], ["contract_review", "risk_extraction"]),
    ("msg-028", "p05_abogada", "2026-05-19 17:25", "Haz minuta de reunion para mediacion laboral con puntos no negociables.", "L3", ["mediacion", "no negociables", "indemnizacion", "confidencialidad"], ["meeting_brief", "legal_summary"]),
    ("msg-029", "p05_abogada", "2026-05-20 08:50", "Compara dos borradores de clausula y senala cual es menos arriesgado.", "L4", ["clausula A", "clausula B", "menos arriesgado", "motivo"], ["comparison", "legal_risk"]),
    ("msg-030", "p05_abogada", "2026-05-20 18:15", "Informe semanal de expedientes: urgencias, bloqueos y siguiente accion.", "L4", ["urgencias", "bloqueos", "siguiente accion", "expedientes"], ["executive_report", "prioritization"]),
    ("msg-031", "p06_finanzas", "2026-05-18 08:25", "Mira facturas y cobros: dime que cliente esta generando tension de caja.", "L2", ["tension de caja", "Norte SA", "847.50", "vencido"], ["financial_analysis", "data_extraction"]),
    ("msg-032", "p06_finanzas", "2026-05-18 12:20", "Redacta email amable reclamando factura vencida sin sonar agresivo.", "L2", ["factura vencida", "Norte SA", "amable", "fecha"], ["email_drafting", "collections"]),
    ("msg-033", "p06_finanzas", "2026-05-19 09:15", "Agrupa gastos por categoria y marca anomalias.", "L3", ["software", "viajes", "anomalias", "duplicado"], ["aggregation", "expense_audit"]),
    ("msg-034", "p06_finanzas", "2026-05-19 16:00", "Haz prevision de caja sencilla para 14 dias con supuestos claros.", "L3", ["14 dias", "supuestos", "cobros", "pagos"], ["forecasting", "financial_reasoning"]),
    ("msg-035", "p06_finanzas", "2026-05-20 10:40", "Crea un resumen para direccion con tres medidas para mejorar caja este mes.", "L4", ["mejorar caja", "tres medidas", "direccion", "prioridad"], ["executive_report", "recommendations"]),
    ("msg-036", "p06_finanzas", "2026-05-20 17:35", "Cruza facturas, cobros y gastos para detectar riesgos financieros y acciones.", "L4", ["facturas", "cobros", "gastos", "riesgos financieros"], ["multi_file_analysis", "financial_risk"]),
]


KNOWLEDGE_BASE = """# Base sintetica de uso diario

## Inmobiliaria
- Piso Olivo: 305000 EUR, 3 dormitorios, 2 banos, cerca de Colegio Albor, zona Centro, disponible jueves 10:00.
- Atico Ronda Norte: 385000 EUR, 2 dormitorios, terraza, margen de negociacion maximo 2%, propietario sensible a rebajas.
- Casa Vallecas: 298000 EUR, 3 dormitorios, necesita reforma media, buena rentabilidad estimada.
- Local Sur: 210000 EUR, demanda baja en la zona, recomendacion interna: no subir precio hasta tener mas visitas.

## Informatica
- access.log sintetico: 07:31-07:49 aumentan errores 502/504 en /login/clientes por timeout OAuth.
- Tickets: TCK-104 alta Marta login clientes; TCK-107 media Raul certificados; TCK-111 baja Ana limpieza logs.
- Rotacion SSO: probar primero en staging, guardar clave anterior, ventana de bajo trafico, rollback documentado.

## Ciencia
- Notas laboratorio: muestra B17 presenta IL-6 elevada frente a control; CRP moderada; n=18, potencia insuficiente para causalidad.
- Outliers: dos mediciones de B17 fuera de rango por posible demora en procesamiento.
- Decision recomendada: ampliar muestra antes de comunicar conclusiones fuertes.

## Ingenieria
- Parte obra: vibracion alta en bomba secundaria; valvulas proveedor Norteval con retraso probable de 3 dias.
- Costes: Hito 2 presupuestado 18400 EUR, real 19780 EUR; Hito 3 presupuestado 22600 EUR, real 22150 EUR.
- Seguridad: revisar EPI, bloqueo electrico, senalizacion y acceso de visitas.

## Legal
- Expediente despido disciplinario: falta carta firmada, registro horario y pruebas documentales completas.
- Contratos: riesgo en renovacion automatica y periodo de prueba ambiguo.
- Mediacion: puntos no negociables: confidencialidad, calendario de pago, no reconocimiento de hechos no probados.
- Clausula A limita responsabilidad con redaccion clara; clausula B contiene ambiguedad de alcance.

## Finanzas
- Facturas: Norte SA debe 847.50 EUR vencidos hace 12 dias; Duero Apps paga en plazo; Orion Retail tiene vencimiento en 5 dias.
- Gastos: duplicado de hotel en marzo; software IA 120 EUR pendiente de revisar proveedor.
- Supuesto de caja: saldo inicial 6200 EUR; cobros probables 3400 EUR; pagos comprometidos 5100 EUR en 14 dias.
"""


def main() -> int:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    (ASSET_DIR / "personas.json").write_text(json.dumps(PERSONAS, ensure_ascii=False, indent=2), encoding="utf-8")
    (ASSET_DIR / "telegram_messages.jsonl").write_text(
        "\n".join(json.dumps(message_to_dict(row), ensure_ascii=False) for row in MESSAGES) + "\n",
        encoding="utf-8",
    )
    (ASSET_DIR / "knowledge_base.md").write_text(KNOWLEDGE_BASE, encoding="utf-8")
    (ASSET_DIR / "README.md").write_text(readme(), encoding="utf-8")

    tasks = [task_from_message(row) for row in MESSAGES]
    TASKS_FILE.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_FILE.write_text(strategy_report(), encoding="utf-8")
    print(TASKS_FILE)
    print(ASSET_DIR)
    print(REPORT_FILE)
    return 0


def message_to_dict(row: tuple[str, str, str, str, str, list[str], list[str]]) -> dict[str, object]:
    msg_id, persona_id, timestamp, text, level, expected_keys, skills = row
    persona = next(item for item in PERSONAS if item["id"] == persona_id)
    return {
        "id": msg_id,
        "persona_id": persona_id,
        "persona_name": persona["name"],
        "profession": persona["profession"],
        "timestamp": timestamp,
        "channel": "telegram",
        "text": text,
        "level": level,
        "expected_keys": expected_keys,
        "skills": skills,
    }


def task_from_message(row: tuple[str, str, str, str, str, list[str], list[str]]) -> dict[str, object]:
    msg_id, persona_id, timestamp, text, level, expected_keys, skills = row
    persona = next(item for item in PERSONAS if item["id"] == persona_id)
    number = int(msg_id.split("-")[1])
    task_id = f"daily-{number:02d}"
    prompt = (
        f"# Telegram diario {msg_id}: {persona['profession']}\n\n"
        "Actua como asistente operativo dentro del sistema. Procesa solo el mensaje indicado y usa los archivos locales vinculados.\n\n"
        f"- Persona: {persona['name']} ({persona['profession']})\n"
        f"- Tono esperado: {persona['tone']}\n"
        f"- Timestamp: {timestamp}\n"
        f"- Mensaje de Telegram: \"{text}\"\n\n"
        "Instrucciones:\n"
        "1. Identifica la intencion real del usuario.\n"
        "2. Consulta `persona_daily_simulation/personas.json`, `persona_daily_simulation/telegram_messages.jsonl` y `persona_daily_simulation/knowledge_base.md`.\n"
        "3. Devuelve una respuesta lista para enviar por Telegram o un entregable breve si la tarea lo pide.\n"
        "4. No inventes datos. Si hay incertidumbre, dilo y propone el siguiente paso.\n"
    )
    return {
        "id": task_id,
        "level": level,
        "category": "persona_daily_telegram",
        "persona_id": persona_id,
        "profession": persona["profession"],
        "source_message_id": msg_id,
        "prompt": prompt,
        "required_files": [
            "persona_daily_simulation/personas.json",
            "persona_daily_simulation/telegram_messages.jsonl",
            "persona_daily_simulation/knowledge_base.md",
        ],
        "expected_outputs": ["resultado.md"],
        "requires_network": False,
        "skills": skills,
        "expected_keys": expected_keys,
        "rubric": {
            "intent_detection": 2,
            "correctness": 3,
            "expected_keys": 2,
            "professional_tone": 2,
            "actionability": 1,
        },
    }


def readme() -> str:
    return """# Persona Daily Simulation

Dataset sintetico de mensajes tipo Telegram para evaluar un asistente diario multi-profesion.

Archivos:
- `personas.json`: seis perfiles profesionales.
- `telegram_messages.jsonl`: 36 mensajes entrantes, seis por persona.
- `knowledge_base.md`: contexto local que sustituye datos privados reales.

Tareas generadas:
- `benchmarks/tasks/persona_daily_tasks.json`

Uso recomendado:
```powershell
python .\\benchmarks\\benchmark_scheduler.py --tasks-file .\\benchmarks\\tasks\\persona_daily_tasks.json --engine codex:gpt-5.4-mini --task daily-01 --once --heuristic-only
```
"""


def strategy_report() -> str:
    persona_rows = "\n".join(
        f"<tr><td>{p['name']}</td><td>{p['profession']}</td><td>{p['tone']}</td><td>{', '.join(p['daily_tools'])}</td><td>{p['risk']}</td></tr>"
        for p in PERSONAS
    )
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Estrategia de simulacion diaria por personas</title>
<style>
body{{margin:0;background:#f6f7fb;color:#172033;font-family:Segoe UI,Arial,sans-serif;line-height:1.45}}
.hero{{background:#18344f;color:white;padding:42px 54px}}.hero h1{{margin:0;font-size:34px}}.hero p{{max-width:980px;color:#d9e7f2}}
.wrap{{max-width:1240px;margin:auto;padding:26px 34px 58px}}.panel{{background:white;border:1px solid #e5e7eb;border-radius:8px;padding:22px;margin:18px 0;box-shadow:0 8px 24px rgba(16,24,40,.05)}}
table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{padding:10px;border-bottom:1px solid #e5e7eb;text-align:left;vertical-align:top}}th{{background:#f2f4f7}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}}.card{{border:1px solid #e5e7eb;border-radius:8px;padding:16px;background:#fff}}
.flow div{{border-left:5px solid #2557a7;padding:12px;background:#f8fafc;border-radius:6px;margin:10px 0}}code{{background:#eef2f7;padding:2px 5px;border-radius:4px}}
</style></head><body>
<section class="hero"><h1>Benchmark de uso diario sintético</h1>
<p>Suite nueva para simular peticiones reales de Telegram hechas por seis perfiles profesionales. El objetivo no es solo medir si un modelo resuelve un ejercicio, sino si sostiene una jornada de trabajo: tono, contexto, acciones, coste, fallos y escalado.</p></section>
<main class="wrap">
<section class="panel"><h2>Perfiles creados</h2><table><thead><tr><th>Persona</th><th>Profesion</th><th>Tono</th><th>Herramientas diarias</th><th>Riesgo evaluado</th></tr></thead><tbody>{persona_rows}</tbody></table></section>
<section class="panel"><h2>Diseno experimental recomendado</h2><div class="flow">
<div><b>Fase 1: baseline barato.</b> Correr 36 mensajes con <code>codex:gpt-5.4-mini</code> para obtener referencia estable.</div>
<div><b>Fase 2: canarios multi-modelo.</b> Correr 6 mensajes representativos con Codex 5.5, Gemini Flash-Lite, Groq Llama y DeepSeek cuando OpenRouter tenga credito.</div>
<div><b>Fase 3: router.</b> Usar un modelo barato para clasificar intencion, dificultad, riesgo, necesidad de herramientas y motor sugerido.</div>
<div><b>Fase 4: produccion simulada.</b> Ejecutar por rondas diarias y comparar coste por tarea aprobada, no solo nota media.</div>
</div></section>
<section class="panel"><h2>Decision: uno o varios modelos</h2>
<p>Para aprender rapido, empieza con un modelo unico estable: <b>Codex 5.4 mini</b>. Para optimizar arquitectura, no corras todo con todos desde el primer dia: usa canarios por profesion y escala solo donde haya incertidumbre. La meta final es un sistema en cascada: router barato, trabajador estandar, validador, escalado premium.</p>
<table><thead><tr><th>Tipo de mensaje</th><th>Primera opcion</th><th>Escalado</th></tr></thead><tbody>
<tr><td>Respuesta breve, extraccion simple</td><td>Gemini Flash-Lite o Groq Llama</td><td>Codex 5.4 mini</td></tr>
<tr><td>Archivos, planificacion, tono profesional</td><td>Codex 5.4 mini</td><td>Codex 5.5</td></tr>
<tr><td>Calculos o informe con riesgos</td><td>Codex 5.4 mini</td><td>Codex 5.5 / Gemini Pro</td></tr>
<tr><td>Contexto largo barato</td><td>DeepSeek V4 Flash pendiente de credito</td><td>Gemini Flash/Pro</td></tr>
</tbody></table></section>
<section class="panel"><h2>Archivos generados</h2>
<ul><li><code>benchmarks/assets/persona_daily_simulation/personas.json</code></li><li><code>benchmarks/assets/persona_daily_simulation/telegram_messages.jsonl</code></li><li><code>benchmarks/assets/persona_daily_simulation/knowledge_base.md</code></li><li><code>benchmarks/tasks/persona_daily_tasks.json</code></li></ul>
</section></main></body></html>"""


if __name__ == "__main__":
    raise SystemExit(main())
