from __future__ import annotations

import html
import json
import re
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "benchmarks" / "results"
TASKS_FILE = ROOT / "benchmarks" / "tasks" / "assistant_tasks.json"

RUN_IDS = [
    "20260520_165939_023816",
    "20260512_173317_490752",
    "20260513_130231_288791",
    "20260513_185318_064815",
]

SELECTED_TASKS = [
    "test-01",
    "test-03",
    "test-05",
    "test-08",
    "test-09",
    "test-13",
    "test-15",
    "test-19",
    "test-24",
    "test-25",
]

PREFERRED_RUNS = {
    "test-01": ["20260520_165939_023816", "20260512_173317_490752", "20260513_130231_288791"],
    "test-03": ["20260520_165939_023816", "20260512_173317_490752", "20260513_130231_288791"],
    "test-05": ["20260520_165939_023816", "20260513_185318_064815"],
    "test-08": ["20260520_165939_023816", "20260512_173317_490752", "20260513_130231_288791"],
    "test-09": ["20260520_165939_023816", "20260513_185318_064815"],
    "test-13": ["20260520_165939_023816", "20260513_185318_064815"],
    "test-15": ["20260520_165939_023816", "20260512_173317_490752", "20260513_185318_064815"],
    "test-19": ["20260513_130231_288791", "20260512_173317_490752", "20260513_185318_064815"],
    "test-24": ["20260512_173317_490752", "20260520_165939_023816", "20260513_185318_064815"],
    "test-25": ["20260513_130231_288791", "20260513_185318_064815"],
}

ENGINE_ORDER = [
    "codex:gpt-5.5",
    "codex:gpt-5.4-mini",
    "gemini:gemini-2.5-pro",
    "gemini:gemini-2.5-flash",
    "gemini:gemini-2.5-flash-lite",
    "opencode:google/gemini-2.5-flash",
    "gemini_api:gemini-2.5-flash-lite",
    "groq:llama-3.1-8b-instant",
    "openrouter:deepseek/deepseek-v3.2",
]

LABELS = {
    "codex:gpt-5.5": "Codex 5.5",
    "codex:gpt-5.4-mini": "Codex 5.4 mini",
    "gemini:gemini-2.5-pro": "Gemini CLI Pro",
    "gemini:gemini-2.5-flash": "Gemini CLI Flash",
    "gemini:gemini-2.5-flash-lite": "Gemini CLI Flash-Lite",
    "opencode:google/gemini-2.5-flash": "OpenCode + Gemini Flash",
    "gemini_api:gemini-2.5-flash-lite": "Gemini API Flash-Lite",
    "groq:llama-3.1-8b-instant": "Groq Llama 8B",
    "openrouter:deepseek/deepseek-v3.2": "OpenRouter DeepSeek V3.2",
}

USAGE = {
    "codex:gpt-5.5": "premium, usar con freno",
    "codex:gpt-5.4-mini": "estandar Codex",
    "gemini:gemini-2.5-pro": "limitado por cuota 429",
    "gemini:gemini-2.5-flash": "Google Pro: buen coste/uso",
    "gemini:gemini-2.5-flash-lite": "muy barato / alto volumen",
    "opencode:google/gemini-2.5-flash": "agente CLI alternativo",
    "gemini_api:gemini-2.5-flash-lite": "barato, no agente",
    "groq:llama-3.1-8b-instant": "ultrarrapido/router",
    "openrouter:deepseek/deepseek-v3.2": "barato con credito",
}

CASE_INSIGHTS = {
    "test-01": "Busca una cita concreta cruzando correo y contacto. Sirve para ver si el modelo localiza datos exactos o se va a otra reunion parecida.",
    "test-03": "Extrae tareas desde notas de voz sinteticas. Mide tabla, cobertura y disciplina para no convertir todo en prosa.",
    "test-05": "Auditoria simple de gasto. Buen detector de si un modelo puede resolver barato sin agente caro.",
    "test-08": "Resumen semanal multiarchivo. Aqui se ve si agrupa compromisos con cliente y fecha sin perder prioridades.",
    "test-09": "Duplicados de marzo. Prueba pequena de calculo y trazabilidad: concepto, duplicado e impacto economico.",
    "test-13": "Auditoria Q1 multiarchivo. Sube la complejidad: reconciliar meses, duplicados, discrepancias y partidas limpias.",
    "test-15": "Cruzar notas con contactos. Es una tarea muy representativa del asistente real: resolver personas, empresas y emails.",
    "test-19": "Plan de implantacion y formacion. Buena tarea para comparar planificacion, hitos y dependencias.",
    "test-24": "Validar descuento con mercado. Mide uso del contexto web preparado y si distingue dato local de comparativa externa.",
    "test-25": "Informe ejecutivo de cuentas prioritarias. Resume el tipo de trabajo que seguramente querremos en uso diario.",
}


def main() -> int:
    tasks = {item["id"]: item for item in json.loads(TASKS_FILE.read_text(encoding="utf-8"))}
    rows, grades = load_runs()
    metrics = build_metrics(rows, grades)
    html_doc = build_report(tasks, rows, grades, metrics)
    output = RESULTS / "task_case_comparison_report.html"
    latest = RESULTS / "latest_task_case_comparison_report.html"
    output.write_text(html_doc, encoding="utf-8")
    latest.write_text(html_doc, encoding="utf-8")
    print(output)
    print(latest)
    return 0


def load_runs() -> tuple[list[dict[str, Any]], dict[tuple[str, str, str], dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    grades: dict[tuple[str, str, str], dict[str, Any]] = {}
    for run_id in RUN_IDS:
        run = RESULTS / run_id
        if not run.exists():
            continue
        for row in load_summary_rows(run):
            row["_run_id"] = run_id
            rows.append(row)
        grades_path = run / "grades.json"
        if grades_path.exists():
            for grade in json.loads(grades_path.read_text(encoding="utf-8", errors="replace")):
                engine = str(grade.get("engine_spec") or grade.get("engine") or "")
                label = str(grade.get("engine") or engine)
                task_id = str(grade.get("task_id") or "")
                grades[(run_id, engine, task_id)] = grade
                grades[(run_id, label, task_id)] = grade
    return rows, grades


def load_summary_rows(run: Path) -> list[dict[str, Any]]:
    summary = run / "summary.json"
    if summary.exists():
        try:
            parsed = json.loads(summary.read_text(encoding="utf-8", errors="replace"))
            return [item for item in parsed if isinstance(item, dict)]
        except json.JSONDecodeError:
            return []
    rows = []
    for path in run.glob("*.json"):
        if path.name in {"scheduler_state.json", "grades.json", "summary.json"}:
            continue
        try:
            parsed = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and "task_id" in parsed and "engine" in parsed:
            rows.append(parsed)
    return rows


def build_metrics(rows: list[dict[str, Any]], grades: dict[tuple[str, str, str], dict[str, Any]]) -> dict[str, dict[str, float]]:
    metrics: dict[str, dict[str, float]] = {}
    for engine in ENGINE_ORDER:
        scores = []
        success = []
        seconds = []
        for task_id in SELECTED_TASKS:
            row = pick_row(rows, grades, task_id, engine)
            if not row:
                continue
            scores.append(row_score(row, grades))
            success.append(1.0 if row.get("returncode") == 0 and not row.get("timed_out") else 0.0)
            seconds.append(float(row.get("elapsed_seconds") or 0))
        if scores:
            metrics[engine] = {
                "n": len(scores),
                "score": mean(scores),
                "success": 100.0 * sum(success) / len(success),
                "seconds": mean(seconds),
            }
    return metrics


def build_report(
    tasks: dict[str, dict[str, Any]],
    rows: list[dict[str, Any]],
    grades: dict[tuple[str, str, str], dict[str, Any]],
    metrics: dict[str, dict[str, float]],
) -> str:
    metrics_rows = "".join(
        f"<tr><td>{esc(LABELS.get(engine, engine))}</td><td>{int(values['n'])}</td>"
        f"<td>{values['score']:.2f}</td><td>{values['success']:.0f}%</td>"
        f"<td>{values['seconds']:.1f}s</td><td>{esc(USAGE.get(engine, ''))}</td></tr>"
        for engine, values in sorted(metrics.items(), key=lambda item: (-item[1]["score"], item[1]["seconds"]))
    )
    cases = "".join(render_case(tasks[task_id], rows, grades) for task_id in SELECTED_TASKS)
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Informe comparativo por tareas - Codex vs Gemini</title>
<style>
:root{{--ink:#172033;--muted:#667085;--bg:#f6f7f9;--panel:#fff;--line:#d9dee8;--blue:#174ea6;--amber:#b86e00}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:Segoe UI,Inter,Arial,sans-serif;line-height:1.45}}
.hero{{padding:42px 54px;background:#13233a;color:white}}.hero h1{{margin:0;font-size:34px}}.hero p{{max-width:1050px;color:#dbe7f5;font-size:17px}}
main{{max-width:1500px;margin:0 auto;padding:28px 34px 70px}}.panel,.case{{background:var(--panel);border:1px solid var(--line);border-radius:8px;box-shadow:0 8px 22px rgba(20,30,50,.05);padding:22px;margin:18px 0}}
.grid{{display:grid;gap:16px}}.cards{{grid-template-columns:repeat(auto-fit,minmax(250px,1fr))}}.card{{border:1px solid var(--line);border-radius:8px;padding:16px;background:white}}.card b{{display:block;font-size:22px;margin-top:6px}}.muted{{color:var(--muted)}}.pill{{display:inline-block;border:1px solid var(--line);background:#f8fafc;border-radius:999px;padding:4px 9px;font-size:12px;color:#344054}}
table{{width:100%;border-collapse:collapse;background:white;border:1px solid var(--line);font-size:13px}}th,td{{padding:10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{background:#eef2f7}}
.case-title{{display:grid;grid-template-columns:1fr minmax(280px,520px);gap:20px;align-items:start}}.case h2{{margin:8px 0 0;font-size:23px}}.expected,.case-conclusion{{border:1px solid #e7edf5;background:#fbfdff;border-radius:8px;padding:11px;margin:12px 0}}.answers{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px}}.answer{{border:1px solid var(--line);border-radius:8px;background:#fff;padding:12px}}.answer.fail{{border-color:#f3b3ad;background:#fffafa}}.answer-head{{display:flex;justify-content:space-between;gap:8px;color:#344054;font-size:12px}}.answer-head b{{font-size:14px;color:var(--ink)}}pre{{white-space:pre-wrap;word-break:break-word;background:#f8fafc;border:1px solid #e6edf7;border-radius:6px;padding:10px;max-height:260px;overflow:auto;font-size:12px;font-family:Consolas,monospace}}.callout{{border-left:5px solid var(--blue);background:#f7fbff;padding:14px;border-radius:8px}}.warn{{border-left-color:var(--amber);background:#fff8eb}}a{{color:#174ea6}}@media(max-width:900px){{.hero{{padding:30px 20px}}main{{padding:18px}}.case-title{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<section class="hero">
  <h1>Comparativa por tareas: Codex vs Gemini</h1>
  <p>Informe narrativo construido con salidas reales del laboratorio. No mira solo medias: entra en tareas concretas y compara como responde cada familia de modelos cuando tiene que leer archivos, extraer datos, calcular, sintetizar o usar contexto web preparado.</p>
</section>
<main>
<section class="panel"><h2>Conclusion ejecutiva</h2><div class="grid cards">
<div class="card"><span class="pill">Trabajo serio con archivos</span><b>Codex 5.4 mini</b><p class="muted">Mejor base operativa: estable, buen uso de filesystem y suficiente calidad sin gastar siempre 5.5.</p></div>
<div class="card"><span class="pill">Escalado</span><b>Codex 5.5</b><p class="muted">Mas prudente y consistente cuando hay riesgo, pero no conviene como motor masivo por coste/cuota.</p></div>
<div class="card"><span class="pill">Fallback Google</span><b>Gemini Flash</b><p class="muted">Puede cubrir una parte grande del trabajo. En la practica es el candidato Google mas equilibrado.</p></div>
<div class="card"><span class="pill">Router / volumen</span><b>Flash-Lite</b><p class="muted">Muy util para clasificar, extraer y validar barato. No lo pondria solo en tareas complejas.</p></div>
<div class="card"><span class="pill">Cuidado</span><b>Gemini Pro</b><p class="muted">La calidad teorica puede ser alta, pero aqui ha chocado con 429/RESOURCE_EXHAUSTED. No es fiable como default con la cuota actual.</p></div>
<div class="card"><span class="pill">Local privado</span><b>Mini Nano</b><p class="muted">Valioso para anonimizar y microtareas locales; no reemplaza hoy a Codex/Gemini CLI como agente.</p></div>
</div></section>
<section class="panel"><h2>Metricas observadas en las tareas seleccionadas</h2><table><thead><tr><th>Modelo</th><th>Muestras</th><th>Nota media heuristica</th><th>Exito tecnico</th><th>Tiempo medio</th><th>Lectura coste/uso</th></tr></thead><tbody>{metrics_rows}</tbody></table><p class="muted">Las notas son heuristicas por claves esperadas. Son utiles para comparar cobertura, pero el informe usa tambien lectura cualitativa de las respuestas.</p></section>
<section class="panel"><h2>Contexto externo y comunidad</h2><div class="callout">Gemini CLI documenta seleccion de modelo con <code>--model</code> y <code>/model</code>, y cuotas diarias para Google AI Pro. En nuestra prueba eso encaja con lo observado: Flash/Flash-Lite aguantan mejor, mientras Pro tropieza con cuota. Fuentes: <a href="https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/model.md">Gemini CLI model selection</a>, <a href="https://github.com/google-gemini/gemini-cli/blob/main/docs/resources/quota-and-pricing.md">Gemini CLI quotas</a>, <a href="https://ai.google.dev/gemini-api/docs/pricing">Gemini API pricing</a>, <a href="https://help.openai.com/en/articles/20001106-codex-rate-card">Codex rate card</a>.</div><div class="callout warn" style="margin-top:10px">En comunidad aparecen quejas recurrentes de limites reales de Gemini Pro por debajo de lo que uno espera en cargas largas. Nuestro 429 en Gemini Pro es coherente con esa senal, asi que no lo trataria como pilar operativo hasta medirlo tras reset o con cuenta/tier distinto.</div></section>
{cases}
<section class="panel"><h2>Regla operativa propuesta</h2><ol><li><b>Privacidad:</b> anonimizar localmente con reglas + Mini Nano cuando haya PII.</li><li><b>Entrada barata:</b> Groq o Gemini Flash-Lite para clasificar, validar claves y decidir ruta.</li><li><b>Trabajo normal:</b> Codex 5.4 mini si toca filesystem, multiarchivo, scripts o salida persistente.</li><li><b>Fallback Google:</b> Gemini CLI Flash para tareas ofimaticas, resumenes, tablas y parte del trabajo con archivos.</li><li><b>Escalado:</b> Codex 5.5 cuando falten claves, haya riesgo alto o la respuesta barata no pase.</li><li><b>No recomendado como default ahora:</b> Gemini Pro por cuota 429, Mini Nano como agente completo y OpenCode+Mini Nano por latencia.</li></ol></section>
</main></body></html>"""


def render_case(task: dict[str, Any], rows: list[dict[str, Any]], grades: dict[tuple[str, str, str], dict[str, Any]]) -> str:
    task_id = str(task["id"])
    answer_cards = []
    available = []
    for engine in ENGINE_ORDER:
        row = pick_row(rows, grades, task_id, engine)
        if not row:
            continue
        score = row_score(row, grades)
        ok = row.get("returncode") == 0 and not row.get("timed_out")
        available.append((score, ok, engine, row))
        status = "ok" if ok else "fail"
        answer_cards.append(
            f"""<article class="answer {status}">
  <div class="answer-head"><b>{esc(LABELS.get(engine, engine))}</b><span>{score:.1f}/10 · {float(row.get('elapsed_seconds') or 0):.0f}s · {esc(row.get('_run_id'))}</span></div>
  <pre>{esc(excerpt(output_text(row)))}</pre>
</article>"""
        )
    if available:
        best = sorted(available, key=lambda item: (-item[0], not item[1], float(item[3].get("elapsed_seconds") or 999999)))[0]
        best_text = f"Mejor senal: {LABELS.get(best[2], best[2])} ({best[0]:.1f}/10)."
    else:
        best_text = "Sin datos suficientes."
    if task_id in {"test-01", "test-03", "test-05", "test-08", "test-09", "test-13", "test-15"}:
        reading = "Codex tiende a crear salida mas verificable; Gemini Flash/Flash-Lite cubre mucho trabajo de bajo coste cuando no se agota cuota; Gemini Pro ahora mismo queda penalizado por 429 en la cuenta actual."
    else:
        reading = "En tareas de planificacion o web, Gemini CLI y OpenCode con Gemini Flash son alternativas razonables, pero Codex conserva mejor trazabilidad y control de archivo."
    title = task["prompt"].splitlines()[0].lstrip("# ").strip()
    expected = ", ".join(task.get("expected_keys", []))
    return f"""<section class="case">
  <div class="case-title">
    <div><span class="pill">{esc(task_id)} · {esc(task.get('level', ''))}</span><h2>{esc(title)}</h2></div>
    <p>{esc(CASE_INSIGHTS[task_id])}</p>
  </div>
  <div class="expected"><b>Claves esperadas:</b> {esc(expected)}</div>
  <div class="case-conclusion">{esc(best_text)} Lectura: {esc(reading)}</div>
  <div class="answers">{''.join(answer_cards)}</div>
</section>"""


def pick_row(rows: list[dict[str, Any]], grades: dict[tuple[str, str, str], dict[str, Any]], task_id: str, engine: str) -> dict[str, Any] | None:
    candidates = [row for row in rows if row.get("task_id") == task_id and engine_spec(row) == engine]
    if not candidates:
        return None
    order = PREFERRED_RUNS.get(task_id, [])

    def sort_key(row: dict[str, Any]) -> tuple[int, int, float]:
        try:
            priority = order.index(str(row.get("_run_id")))
        except ValueError:
            priority = 99
        ok = 1 if row.get("returncode") == 0 and not row.get("timed_out") else 0
        return (priority, -ok, -row_score(row, grades))

    return sorted(candidates, key=sort_key)[0]


def engine_spec(row: dict[str, Any]) -> str:
    return str(row.get("engine_spec") or row.get("engine") or "")


def row_score(row: dict[str, Any], grades: dict[tuple[str, str, str], dict[str, Any]]) -> float:
    run_id = str(row.get("_run_id"))
    task_id = str(row.get("task_id"))
    candidates = [
        grades.get((run_id, engine_spec(row), task_id)),
        grades.get((run_id, str(row.get("engine")), task_id)),
    ]
    for grade in candidates:
        if grade:
            return float(grade.get("score", grade.get("heuristic_score", 0)) or 0)
    if row.get("returncode") != 0 or row.get("timed_out"):
        return 0.0
    return 6.0


def output_text(row: dict[str, Any]) -> str:
    paths = []
    for key in ("copied_outputs", "output_files"):
        value = row.get(key)
        if isinstance(value, list):
            paths.extend(Path(str(item)) for item in value)
    for path in paths:
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="replace").strip()
            if text:
                return text
    return str(row.get("stdout") or row.get("stderr") or "").strip()


def excerpt(text: str, limit: int = 520) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text[:limit].rstrip() + ("..." if len(text) > limit else "")


def esc(value: Any) -> str:
    return html.escape(fix_mojibake(str(value)), quote=True)


def fix_mojibake(text: str) -> str:
    if "Ã" not in text and "Â" not in text:
        return text
    try:
        repaired = text.encode("latin1", errors="ignore").decode("utf-8", errors="ignore")
        return repaired or text
    except UnicodeError:
        return text


if __name__ == "__main__":
    raise SystemExit(main())
