from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TASKS_FILE = ROOT / "tasks" / "persona_natural_tasks.json"
ASSET_DIR = ROOT / "assets" / "persona_task_research"
DOC_DIMENSIONS = ROOT / "PERSONA_TASK_DIMENSIONS.md"
DOC_REVIEW = ROOT / "PERSONA_TASK_REVIEW_PACK.md"


DIMENSIONS = {
    "context_scope": {
        "description": "Cantidad y dispersion del contexto necesario.",
        "values": ["none", "small", "medium", "large", "cross_project"],
    },
    "data_mode": {
        "description": "Tipo de informacion dominante.",
        "values": ["conversation", "documents", "tables", "logs", "mixed", "web_fresh"],
    },
    "tool_need": {
        "description": "Capacidad externa necesaria para resolver bien.",
        "values": ["none", "read_files", "create_file", "code_execution", "web_search", "calendar", "multi_tool"],
    },
    "risk": {
        "description": "Coste potencial de una respuesta mala.",
        "values": ["low", "medium", "high", "critical"],
    },
    "output_form": {
        "description": "Forma final que el usuario espera.",
        "values": ["short_reply", "email", "table", "checklist", "plan", "report", "script", "calendar", "data_file"],
    },
    "reasoning_shape": {
        "description": "Tipo de procesamiento mental principal.",
        "values": ["retrieve", "extract", "compare", "calculate", "synthesize", "diagnose", "decide", "draft"],
    },
    "freshness": {
        "description": "Necesidad de informacion actual.",
        "values": ["static_local", "recent_local", "current_web"],
    },
    "error_tolerance": {
        "description": "Cuanto error puede aceptar el flujo antes de escalar.",
        "values": ["high", "medium", "low", "near_zero"],
    },
}


PROFESSIONS = [
    {
        "id": "inmobiliaria",
        "person": "Clara Benavides",
        "profession": "Agente inmobiliaria",
        "world": {
            "clients": ["pareja joven", "inversor de alquiler", "propietario impaciente", "comprador extranjero"],
            "projects": ["visitas semanales", "captacion de viviendas", "negociacion de ofertas", "seguimiento postvisita"],
            "documents": ["fichas de inmuebles", "notas de visita", "emails de propietarios", "comparativas de precio"],
        },
    },
    {
        "id": "informatico",
        "person": "Nicolas Ortega",
        "profession": "Responsable informatico / DevOps",
        "world": {
            "clients": ["equipo comercial", "soporte interno", "proveedor SSO", "direccion"],
            "projects": ["incidencias de login", "rotacion de claves", "limpieza de logs", "monitorizacion"],
            "documents": ["access.log", "tickets", "runbooks", "postmortems"],
        },
    },
    {
        "id": "cientifica",
        "person": "Dra. Irene Salvatierra",
        "profession": "Cientifica biomedica",
        "world": {
            "clients": ["comite etico", "equipo de estadistica", "direccion del laboratorio", "colaboradores externos"],
            "projects": ["ensayo piloto", "revision de resultados", "abstract de congreso", "control de muestras"],
            "documents": ["notas de laboratorio", "tablas de marcadores", "borradores de abstract", "protocolos"],
        },
    },
    {
        "id": "ingeniero",
        "person": "Marcos Valcarce",
        "profession": "Ingeniero industrial",
        "world": {
            "clients": ["proveedor de valvulas", "jefe de obra", "direccion", "equipo de seguridad"],
            "projects": ["seguimiento de hitos", "riesgos de obra", "control de costes", "inspecciones"],
            "documents": ["partes de obra", "presupuestos", "checklists de seguridad", "cronograma"],
        },
    },
    {
        "id": "abogada",
        "person": "Laura Montalban",
        "profession": "Abogada laboralista",
        "world": {
            "clients": ["trabajador despedido", "empresa cliente", "mediador", "asesoria externa"],
            "projects": ["despido disciplinario", "revision contractual", "mediacion", "plazos procesales"],
            "documents": ["contratos", "emails de cliente", "cartas de despido", "minutas"],
        },
    },
    {
        "id": "finanzas",
        "person": "Hector Rivas",
        "profession": "Consultor financiero para pymes",
        "world": {
            "clients": ["gerente pyme", "responsable contable", "cliente moroso", "banco"],
            "projects": ["prevision de caja", "cobros pendientes", "auditoria de gastos", "informe mensual"],
            "documents": ["facturas", "cobros", "gastos", "reportes de caja"],
        },
    },
]


NATURAL_TASKS = {
    "inmobiliaria": [
        ("El comprador me acaba de escribir que solo puede visitar hoy a partir de las seis. Mira mis inmuebles y proponme dos opciones realistas para responderle por WhatsApp.", ["visita", "dos opciones", "WhatsApp"], {"context_scope": "medium", "data_mode": "mixed", "tool_need": "read_files", "risk": "medium", "output_form": "short_reply", "reasoning_shape": "compare", "freshness": "recent_local", "error_tolerance": "medium"}),
        ("Prepara un email al propietario explicando por que no conviene subir el precio esta semana.", ["propietario", "precio", "no conviene"], {"context_scope": "small", "data_mode": "documents", "tool_need": "read_files", "risk": "medium", "output_form": "email", "reasoning_shape": "draft", "freshness": "recent_local", "error_tolerance": "medium"}),
        ("Tengo notas de tres visitas. Sacame objeciones repetidas y como responderlas sin sonar agresiva.", ["objeciones", "visitas", "responder"], {"context_scope": "medium", "data_mode": "conversation", "tool_need": "read_files", "risk": "medium", "output_form": "table", "reasoning_shape": "synthesize", "freshness": "recent_local", "error_tolerance": "medium"}),
        ("Ordename la ruta de visitas de manana minimizando desplazamientos y dime que huecos quedan.", ["ruta", "visitas", "huecos"], {"context_scope": "medium", "data_mode": "mixed", "tool_need": "calendar", "risk": "medium", "output_form": "plan", "reasoning_shape": "decide", "freshness": "recent_local", "error_tolerance": "low"}),
        ("Compara tres inmuebles para un inversor: precio, reforma probable, alquiler estimado y riesgo.", ["inversor", "precio", "riesgo"], {"context_scope": "large", "data_mode": "tables", "tool_need": "read_files", "risk": "high", "output_form": "report", "reasoning_shape": "compare", "freshness": "recent_local", "error_tolerance": "low"}),
        ("Redacta una respuesta breve a un comprador que quiere negociar demasiado a la baja.", ["negociar", "baja", "respuesta"], {"context_scope": "small", "data_mode": "conversation", "tool_need": "none", "risk": "medium", "output_form": "short_reply", "reasoning_shape": "draft", "freshness": "static_local", "error_tolerance": "medium"}),
        ("Hazme un resumen semanal de oportunidades calientes y propietarios que debo llamar.", ["oportunidades", "propietarios", "llamar"], {"context_scope": "large", "data_mode": "mixed", "tool_need": "read_files", "risk": "medium", "output_form": "report", "reasoning_shape": "synthesize", "freshness": "recent_local", "error_tolerance": "medium"}),
        ("Busca en la web si los precios de esta zona han cambiado y cruzalo con mis fichas.", ["web", "precios", "zona"], {"context_scope": "large", "data_mode": "web_fresh", "tool_need": "web_search", "risk": "high", "output_form": "report", "reasoning_shape": "compare", "freshness": "current_web", "error_tolerance": "low"}),
    ],
    "informatico": [
        ("Mira el log de esta manana y dime si el problema de login parece de nuestra app o del proveedor SSO.", ["login", "SSO", "log"], {"context_scope": "medium", "data_mode": "logs", "tool_need": "read_files", "risk": "high", "output_form": "short_reply", "reasoning_shape": "diagnose", "freshness": "recent_local", "error_tolerance": "low"}),
        ("Convierte estos tickets en una tabla por prioridad, responsable y siguiente accion.", ["tickets", "prioridad", "responsable"], {"context_scope": "medium", "data_mode": "documents", "tool_need": "read_files", "risk": "medium", "output_form": "table", "reasoning_shape": "extract", "freshness": "recent_local", "error_tolerance": "medium"}),
        ("Escribe un runbook corto para rotar la clave API sin romper produccion.", ["runbook", "clave API", "rollback"], {"context_scope": "small", "data_mode": "documents", "tool_need": "read_files", "risk": "high", "output_form": "checklist", "reasoning_shape": "decide", "freshness": "static_local", "error_tolerance": "low"}),
        ("Genera un script sencillo para contar errores 5xx por minuto en access.log.", ["script", "5xx", "por minuto"], {"context_scope": "medium", "data_mode": "logs", "tool_need": "code_execution", "risk": "medium", "output_form": "script", "reasoning_shape": "calculate", "freshness": "recent_local", "error_tolerance": "low"}),
        ("Redacta aviso interno sobre la incidencia sin asustar a comercial.", ["aviso", "incidencia", "comercial"], {"context_scope": "small", "data_mode": "conversation", "tool_need": "none", "risk": "medium", "output_form": "short_reply", "reasoning_shape": "draft", "freshness": "recent_local", "error_tolerance": "medium"}),
        ("Haz postmortem corto con causa probable, impacto, mitigacion y accion preventiva.", ["postmortem", "causa", "mitigacion"], {"context_scope": "large", "data_mode": "mixed", "tool_need": "read_files", "risk": "high", "output_form": "report", "reasoning_shape": "diagnose", "freshness": "recent_local", "error_tolerance": "low"}),
        ("Revisa dependencias del proyecto y dime si hay algo sospechoso o urgente.", ["dependencias", "sospechoso", "urgente"], {"context_scope": "large", "data_mode": "documents", "tool_need": "code_execution", "risk": "high", "output_form": "report", "reasoning_shape": "diagnose", "freshness": "current_web", "error_tolerance": "low"}),
        ("Prepara plan de migracion a otro proveedor de monitorizacion con pros, contras y riesgos.", ["migracion", "monitorizacion", "riesgos"], {"context_scope": "large", "data_mode": "web_fresh", "tool_need": "web_search", "risk": "high", "output_form": "plan", "reasoning_shape": "decide", "freshness": "current_web", "error_tolerance": "low"}),
    ],
    "cientifica": [
        ("Resume las notas de laboratorio separando observaciones, hipotesis y dudas.", ["observaciones", "hipotesis", "dudas"], {"context_scope": "medium", "data_mode": "documents", "tool_need": "read_files", "risk": "high", "output_form": "report", "reasoning_shape": "synthesize", "freshness": "recent_local", "error_tolerance": "low"}),
        ("Ordena la tabla de resultados por marcador y senala anomalias sin concluir causalidad.", ["marcador", "anomalias", "sin causalidad"], {"context_scope": "medium", "data_mode": "tables", "tool_need": "read_files", "risk": "high", "output_form": "table", "reasoning_shape": "extract", "freshness": "recent_local", "error_tolerance": "low"}),
        ("Redacta email prudente al comite pidiendo ampliar muestra.", ["comite", "ampliar muestra", "prudente"], {"context_scope": "small", "data_mode": "documents", "tool_need": "none", "risk": "high", "output_form": "email", "reasoning_shape": "draft", "freshness": "static_local", "error_tolerance": "low"}),
        ("Dame preguntas para estadistica antes de enviar el abstract.", ["estadistica", "abstract", "preguntas"], {"context_scope": "small", "data_mode": "documents", "tool_need": "read_files", "risk": "medium", "output_form": "checklist", "reasoning_shape": "decide", "freshness": "static_local", "error_tolerance": "medium"}),
        ("Cruza notas y tabla para briefing de direccion: que sabemos, que no sabemos y decision recomendada.", ["sabemos", "no sabemos", "decision"], {"context_scope": "large", "data_mode": "mixed", "tool_need": "read_files", "risk": "high", "output_form": "report", "reasoning_shape": "synthesize", "freshness": "recent_local", "error_tolerance": "low"}),
        ("Convierte estas notas en un resumen para pacientes, sin tecnicismos y sin prometer resultados.", ["pacientes", "sin tecnicismos", "sin prometer"], {"context_scope": "medium", "data_mode": "documents", "tool_need": "read_files", "risk": "critical", "output_form": "short_reply", "reasoning_shape": "draft", "freshness": "static_local", "error_tolerance": "near_zero"}),
        ("Busca literatura reciente sobre este marcador y dime si cambia nuestra interpretacion.", ["literatura reciente", "marcador", "interpretacion"], {"context_scope": "large", "data_mode": "web_fresh", "tool_need": "web_search", "risk": "critical", "output_form": "report", "reasoning_shape": "compare", "freshness": "current_web", "error_tolerance": "near_zero"}),
        ("Prepara una tabla de limitaciones del estudio y mitigaciones posibles.", ["limitaciones", "mitigaciones", "estudio"], {"context_scope": "medium", "data_mode": "mixed", "tool_need": "read_files", "risk": "high", "output_form": "table", "reasoning_shape": "synthesize", "freshness": "recent_local", "error_tolerance": "low"}),
    ],
    "ingeniero": [
        ("Del parte de obra de hoy, dime los dos riesgos que debo mirar primero.", ["riesgos", "obra", "primero"], {"context_scope": "medium", "data_mode": "documents", "tool_need": "read_files", "risk": "high", "output_form": "short_reply", "reasoning_shape": "decide", "freshness": "recent_local", "error_tolerance": "low"}),
        ("Calcula desviacion entre presupuesto y coste real por hito.", ["desviacion", "presupuesto", "coste real"], {"context_scope": "medium", "data_mode": "tables", "tool_need": "read_files", "risk": "high", "output_form": "table", "reasoning_shape": "calculate", "freshness": "recent_local", "error_tolerance": "low"}),
        ("Redacta aviso al proveedor por retraso sin romper la relacion.", ["proveedor", "retraso", "relacion"], {"context_scope": "small", "data_mode": "conversation", "tool_need": "none", "risk": "medium", "output_form": "email", "reasoning_shape": "draft", "freshness": "recent_local", "error_tolerance": "medium"}),
        ("Prepara checklist de seguridad para inspeccion de manana.", ["checklist", "seguridad", "inspeccion"], {"context_scope": "small", "data_mode": "documents", "tool_need": "read_files", "risk": "critical", "output_form": "checklist", "reasoning_shape": "extract", "freshness": "recent_local", "error_tolerance": "near_zero"}),
        ("Dame plan de recuperacion si el proveedor llega tres dias tarde.", ["plan", "tres dias", "proveedor"], {"context_scope": "large", "data_mode": "mixed", "tool_need": "read_files", "risk": "high", "output_form": "plan", "reasoning_shape": "decide", "freshness": "recent_local", "error_tolerance": "low"}),
        ("Haz informe para direccion con estado, desviaciones y decisiones pendientes.", ["direccion", "desviaciones", "decisiones"], {"context_scope": "large", "data_mode": "mixed", "tool_need": "read_files", "risk": "high", "output_form": "report", "reasoning_shape": "synthesize", "freshness": "recent_local", "error_tolerance": "low"}),
        ("Crea un CSV con hitos, responsable, riesgo y siguiente accion.", ["CSV", "hitos", "responsable"], {"context_scope": "medium", "data_mode": "tables", "tool_need": "create_file", "risk": "medium", "output_form": "data_file", "reasoning_shape": "extract", "freshness": "recent_local", "error_tolerance": "medium"}),
        ("Busca alternativas de proveedor y compara plazo, coste y riesgo tecnico.", ["alternativas", "proveedor", "plazo"], {"context_scope": "large", "data_mode": "web_fresh", "tool_need": "web_search", "risk": "high", "output_form": "report", "reasoning_shape": "compare", "freshness": "current_web", "error_tolerance": "low"}),
    ],
    "abogada": [
        ("Resume este hilo de cliente y dime que documentos faltan antes de contestar.", ["documentos faltan", "cliente", "contestar"], {"context_scope": "medium", "data_mode": "conversation", "tool_need": "read_files", "risk": "high", "output_form": "short_reply", "reasoning_shape": "extract", "freshness": "recent_local", "error_tolerance": "low"}),
        ("Redacta respuesta formal al cliente sin prometer resultado.", ["formal", "sin prometer", "cliente"], {"context_scope": "small", "data_mode": "conversation", "tool_need": "none", "risk": "high", "output_form": "email", "reasoning_shape": "draft", "freshness": "static_local", "error_tolerance": "low"}),
        ("Extrae plazos, riesgos y puntos ambiguos de estos contratos.", ["plazos", "riesgos", "ambiguos"], {"context_scope": "large", "data_mode": "documents", "tool_need": "read_files", "risk": "critical", "output_form": "table", "reasoning_shape": "extract", "freshness": "recent_local", "error_tolerance": "near_zero"}),
        ("Prepara minuta de reunion de mediacion con puntos no negociables.", ["mediacion", "no negociables", "minuta"], {"context_scope": "medium", "data_mode": "documents", "tool_need": "read_files", "risk": "high", "output_form": "report", "reasoning_shape": "synthesize", "freshness": "recent_local", "error_tolerance": "low"}),
        ("Compara dos clausulas y dime cual es menos arriesgada, con cautelas.", ["clausula", "menos arriesgada", "cautelas"], {"context_scope": "medium", "data_mode": "documents", "tool_need": "read_files", "risk": "critical", "output_form": "report", "reasoning_shape": "compare", "freshness": "static_local", "error_tolerance": "near_zero"}),
        ("Haz informe semanal de expedientes: urgencias, bloqueos y siguiente accion.", ["urgencias", "bloqueos", "siguiente accion"], {"context_scope": "large", "data_mode": "mixed", "tool_need": "read_files", "risk": "high", "output_form": "report", "reasoning_shape": "synthesize", "freshness": "recent_local", "error_tolerance": "low"}),
        ("Convierte este audio transcrito en lista de tareas con plazos y responsables.", ["tareas", "plazos", "responsables"], {"context_scope": "medium", "data_mode": "conversation", "tool_need": "read_files", "risk": "medium", "output_form": "table", "reasoning_shape": "extract", "freshness": "recent_local", "error_tolerance": "medium"}),
        ("Busca si ha cambiado alguna referencia normativa relevante y resume impacto sin asesorar definitivamente.", ["referencia normativa", "impacto", "sin asesorar"], {"context_scope": "large", "data_mode": "web_fresh", "tool_need": "web_search", "risk": "critical", "output_form": "report", "reasoning_shape": "compare", "freshness": "current_web", "error_tolerance": "near_zero"}),
    ],
    "finanzas": [
        ("Mira facturas y cobros: dime que cliente genera tension de caja esta semana.", ["facturas", "cobros", "tension de caja"], {"context_scope": "medium", "data_mode": "tables", "tool_need": "read_files", "risk": "high", "output_form": "short_reply", "reasoning_shape": "calculate", "freshness": "recent_local", "error_tolerance": "low"}),
        ("Redacta email amable reclamando una factura vencida.", ["email", "factura vencida", "amable"], {"context_scope": "small", "data_mode": "conversation", "tool_need": "none", "risk": "medium", "output_form": "email", "reasoning_shape": "draft", "freshness": "recent_local", "error_tolerance": "medium"}),
        ("Agrupa gastos por categoria y marca anomalias.", ["gastos", "categoria", "anomalias"], {"context_scope": "medium", "data_mode": "tables", "tool_need": "read_files", "risk": "high", "output_form": "table", "reasoning_shape": "calculate", "freshness": "recent_local", "error_tolerance": "low"}),
        ("Haz prevision de caja sencilla para 14 dias con supuestos claros.", ["prevision", "14 dias", "supuestos"], {"context_scope": "medium", "data_mode": "tables", "tool_need": "read_files", "risk": "high", "output_form": "report", "reasoning_shape": "calculate", "freshness": "recent_local", "error_tolerance": "low"}),
        ("Crea resumen para direccion con tres medidas para mejorar caja este mes.", ["direccion", "tres medidas", "caja"], {"context_scope": "large", "data_mode": "mixed", "tool_need": "read_files", "risk": "high", "output_form": "report", "reasoning_shape": "decide", "freshness": "recent_local", "error_tolerance": "low"}),
        ("Cruza facturas, cobros y gastos para detectar riesgos financieros y acciones.", ["facturas", "cobros", "riesgos"], {"context_scope": "large", "data_mode": "mixed", "tool_need": "read_files", "risk": "high", "output_form": "report", "reasoning_shape": "synthesize", "freshness": "recent_local", "error_tolerance": "low"}),
        ("Genera un CSV limpio de clientes con deuda vencida, importe y dias de retraso.", ["CSV", "deuda vencida", "dias"], {"context_scope": "medium", "data_mode": "tables", "tool_need": "create_file", "risk": "high", "output_form": "data_file", "reasoning_shape": "extract", "freshness": "recent_local", "error_tolerance": "low"}),
        ("Busca alternativas de financiacion a corto plazo y dime pros, contras y coste probable.", ["financiacion", "pros", "coste"], {"context_scope": "large", "data_mode": "web_fresh", "tool_need": "web_search", "risk": "critical", "output_form": "report", "reasoning_shape": "compare", "freshness": "current_web", "error_tolerance": "near_zero"}),
    ],
}


def main() -> int:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)

    worlds = {"professions": PROFESSIONS, "dimensions": DIMENSIONS}
    (ASSET_DIR / "profession_worlds.json").write_text(json.dumps(worlds, ensure_ascii=False, indent=2), encoding="utf-8")
    (ASSET_DIR / "README.md").write_text(asset_readme(), encoding="utf-8")

    tasks = build_tasks()
    TASKS_FILE.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_DIMENSIONS.write_text(dimensions_doc(), encoding="utf-8")
    DOC_REVIEW.write_text(review_pack(tasks), encoding="utf-8")
    print(TASKS_FILE)
    print(DOC_DIMENSIONS)
    print(DOC_REVIEW)
    return 0


def build_tasks() -> list[dict[str, object]]:
    tasks: list[dict[str, object]] = []
    counter = 1
    for profession in PROFESSIONS:
        for message, expected_keys, dimensions in NATURAL_TASKS[profession["id"]]:
            task_id = f"natural-{counter:03d}"
            prompt = (
                f"# Tarea natural {task_id}: {profession['profession']}\n\n"
                f"Persona sintetica: {profession['person']}.\n"
                f"Profesion: {profession['profession']}.\n"
                f"Mensaje entrante tipo Telegram: \"{message}\"\n\n"
                "Usa el contexto local disponible sobre esta profesion y responde como asistente operativo.\n"
                "No clasifiques por dificultad. Resuelve la tarea de manera natural, breve y util.\n"
                "Si falta informacion, dilo y propone la accion minima siguiente.\n"
            )
            tasks.append(
                {
                    "id": task_id,
                    "category": "persona_natural_task",
                    "persona_id": profession["id"],
                    "profession": profession["profession"],
                    "prompt": prompt,
                    "required_files": ["persona_task_research/profession_worlds.json"],
                    "expected_outputs": ["resultado.md"],
                    "requires_network": dimensions["tool_need"] == "web_search",
                    "skills": sorted({dimensions["reasoning_shape"], dimensions["output_form"], dimensions["tool_need"]}),
                    "expected_keys": expected_keys,
                    "dimensions": dimensions,
                    "rubric": {
                        "intent_detection": 2,
                        "correctness": 3,
                        "expected_keys": 2,
                        "professional_fit": 2,
                        "actionability": 1,
                    },
                }
            )
            counter += 1
    return tasks


def dimensions_doc() -> str:
    lines = [
        "# Dimensiones Para Benchmark De Tareas Naturales",
        "",
        "La suite deja de usar niveles rigidos. Las tareas se describen por dimensiones observables, mas estables que la dificultad.",
        "",
        "Estas dimensiones son una primera version y deben evolucionar con datos de benchmark y feedback humano.",
        "",
    ]
    for key, value in DIMENSIONS.items():
        lines.append(f"## {key}")
        lines.append(value["description"])
        lines.append("")
        lines.append("Valores: " + ", ".join(f"`{item}`" for item in value["values"]))
        lines.append("")
    lines.extend(
        [
            "## Como Usarlas",
            "",
            "1. Generar tareas naturales sin nivel numerico.",
            "2. Etiquetarlas inicialmente con estas dimensiones.",
            "3. Ejecutarlas contra varios modelos.",
            "4. Medir nota, coste, tiempo, fallos, reintentos y claves acertadas.",
            "5. Aprender que dimensiones predicen mejor el modelo minimo suficiente.",
            "",
            "La dificultad pasa a ser una variable observada, no una etiqueta impuesta de antemano.",
        ]
    )
    return "\n".join(lines) + "\n"


def review_pack(tasks: list[dict[str, object]]) -> str:
    lines = [
        "# Pack De Revision Humana: Tareas Naturales Por Profesion",
        "",
        "Objetivo: pasar esta lista a personas reales para que opinen si las tareas se parecen a su dia a dia.",
        "",
        "## Como Pedir Feedback",
        "",
        "Puedes enviarles este texto:",
        "",
        "> Estoy creando un banco de pruebas sintetico para asistentes de IA. Lee las tareas de tu profesion y grabame una nota de voz comentando: cuales son realistas, cuales sobran, cuales faltan, que matices profesionales ves y que errores de una IA te preocuparian.",
        "",
        "Preguntas utiles:",
        "",
        "- Que tareas haces de verdad cada semana?",
        "- Cuales de estas tareas te parecen artificiales?",
        "- Que datos/documentos reales harian falta?",
        "- Que respuesta de IA seria peligrosa o inutil?",
        "- Que formato preferirias recibir?",
        "- Que tarea pequena haces muchas veces y seria valiosa automatizar?",
        "",
    ]
    grouped: dict[str, list[dict[str, object]]] = {}
    for task in tasks:
        grouped.setdefault(str(task["profession"]), []).append(task)
    for profession, items in grouped.items():
        lines.append(f"## {profession}")
        lines.append("")
        for task in items:
            prompt = str(task["prompt"]).split('Mensaje entrante tipo Telegram: "', 1)[1].split('"', 1)[0]
            dims = task["dimensions"]
            dim_text = ", ".join(f"{k}={v}" for k, v in dims.items())
            lines.append(f"- **{task['id']}**: {prompt}")
            lines.append(f"  - Dimensiones iniciales: {dim_text}")
            lines.append(f"  - Claves esperadas: {', '.join(task['expected_keys'])}")
        lines.append("")
    return "\n".join(lines)


def asset_readme() -> str:
    return """# Persona Task Research

Contexto sintetico para generar y evaluar tareas naturales por profesion.

Archivos:
- `profession_worlds.json`: personas, mundo profesional y dimensiones.

Tareas:
- `benchmarks/tasks/persona_natural_tasks.json`

Documentos:
- `benchmarks/PERSONA_TASK_DIMENSIONS.md`
- `benchmarks/PERSONA_TASK_REVIEW_PACK.md`
"""


if __name__ == "__main__":
    raise SystemExit(main())
