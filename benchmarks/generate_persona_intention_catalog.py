from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TASKS_FILE = ROOT / "tasks" / "persona_intention_tasks.json"
ASSET_DIR = ROOT / "assets" / "persona_intention_catalog"
REVIEW_FILE = ROOT / "PERSONA_INTENTION_REVIEW_PACK.md"
DESIGN_FILE = ROOT / "PERSONA_INTENTION_CATALOG.md"


DIMENSIONS = {
    "context_scope": ["small", "medium", "large", "cross_project"],
    "data_mode": ["conversation", "documents", "tables", "logs", "mixed", "web_fresh"],
    "tool_need": ["none", "read_files", "create_file", "code_execution", "web_search", "calendar", "multi_tool"],
    "risk": ["low", "medium", "high", "critical"],
    "output_form": ["short_reply", "email", "table", "checklist", "plan", "report", "script", "calendar", "data_file"],
    "reasoning_shape": ["retrieve", "extract", "compare", "calculate", "synthesize", "diagnose", "decide", "draft"],
    "freshness": ["static_local", "recent_local", "current_web"],
    "error_tolerance": ["high", "medium", "low", "near_zero"],
}


PROFESSIONS = [
    ("inmobiliaria", "Agente inmobiliaria", "clientes compradores, propietarios, visitas, fichas de inmuebles, rutas, negociaciones"),
    ("informatico", "Responsable informatico / DevOps", "tickets, logs, incidencias, proveedores SaaS, seguridad, despliegues"),
    ("cientifica", "Cientifica biomedica", "notas de laboratorio, resultados preliminares, comite etico, estadistica, direccion"),
    ("ingeniero", "Ingeniero industrial", "partes de obra, proveedores, seguridad, costes, hitos, inspecciones"),
    ("abogada", "Abogada laboralista", "clientes, contratos, plazos, expedientes, mediaciones, riesgos juridicos"),
    ("finanzas", "Consultor financiero para pymes", "facturas, cobros, gastos, caja, clientes morosos, direccion"),
]


BASE_CONTEXT = {
    "inmobiliaria": [
        "Oficina: Calle Mayor 18, Madrid.",
        "Piso Olivo: Calle Olivo 14, 305000 EUR, 3 dormitorios, Colegio Albor a 350 m.",
        "Atico Ronda Norte: Ronda Norte 22, 385000 EUR, margen maximo 2%, minimo recomendado 377000 EUR.",
        "Casa Vallecas: Avenida de la Albufera 210, 298000 EUR, reforma estimada 18000 EUR.",
        "Local Sur: Calle Puerto Rico 7, 210000 EUR, tres semanas sin visitas cualificadas.",
    ],
    "informatico": [
        "portal-clientes gestiona login y facturas.",
        "AuthNova es proveedor SSO; /oauth/token tuvo latencia de 4800 ms.",
        "TCK-104 alta: login clientes, Marta.",
        "TCK-107 media: certificado staging, Raul.",
        "TCK-111 baja: limpieza logs, Ana.",
    ],
    "cientifica": [
        "Ensayo piloto B17, n=18.",
        "IL-6 media 8.4 en B17 frente a 5.1 control.",
        "CRP media 3.2 frente a 2.9 control.",
        "Outliers B17-06 y B17-14 por posible demora.",
        "No afirmar causalidad; pedir ampliacion de muestra.",
    ],
    "ingeniero": [
        "Planta Norte, Poligono 4, nave 12.",
        "Bomba secundaria con vibracion alta.",
        "Cuadro electrico C2 requiere bloqueo antes de inspeccion.",
        "Hito 2: presupuesto 18400, real 19780.",
        "Norteval puede retrasar valvulas 3 dias.",
    ],
    "abogada": [
        "DES-24: despido disciplinario; faltan carta firmada, registro horario y pruebas completas.",
        "CON-18: renovacion automatica ambigua.",
        "MED-07: mediacion; confidencialidad, calendario de pago y no reconocimiento de hechos no probados.",
        "Clausula A: alcance concreto.",
        "Clausula B: obligaciones posteriores ambiguas.",
    ],
    "finanzas": [
        "Saldo inicial 6200 EUR.",
        "Cobros probables 14 dias: 3400 EUR.",
        "Pagos comprometidos 14 dias: 5100 EUR.",
        "Norte SA debe F-118 por 847.50 EUR, vencida hace 12 dias.",
        "Marzo tiene duplicado hotel 210 EUR; mayo software IA 120 EUR pendiente.",
    ],
}


TASKS_BY_PROFESSION = {
    "inmobiliaria": [
        ("Seleccionar inmueble para comprador con presupuesto 310000 EUR, 3 dormitorios y colegio cercano.", ["Piso Olivo", "305000", "3 dormitorios", "Colegio Albor"], "short_reply", "compare", "medium"),
        ("Ordenar ruta de visitas desde Calle Mayor 18 incluyendo direcciones concretas y hora sugerida.", ["Calle Mayor 18", "Calle Olivo 14", "Ronda Norte 22", "ruta"], "plan", "decide", "medium"),
        ("Preparar respuesta prudente para oferta baja sobre Atico Ronda Norte sin prometer aceptacion.", ["Atico Ronda Norte", "2%", "377000", "prudente"], "short_reply", "draft", "medium"),
        ("Redactar email a propietario de Local Sur explicando por que no conviene subir precio.", ["Local Sur", "210000", "tres semanas", "visitas"], "email", "draft", "medium"),
        ("Comparar Casa Vallecas y Piso Olivo para inversor tolerante a reforma.", ["Casa Vallecas", "Piso Olivo", "18000", "reforma"], "table", "compare", "high"),
        ("Crear lista de objeciones de compradores y respuestas comerciales no agresivas.", ["objeciones", "compradores", "respuestas", "tono"], "table", "synthesize", "medium"),
        ("Preparar resumen semanal de oportunidades calientes y propietarios a llamar.", ["oportunidades", "propietarios", "llamar", "semana"], "report", "synthesize", "medium"),
        ("Generar mensaje de WhatsApp para confirmar visita con datos de inmueble y condiciones.", ["WhatsApp", "visita", "inmueble", "confirmar"], "short_reply", "draft", "medium"),
        ("Crear tabla de inmuebles con precio, direccion, perfil de cliente y siguiente accion.", ["precio", "direccion", "cliente", "siguiente accion"], "table", "extract", "medium"),
        ("Detectar que datos faltan antes de contestar a comprador extranjero.", ["comprador extranjero", "datos faltan", "email", "claridad"], "checklist", "extract", "medium"),
        ("Preparar comparativa para negociar rebaja sin danar relacion con propietario.", ["rebaja", "propietario", "comparativa", "negociar"], "report", "decide", "high"),
        ("Crear agenda diaria de llamadas a propietarios y compradores por prioridad.", ["agenda", "llamadas", "prioridad", "propietarios"], "plan", "decide", "medium"),
        ("Convertir notas de visita en CRM: interes, objeciones, presupuesto y proxima accion.", ["CRM", "interes", "objeciones", "proxima accion"], "data_file", "extract", "medium"),
        ("Redactar email a comprador que descarta inmueble por colegio, proponiendo alternativa.", ["colegio", "alternativa", "comprador", "email"], "email", "draft", "medium"),
        ("Preparar informe de precios de zona usando datos locales y fuente web actual.", ["precios", "zona", "fuente", "web"], "report", "compare", "high", "web_search"),
        ("Priorizar captaciones de inmuebles segun demanda, precio y urgencia del propietario.", ["captaciones", "demanda", "precio", "urgencia"], "table", "decide", "high"),
        ("Crear guion de llamada para propietario susceptible que quiere subir precio.", ["guion", "propietario", "subir precio", "susceptible"], "checklist", "draft", "medium"),
        ("Calcular impacto de rebaja del 2% en Atico Ronda Norte.", ["2%", "Atico Ronda Norte", "385000", "impacto"], "table", "calculate", "medium"),
        ("Preparar briefing de 1 pagina para reunion comercial semanal.", ["briefing", "comercial", "semana", "acciones"], "report", "synthesize", "medium"),
        ("Crear archivo CSV de seguimiento de visitas con inmueble, cliente, estado y siguiente accion.", ["CSV", "visitas", "estado", "siguiente accion"], "data_file", "extract", "medium"),
    ],
    "informatico": [
        ("Diagnosticar si fallo de login viene de AuthNova o portal-clientes usando logs.", ["login", "AuthNova", "portal-clientes", "logs"], "short_reply", "diagnose", "high"),
        ("Redactar aviso a comercial sobre incidencia sin generar alarma.", ["comercial", "incidencia", "sin perdida de datos", "aviso"], "short_reply", "draft", "medium"),
        ("Crear runbook para rotar clave API SSO con staging, rollback y validacion.", ["runbook", "staging", "rollback", "validacion"], "checklist", "decide", "high"),
        ("Convertir tickets TCK-104, TCK-107 y TCK-111 en tabla por prioridad y responsable.", ["TCK-104", "TCK-107", "TCK-111", "responsable"], "table", "extract", "medium"),
        ("Generar script para contar errores 5xx por minuto en access.log.", ["script", "5xx", "access.log", "minuto"], "script", "calculate", "medium", "code_execution"),
        ("Preparar postmortem con causa probable, impacto, mitigacion y prevencion.", ["postmortem", "causa", "impacto", "mitigacion"], "report", "diagnose", "high"),
        ("Crear checklist previo a despliegue con pruebas de login, rollback y monitorizacion.", ["despliegue", "login", "rollback", "monitorizacion"], "checklist", "decide", "high"),
        ("Resumir logs para direccion en lenguaje no tecnico.", ["logs", "direccion", "no tecnico", "resumen"], "report", "synthesize", "medium"),
        ("Extraer de una nota larga todas las acciones tecnicas y dependencias.", ["acciones", "dependencias", "tecnicas", "nota"], "table", "extract", "medium"),
        ("Preparar respuesta al proveedor SSO pidiendo RCA y tiempos de resolucion.", ["proveedor SSO", "RCA", "tiempos", "resolucion"], "email", "draft", "medium"),
        ("Clasificar incidencia como aplicacion, proveedor, red o usuario con evidencia.", ["aplicacion", "proveedor", "red", "evidencia"], "table", "diagnose", "high"),
        ("Crear plan de guardia para incidencias fuera de horario.", ["guardia", "incidencias", "horario", "plan"], "plan", "decide", "medium"),
        ("Detectar tareas automatizables en soporte interno.", ["automatizables", "soporte", "interno", "tareas"], "report", "synthesize", "medium"),
        ("Preparar documentacion breve para renovar certificado staging.", ["certificado", "staging", "renovar", "documentacion"], "checklist", "extract", "medium"),
        ("Buscar alternativas de monitorizacion y comparar coste, cobertura y riesgo.", ["monitorizacion", "coste", "cobertura", "riesgo"], "report", "compare", "high", "web_search"),
        ("Generar CSV de tickets con prioridad, responsable, fecha objetivo y bloqueo.", ["CSV", "tickets", "prioridad", "bloqueo"], "data_file", "extract", "medium"),
        ("Redactar mensaje de seguimiento tras recuperar servicio.", ["seguimiento", "servicio", "recuperar", "mensaje"], "short_reply", "draft", "medium"),
        ("Calcular duracion estimada de degradacion entre primer y ultimo error.", ["duracion", "degradacion", "primer error", "ultimo error"], "table", "calculate", "high"),
        ("Crear matriz de riesgos de seguridad para cambios SSO.", ["riesgos", "seguridad", "SSO", "matriz"], "table", "decide", "high"),
        ("Preparar informe semanal de incidencias y deuda tecnica.", ["informe semanal", "incidencias", "deuda tecnica", "acciones"], "report", "synthesize", "medium"),
    ],
}


def clone_for_missing_professions() -> None:
    templates = {
        "cientifica": ("B17", "comite", "muestra", "causalidad"),
        "ingeniero": ("Planta Norte", "Norteval", "seguridad", "hitos"),
        "abogada": ("DES-24", "cliente", "plazos", "riesgo"),
        "finanzas": ("Norte SA", "caja", "facturas", "riesgo financiero"),
    }
    for profession, words in templates.items():
        if profession in TASKS_BY_PROFESSION:
            continue
        a, b, c, d = words
        TASKS_BY_PROFESSION[profession] = [
            (f"Extraer de una nota larga los hechos importantes sobre {a}.", [a, "hechos", c, d], "table", "extract", "high"),
            (f"Redactar respuesta profesional relacionada con {b} sin prometer mas de lo que se sabe.", [b, "respuesta", "prudente", d], "email", "draft", "high"),
            (f"Preparar plan de accion con prioridades, responsables y dudas abiertas sobre {a}.", [a, "prioridades", "responsables", "dudas"], "plan", "decide", "high"),
            (f"Crear informe para direccion con contexto, riesgos y decision recomendada.", ["direccion", "riesgos", "decision", a], "report", "synthesize", "high"),
            (f"Convertir informacion dispersa en tabla estructurada de seguimiento.", ["tabla", "seguimiento", c, d], "table", "extract", "medium"),
            (f"Detectar inconsistencias o datos faltantes antes de contestar.", ["inconsistencias", "datos faltantes", "contestar", a], "checklist", "diagnose", "high"),
            (f"Calcular impacto numerico a partir de datos de la nota y documentos.", ["calcular", "impacto", "datos", a], "table", "calculate", "high"),
            (f"Preparar checklist operativo para no olvidar pasos criticos.", ["checklist", "pasos criticos", c, d], "checklist", "decide", "high"),
            (f"Resumir para un destinatario no tecnico manteniendo cautelas.", ["resumir", "no tecnico", "cautelas", a], "short_reply", "synthesize", "medium"),
            (f"Generar archivo CSV con campos clave extraidos de la informacion.", ["CSV", "campos clave", "extraidos", a], "data_file", "extract", "medium"),
            (f"Preparar preguntas de aclaracion para desbloquear la tarea.", ["preguntas", "aclaracion", "desbloquear", a], "checklist", "decide", "medium"),
            (f"Comparar dos opciones y recomendar una con cautelas.", ["comparar", "recomendar", "cautelas", d], "report", "compare", "high"),
            (f"Crear mensaje corto de seguimiento para confirmar datos pendientes.", ["mensaje", "seguimiento", "datos pendientes", b], "short_reply", "draft", "medium"),
            (f"Ordenar cronologicamente eventos mencionados en una nota larga.", ["cronologia", "eventos", "nota", a], "table", "extract", "medium"),
            (f"Buscar informacion actual externa y cruzarla con datos locales.", ["informacion actual", "fuente", "datos locales", a], "report", "compare", "high", "web_search"),
            (f"Preparar resumen semanal de bloqueos y siguientes acciones.", ["resumen semanal", "bloqueos", "acciones", a], "report", "synthesize", "medium"),
            (f"Separar hechos, opiniones, hipotesis y decisiones pendientes.", ["hechos", "opiniones", "hipotesis", "decisiones"], "table", "extract", "high"),
            (f"Crear guion de llamada para obtener informacion que falta.", ["guion", "llamada", "informacion que falta", b], "checklist", "draft", "medium"),
            (f"Evaluar riesgo de actuar con informacion incompleta.", ["riesgo", "informacion incompleta", "actuar", d], "report", "diagnose", "high"),
            (f"Transformar una nota larga en entregable listo para copiar y pegar.", ["entregable", "copiar", "pegar", a], "report", "synthesize", "medium"),
        ]


def main() -> int:
    clone_for_missing_professions()
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    (ASSET_DIR / "dimension_schema.json").write_text(json.dumps(DIMENSIONS, ensure_ascii=False, indent=2), encoding="utf-8")
    (ASSET_DIR / "profession_context.json").write_text(json.dumps(BASE_CONTEXT, ensure_ascii=False, indent=2), encoding="utf-8")
    tasks = build_tasks()
    TASKS_FILE.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    REVIEW_FILE.write_text(review_pack(tasks), encoding="utf-8")
    DESIGN_FILE.write_text(design_doc(tasks), encoding="utf-8")
    print(TASKS_FILE)
    print(REVIEW_FILE)
    print(DESIGN_FILE)
    return 0


def build_tasks() -> list[dict[str, object]]:
    tasks: list[dict[str, object]] = []
    counter = 1
    profession_map = {item[0]: item for item in PROFESSIONS}
    for profession_id, profession_name, _ in PROFESSIONS:
        for intent, expected, output_form, reasoning, risk, *tool_override in TASKS_BY_PROFESSION[profession_id]:
            tool_need = tool_override[0] if tool_override else ("create_file" if output_form in {"data_file", "script"} else "read_files")
            dimensions = {
                "context_scope": "large" if risk == "high" else "medium",
                "data_mode": "web_fresh" if tool_need == "web_search" else "mixed",
                "tool_need": tool_need,
                "risk": risk,
                "output_form": output_form,
                "reasoning_shape": reasoning,
                "freshness": "current_web" if tool_need == "web_search" else "recent_local",
                "error_tolerance": "low" if risk == "high" else "medium",
            }
            prompt = (
                f"# Intencion sintetizada {counter:03d}: {profession_name}\n\n"
                "Esta tarea representa la intencion operativa que deberia extraerse de una nota de voz larga real. "
                "No se proporciona una nota falsa; se proporciona la tarea ya sintetizada para evaluar si el modelo puede resolverla con datos concretos.\n\n"
                f"Intencion: {intent}\n\n"
                "Usa los archivos locales de contexto profesional. Responde con un entregable directamente utilizable, no con una explicacion generica."
            )
            tasks.append(
                {
                    "id": f"intent-{counter:03d}",
                    "category": "persona_intention",
                    "persona_id": profession_id,
                    "profession": profession_name,
                    "prompt": prompt,
                    "required_files": [
                        "persona_intention_catalog/profession_context.json",
                        "persona_intention_catalog/dimension_schema.json",
                    ],
                    "expected_outputs": ["resultado.md"],
                    "requires_network": tool_need == "web_search",
                    "skills": sorted({tool_need, output_form, reasoning}),
                    "expected_keys": expected,
                    "dimensions": dimensions,
                    "rubric": {
                        "intent_resolution": 3,
                        "concrete_data_use": 3,
                        "expected_keys": 2,
                        "professional_fit": 1,
                        "usable_output": 1,
                    },
                }
            )
            counter += 1
    return tasks


def review_pack(tasks: list[dict[str, object]]) -> str:
    lines = [
        "# Pack De Revision Humana: Intenciones De Tareas Por Profesion",
        "",
        "Este documento NO contiene notas de voz falsas. Contiene la intencion sintetizada que podria salir de notas de voz largas reales.",
        "",
        "## Como pedir feedback",
        "",
        "Pidele a la persona real:",
        "",
        "> Lee las intenciones de tu profesion. Dime por nota de voz cuales son realistas, cuales sobran, cuales faltan, que datos concretos necesitarias aportar y que salida esperarias de una IA.",
        "",
        "Preguntas:",
        "",
        "- ¿Esta tarea sale realmente en tu dia a dia?",
        "- ¿Que datos concretos faltan?",
        "- ¿La pedirias por audio, por texto o no la pedirias?",
        "- ¿Que formato de salida te serviria?",
        "- ¿Que error seria grave?",
        "- ¿Que otras tareas repetitivas haces que no aparecen?",
        "",
    ]
    grouped: dict[str, list[dict[str, object]]] = {}
    for task in tasks:
        grouped.setdefault(str(task["profession"]), []).append(task)
    for profession, items in grouped.items():
        lines.append(f"## {profession}")
        lines.append("")
        for item in items:
            intent = str(item["prompt"]).split("Intencion: ", 1)[1].split("\n\n", 1)[0]
            dims = item["dimensions"]
            dim_text = ", ".join(f"{k}={v}" for k, v in dims.items())
            lines.append(f"- **{item['id']}**: {intent}")
            lines.append(f"  - Salida esperada: {dims['output_form']}; razonamiento: {dims['reasoning_shape']}; riesgo: {dims['risk']}")
            lines.append(f"  - Claves: {', '.join(item['expected_keys'])}")
            lines.append(f"  - Dimensiones: {dim_text}")
        lines.append("")
    return "\n".join(lines)


def design_doc(tasks: list[dict[str, object]]) -> str:
    by_profession: dict[str, int] = {}
    for task in tasks:
        by_profession[str(task["profession"])] = by_profession.get(str(task["profession"]), 0) + 1
    lines = [
        "# Persona Intention Catalog",
        "",
        "Catalogo de intenciones operativas que saldrian de notas de voz largas reales.",
        "",
        "No intenta imitar la voz humana. Separa dos fases:",
        "",
        "1. Captura de intencion desde nota larga real.",
        "2. Resolucion de la tarea ya sintetizada.",
        "",
        f"Total tareas: {len(tasks)}",
        "",
        "## Cobertura",
        "",
    ]
    for profession, count in sorted(by_profession.items()):
        lines.append(f"- {profession}: {count} intenciones")
    lines.extend(
        [
            "",
            "## Uso",
            "",
            "```powershell",
            "python .\\benchmarks\\benchmark_scheduler.py --tasks-file .\\benchmarks\\tasks\\persona_intention_tasks.json --engine codex:gpt-5.4-mini --task intent-001 --once",
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
