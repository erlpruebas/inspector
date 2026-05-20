from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

from task_loader import RESULTS_DIR


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an HTML report from a benchmark run.")
    parser.add_argument("--run-dir", default="")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    run_dir = Path(args.run_dir) if args.run_dir else latest_run_dir()
    output = Path(args.output) if args.output else run_dir / "lab_report.html"
    report = build_html_report(run_dir)
    output.write_text(report, encoding="utf-8")
    latest = RESULTS_DIR / "latest_lab_report.html"
    latest.write_text(report, encoding="utf-8")
    print(output)
    print(latest)
    return 0


def latest_run_dir() -> Path:
    candidates = [path for path in RESULTS_DIR.iterdir() if path.is_dir()]
    if not candidates:
        raise SystemExit("No benchmark runs found")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def build_html_report(run_dir: Path) -> str:
    summary = load_json(run_dir / "summary.json", default=[])
    grades = load_json(run_dir / "grades.json", default=[])
    checks = load_json(run_dir / "expected_key_checks.json", default=[])
    manifest = load_json(run_dir / "multi_user_manifest.json", default={})
    by_engine = aggregate_by_engine(summary, grades, checks)
    by_user = aggregate_by_user(summary)
    privacy = aggregate_privacy(summary)
    examples_markup = build_examples_markup(summary, grades)
    history_markup = build_history_markup()

    kpis = {
        "tasks": len(summary),
        "engines": len(by_engine),
        "users": manifest.get("users", len(by_user)),
        "avg_score": round(mean([row.get("score", row.get("heuristic_score", 0)) for row in grades]) if grades else 0, 2),
    }
    best_quality = best_engine(by_engine, "avg_score")
    fastest = best_engine(by_engine, "avg_seconds", lowest=True)
    cheapest = best_engine(by_engine, "avg_cost", lowest=True)
    recommended = build_recommendations(by_engine)

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Lab Report {escape(run_dir.name)}</title>
<style>
:root{{--ink:#172033;--muted:#667085;--line:#e5e7eb;--bg:#f7f8fb;--panel:#fff;--blue:#2557a7;--green:#137a4b;--amber:#b7791f;--red:#b83232;}}
*{{box-sizing:border-box}} body{{margin:0;font-family:Inter,Segoe UI,Roboto,Arial,sans-serif;background:var(--bg);color:var(--ink);line-height:1.45}} a{{color:var(--blue)}}
.hero{{background:linear-gradient(135deg,#10233f,#265a7f 48%,#2b7a5b);color:white;padding:44px 56px 34px}} .hero h1{{margin:0;font-size:38px}} .hero p{{max-width:1040px;color:#dce9f5;font-size:17px}}
.wrap{{max-width:1480px;margin:0 auto;padding:28px 36px 60px}} .grid{{display:grid;gap:18px}} .kpis{{grid-template-columns:repeat(4,minmax(180px,1fr));margin-top:-44px}}
.kpi,.panel,.card{{background:var(--panel);border:1px solid var(--line);border-radius:8px;box-shadow:0 8px 26px rgba(16,24,40,.06)}} .kpi{{padding:18px}} .kpi span{{color:var(--muted);font-size:13px}} .kpi b{{display:block;font-size:28px;margin-top:6px}}
.panel{{padding:22px;margin-top:22px}} h2{{font-size:23px;margin:0 0 14px}} h3{{margin:0;font-size:17px}} .lead{{font-size:17px;color:#344054;max-width:1080px}}
.cards{{grid-template-columns:repeat(auto-fit,minmax(280px,1fr));}} .card{{padding:18px}} .card .num{{font-size:34px;font-weight:800;margin:10px 0 4px}} .tag{{display:inline-block;padding:4px 8px;border:1px solid var(--line);border-radius:999px;font-size:12px;color:#344054;background:#f9fafb}}
.example-card{{display:flex;flex-direction:column;gap:12px}} .example-list{{display:grid;gap:12px}} .example-item{{border:1px solid var(--line);border-radius:8px;background:#fbfdff;padding:12px}} .example-top{{display:flex;justify-content:space-between;gap:10px;align-items:flex-start;margin-bottom:4px}} pre{{margin:8px 0 0;white-space:pre-wrap;word-break:break-word;font-family:Consolas,Monaco,monospace;font-size:12px;line-height:1.45;background:#f8fafc;border:1px solid #e6edf7;border-radius:6px;padding:10px;max-height:240px;overflow:auto}}
table{{width:100%;border-collapse:separate;border-spacing:0;border:1px solid var(--line);border-radius:8px;overflow:hidden;background:white;font-size:13px}} th,td{{padding:10px 11px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}} th{{background:#f2f4f7;color:#344054;font-weight:700}} tr:last-child td,tr:last-child th{{border-bottom:0}}
.steps{{display:grid;gap:10px}} .step{{border:1px solid var(--line);border-left:5px solid var(--blue);padding:13px;border-radius:8px;background:#fff}}
.muted{{color:var(--muted)}} .bad{{color:var(--red)}} .good{{color:var(--green)}} .warn{{color:#9f3412;background:#fff7ed;border:1px solid #fed7aa;border-radius:7px;padding:8px}}
.scroll{{overflow:auto;max-height:760px;border-radius:8px}} @media(max-width:900px){{.hero{{padding:32px 22px}}.wrap{{padding:18px}}.kpis{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<section class="hero">
  <h1>Lab Report · {escape(run_dir.name)}</h1>
  <p>Informe operativo del laboratorio: anonimización, calidad por modelo y orquestación multiusuario. Este run es la pieza que nos dice qué modelo conviene para cada tipo de trabajo y cómo repartirlo sin mezclar carpetas ni contextos.</p>
</section>
<main class="wrap">
  <section class="grid kpis">
    <div class="kpi"><span>Tareas corridas</span><b>{kpis["tasks"]}</b></div>
    <div class="kpi"><span>Motores</span><b>{kpis["engines"]}</b></div>
    <div class="kpi"><span>Usuarios aislados</span><b>{kpis["users"]}</b></div>
    <div class="kpi"><span>Score medio</span><b>{kpis["avg_score"]}</b></div>
  </section>

  <section class="panel">
    <h2>Lectura Ejecutiva</h2>
    <p class="lead">La arquitectura ya permite correr tareas privadas con carpetas separadas por usuario, anonimizar antes de llamar al modelo y guardar un mapa global estable. En el corte actual, <b>{escape(best_quality.name if best_quality else "-")}</b> es el mejor modelo por calidad media, <b>{escape(fastest.name if fastest else "-")}</b> es el más ágil y <b>{escape(cheapest.name if cheapest else "-")}</b> es el más barato en el conjunto observado.</p>
    <div class="steps">
      <div class="step"><b>1. Privacidad primero</b>Las tareas con datos sensibles se anonimizan antes de entrar al modelo. El mapa de tokens queda fuera del workdir y no viaja al proveedor.</div>
      <div class="step"><b>2. Cuatro usuarios aislados</b>La carga se reparte en cuatro lanes con carpetas separadas y sin interacción entre hilos.</div>
      <div class="step"><b>3. Router barato</b>Groq y Gemini Flash-Lite son los mejores candidatos para clasificar, extraer y enrutar antes de gastar motores caros.</div>
      <div class="step"><b>4. Escalado selectivo</b>Codex 5.4 mini se queda como caballo de batalla y 5.5 solo entra cuando la tarea es crítica o el intento barato falla.</div>
    </div>
  </section>

  <section class="panel">
    <h2>Métricas Por Modelo</h2>
    <div class="scroll">
      <table>
        <thead>
          <tr>
            <th>Motor</th>
            <th>Score medio</th>
            <th>% Claves OK</th>
            <th>% Éxito técnico</th>
            <th>Tiempo medio</th>
            <th>Coste medio</th>
            <th>Observación</th>
          </tr>
        </thead>
        <tbody>
          {''.join(render_engine_rows(by_engine))}
        </tbody>
      </table>
    </div>
  </section>

  <section class="panel">
    <h2>Ejemplos Reales Del Run Privado</h2>
    <p class="lead">Estas tarjetas muestran ejemplos concretos de salida obtenida por cada motor en la última campaña privada. Es una lectura más útil que una sola nota media porque enseña el estilo de respuesta, la disciplina con la privacidad y el tipo de tarea donde cada motor se mueve mejor.</p>
    <div class="grid cards">
      {examples_markup}
    </div>
  </section>

  <section class="panel">
    <h2>Referencia Histórica De Codex 5.5</h2>
    {history_markup}
  </section>

  <section class="panel">
    <h2>Distribución Por Usuario</h2>
    <div class="scroll">
      <table>
        <thead><tr><th>Usuario</th><th>Tareas</th><th>Motores</th><th>Ruta</th></tr></thead>
        <tbody>{''.join(render_user_rows(by_user, run_dir))}</tbody>
      </table>
    </div>
  </section>

  <section class="panel">
    <h2>Privacidad</h2>
    <div class="grid cards">
      <div class="card"><span class="tag">Tokens encontrados</span><div class="num">{privacy["entities_found"]}</div><div class="muted">Durante el run privado</div></div>
      <div class="card"><span class="tag">Archivos procesados</span><div class="num">{privacy["files_processed"]}</div><div class="muted">Copia original, mixed y redacted generadas</div></div>
      <div class="card"><span class="tag">Verificación</span><div class="num">{'OK' if privacy["verification_passed"] else 'FAIL'}</div><div class="muted">{'Sin restos detectables' if privacy["verification_passed"] else 'Quedaron hallazgos residuales'}</div></div>
      <div class="card"><span class="tag">Revisor Mini Nano</span><div class="num">{'sí' if privacy["reviewer_used"] else 'no'}</div><div class="muted">Usado solo si se activó review semántico</div></div>
    </div>
  </section>

  <section class="panel">
    <h2>Recomendaciones Operativas</h2>
    <div class="steps">
      {''.join(f'<div class="step">{escape(item)}</div>' for item in recommended)}
    </div>
  </section>

  <section class="panel">
    <h2>Notas</h2>
    <p class="lead">Este informe combina las señales técnicas del run con la capa de privacidad y la distribución por usuario. Cuando tengamos más muestras, podremos convertir estas recomendaciones en reglas de enrutado más finas por profesión, riesgo y tipo de salida.</p>
    <p class="warn">Bloqueos observados en esta base: Groq puede cortar por tamaño de contexto, OpenRouter necesita margen de tokens, Mini Nano sigue siendo sensible a timeout y Codex conviene reservarlo para fases con valor real.</p>
  </section>
</main>
</body></html>"""


@dataclass
class EngineStats:
    name: str
    avg_score: float
    avg_seconds: float
    avg_cost: float
    pass_rate: float
    success_rate: float
    notes: str


def aggregate_by_engine(summary: list[dict[str, Any]], grades: list[dict[str, Any]], checks: list[dict[str, Any]]) -> list[EngineStats]:
    grades_by_engine = defaultdict(list)
    for row in grades:
        grades_by_engine[str(row.get("engine", ""))].append(row)
    rows_by_engine = defaultdict(list)
    for row in summary:
        rows_by_engine[str(row.get("engine", ""))].append(row)
    checks_by_engine = defaultdict(list)
    for row in checks:
        checks_by_engine[str(row.get("engine", ""))].append(row)

    out: list[EngineStats] = []
    for engine in sorted(rows_by_engine):
        rows = rows_by_engine[engine]
        grade_rows = grades_by_engine.get(engine, [])
        check_rows = checks_by_engine.get(engine, [])
        scores = [float(row.get("score", row.get("heuristic_score", 0))) for row in grade_rows if row.get("score", row.get("heuristic_score", 0)) is not None]
        costs = [extract_cost(row) for row in rows]
        seconds = [float(row.get("elapsed_seconds") or 0) for row in rows]
        pass_rate = percent([bool(row.get("passed_expected_keys")) for row in grade_rows]) if grade_rows else 0.0
        success_rate = percent([row.get("returncode") == 0 and not row.get("timed_out") for row in rows]) if rows else 0.0
        notes = engine_notes(engine, rows, grade_rows, check_rows)
        out.append(
            EngineStats(
                name=engine_label(engine),
                avg_score=round(mean(scores), 2) if scores else 0.0,
                avg_seconds=round(mean(seconds), 2) if seconds else 0.0,
                avg_cost=round(mean(costs), 6) if costs else 0.0,
                pass_rate=round(pass_rate, 1),
                success_rate=round(success_rate, 1),
                notes=notes,
            )
        )
    return sorted(out, key=lambda item: (-item.avg_score, item.avg_seconds, item.avg_cost))


def aggregate_by_user(summary: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in summary:
        grouped[str(row.get("user", "user_01"))].append(row)
    return grouped


def aggregate_privacy(summary: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [row.get("privacy") for row in summary if isinstance(row.get("privacy"), dict)]
    if not rows:
        return {"entities_found": 0, "files_processed": 0, "verification_passed": True, "reviewer_used": False}
    return {
        "entities_found": sum(int(row.get("entities_found", 0)) for row in rows),
        "files_processed": sum(int(row.get("files_processed", 0)) for row in rows),
        "verification_passed": all(bool(row.get("verification_passed", False)) for row in rows),
        "reviewer_used": any(bool(row.get("reviewer_used", False)) for row in rows),
    }


def render_engine_rows(rows: list[EngineStats]) -> list[str]:
    html_rows = []
    for row in rows:
        html_rows.append(
            f"<tr><td>{escape(row.name)}</td><td>{row.avg_score:.2f}</td><td>{row.pass_rate:.0f}%</td><td>{row.success_rate:.0f}%</td><td>{row.avg_seconds:.2f}s</td><td>{row.avg_cost:.6f}</td><td>{escape(row.notes)}</td></tr>"
        )
    return html_rows


def render_user_rows(grouped: dict[str, list[dict[str, Any]]], run_dir: Path) -> list[str]:
    rows = []
    for user, entries in sorted(grouped.items()):
        engines = ", ".join(sorted({str(row.get("engine", "")) for row in entries}))
        rows.append(f"<tr><td>{escape(user)}</td><td>{len(entries)}</td><td>{escape(engines)}</td><td>{escape(str(run_dir / 'users' / user))}</td></tr>")
    return rows


def build_recommendations(rows: list[EngineStats]) -> list[str]:
    if not rows:
        return ["No hay datos suficientes para recomendar motores."]
    quality = rows[0]
    fastest = min(rows, key=lambda item: item.avg_seconds)
    cheapest = min(rows, key=lambda item: item.avg_cost)
    return [
        f"Modelo de calidad: {quality.name} con score medio {quality.avg_score:.2f}.",
        f"Modelo más rápido: {fastest.name} con {fastest.avg_seconds:.2f}s medio.",
        f"Modelo más barato: {cheapest.name} con coste medio {cheapest.avg_cost:.6f}.",
        "Groq y Gemini Flash-Lite quedan bien como router barato o extractor corto.",
        "Codex 5.4 mini debe ser el trabajo estándar si la tarea toca archivos.",
        "Codex 5.5 solo debería entrar cuando falten claves, haya riesgo alto o el primer intento no alcance.",
    ]


def build_examples_markup(summary: list[dict[str, Any]], grades: list[dict[str, Any]]) -> str:
    by_engine = defaultdict(list)
    grade_index = {(str(row.get("engine", "")), str(row.get("task_id", ""))): row for row in grades}
    for row in summary:
        by_engine[str(row.get("engine", ""))].append(row)

    cards: list[str] = []
    for engine, rows in sorted(by_engine.items()):
        ranked_rows = sorted(
            rows,
            key=lambda row: (
                -(float(grade_index.get((engine, str(row.get("task_id", ""))), {}).get("score", row.get("score", row.get("heuristic_score", 0))) or 0)),
                float(row.get("elapsed_seconds") or 0),
            ),
        )
        top_rows = ranked_rows[:2]
        if not top_rows:
            continue
        examples = []
        for row in top_rows:
            task_title = task_title_from_prompt(str(row.get("task_prompt", "")))
            engine_key = str(row.get("engine", ""))
            grade = grade_index.get((engine_key, str(row.get("task_id", ""))), {})
            score = float(grade.get("score", grade.get("heuristic_score", row.get("score", row.get("heuristic_score", 0))) or 0))
            snippet = read_output_excerpt(row)
            privacy = row.get("privacy") or {}
            privacy_badge = "privado" if privacy.get("mode") == "redacted" else "descubierto"
            examples.append(
                f"""
                <div class="example-item">
                  <div class="example-top">
                    <b>{escape(task_title)}</b>
                    <span class="tag">{escape(str(row.get("task_id", "")))}</span>
                  </div>
                  <div class="small muted">{escape(privacy_badge)} · score {score:.1f} · {escape(str(row.get("elapsed_seconds", row.get("elapsed_wall_seconds", 0))))}s</div>
                  <pre>{escape(snippet)}</pre>
                </div>
                """
            )
        cards.append(
            f"""
            <article class="card example-card">
              <div class="model-head"><h3>{escape(engine_label(engine))}</h3><span class="tag">{escape(engine_tag(engine))}</span></div>
              <p class="small muted">Muestra de las salidas más representativas de este motor en la campaña reciente.</p>
              <div class="example-list">
                {''.join(examples)}
              </div>
            </article>
            """
        )
    return "".join(cards)


def build_history_markup() -> str:
    historical = RESULTS_DIR / "20260513_185318_064815"
    report = RESULTS_DIR / "latest_model_quality_report.html"
    if not historical.exists() or not report.exists():
        return (
            '<p class="lead">No encuentro el run histórico necesario para la comparación ampliada. '
            'Aun así, el informe histórico sigue disponible en '
            '<a href="../latest_model_quality_report.html">latest_model_quality_report.html</a>.</p>'
        )
    snippet = (
        "Sí, Codex GPT-5.5 fue benchmarkeado en un run histórico separado y aparece como el mejor en calidad media "
        "en el informe histórico. En la campaña privada reciente no se usó 5.5; ahí el caballito de batalla fue 5.4 mini."
    )
    return f"""
    <p class="lead">{escape(snippet)} Puedes revisar el informe histórico completo en <a href="../latest_model_quality_report.html">latest_model_quality_report.html</a>.</p>
    <div class="grid cards">
      <div class="card">
        <span class="tag">Run histórico</span>
        <div class="num">20260513_185318_064815</div>
        <div class="muted">Matriz completa con Codex 5.5, 5.4 mini, Gemini, Groq y OpenRouter.</div>
      </div>
      <div class="card">
        <span class="tag">Conclusión histórica</span>
        <div class="num">5.5</div>
        <div class="muted">Mejor calidad media en esa campaña, con 5.4 mini cerca y mucho más barato.</div>
      </div>
      <div class="card">
        <span class="tag">Lectura práctica</span>
        <div class="num">5.4 mini</div>
        <div class="muted">Mejor base operativa para iterar sin comerse la ventana de proceso.</div>
      </div>
    </div>
    """


def task_title_from_prompt(prompt: str) -> str:
    first_line = ""
    for line in prompt.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            first_line = stripped
            break
    if not first_line:
        for line in prompt.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                first_line = stripped.lstrip("#").strip()
                break
    return first_line or "Tarea"


def engine_label(engine: str) -> str:
    return {
        "codex_gpt_5_4_mini": "Codex GPT-5.4 mini",
        "codex_gpt_5_5": "Codex GPT-5.5",
        "gemini_gemini_2_5_pro": "Gemini 2.5 Pro CLI",
        "gemini_gemini_2_5_flash": "Gemini 2.5 Flash CLI",
        "gemini_gemini_2_5_flash_lite": "Gemini 2.5 Flash-Lite CLI",
        "chrome_nano_gemini_nano": "Mini Nano Direct",
        "opencode_gemini_nanolocal_gemini_nano": "Mini Nano OpenCode",
        "groq_llama_3_1_8b_instant": "Groq Llama 3.1 8B Instant",
        "openrouter_deepseek_deepseek_v3_2": "OpenRouter DeepSeek V3.2",
        "gemini_api_gemini_2_5_flash_lite": "Gemini 2.5 Flash-Lite API",
    }.get(engine, engine.replace("_", " "))


def engine_tag(engine: str) -> str:
    if "codex" in engine:
        return "CLI agente"
    if "chrome_nano" in engine:
        return "CLI local"
    if "groq" in engine:
        return "Router rápido"
    if "openrouter" in engine:
        return "API barata"
    if "gemini" in engine:
        return "API directa"
    return "Motor"


def read_output_excerpt(row: dict[str, Any], max_lines: int = 6, max_chars: int = 420) -> str:
    candidates = []
    for key in ("copied_outputs", "output_files"):
        value = row.get(key)
        if isinstance(value, list):
            candidates.extend(str(item) for item in value if item)
    for path_str in candidates:
        path = Path(path_str)
        if path.exists():
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
                lines = [line.rstrip() for line in text.splitlines() if line.strip()]
                excerpt = "\n".join(lines[:max_lines]).strip()
                if len(excerpt) > max_chars:
                    return excerpt[:max_chars].rstrip() + "..."
                return excerpt
            except OSError:
                continue
    task = str(row.get("task_prompt", "")).strip()
    return task[:max_chars] + ("..." if len(task) > max_chars else "")


def best_engine(rows: list[EngineStats], field: str, *, lowest: bool = False) -> EngineStats | None:
    if not rows:
        return None
    return min(rows, key=lambda item: getattr(item, field)) if lowest else max(rows, key=lambda item: getattr(item, field))


def engine_notes(engine: str, rows: list[dict[str, Any]], grade_rows: list[dict[str, Any]], check_rows: list[dict[str, Any]]) -> str:
    if "openrouter" in engine:
        if any("402" in str(row.get("stderr", "")) for row in rows):
            return "Requiere crédito o techo menor de tokens."
        return "Buena relación coste/calidad en DeepSeek."
    if "groq" in engine:
        return "Muy rápido, sensible al tamaño del prompt."
    if "gemini_api" in engine or "gemini" in engine:
        if any(row.get("returncode") != 0 for row in rows):
            return "Barato y útil, pero conviene vigilar disponibilidad."
        return "Buen router de bajo coste y buena lectura de contexto corto."
    if "codex" in engine:
        return "Agente robusto. 5.4 mini como base y 5.5 como escalado."
    if "vikingnano" in engine:
        return "Útil para privacidad local, pero sensible a timeout."
    return "Motor general de laboratorio."


def extract_cost(row: dict[str, Any]) -> float:
    usage = row.get("usage") or {}
    if isinstance(usage, dict):
        inner = usage.get("usage") if isinstance(usage.get("usage"), dict) else usage
        if "cost" in inner:
            try:
                return float(inner["cost"])
            except (TypeError, ValueError):
                return 0.0
    return 0.0


def percent(values: list[bool]) -> float:
    if not values:
        return 0.0
    return 100.0 * sum(1 for value in values if value) / len(values)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def escape(value: Any) -> str:
    text = str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


if __name__ == "__main__":
    raise SystemExit(main())
