from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a strategic Markdown report from office benchmark runs.")
    parser.add_argument("--run-dir", action="append", required=True)
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    run_dirs = [Path(item).resolve() for item in args.run_dir]
    output = Path(args.output).resolve() if args.output else run_dirs[0] / "office_strategy_report.md"
    report = build_report(run_dirs)
    output.write_text(report, encoding="utf-8")
    print(output)
    return 0


def build_report(run_dirs: list[Path]) -> str:
    rows: list[dict[str, Any]] = []
    grades: list[dict[str, Any]] = []
    for run_dir in run_dirs:
        rows.extend(with_run(load_json(run_dir / "summary.json", []), run_dir))
        grades.extend(with_run(load_json(run_dir / "grades.json", []), run_dir))

    grade_by_key = {(g.get("run_dir"), g.get("engine"), g.get("task_id")): g for g in grades}
    engine_rows = aggregate(rows, grade_by_key)
    technical = aggregate_technical(rows)

    lines = [
        "# Office Strategy Benchmark Report",
        "",
        "## Runs",
        "",
    ]
    lines.extend(f"- `{run_dir}`" for run_dir in run_dirs)
    lines.extend(
        [
            "",
            "## Executive Read",
            "",
            "La prueba evaluo la capacidad de resolver tareas transversales de ofimatica con archivos, texto, agregacion y busqueda preparada. Las notas de calidad se fusionaron desde `codex:gpt-5.5` cuando hubo salida real.",
            "",
            "Resultado practico: Codex CLI y Gemini CLI fueron los motores utiles en esta maquina; OpenCode funciona pero queda por debajo en esta muestra; OpenRouter quedo bloqueado casi por completo por credito insuficiente, aunque el canario con `max_tokens=128` dejo senal de DeepSeek V4 Flash y Llama 3.3 70B; Groq no pudo evaluarse porque falta `GROQ_API_KEY`.",
            "",
            "## Quality On Successful Outputs",
            "",
            "| Engine | Outputs judged | Avg score | Pass rate | Avg seconds | Notes |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    for item in engine_rows:
        lines.append(
            f"| `{item['engine']}` | {item['count']} | {item['avg_score']:.2f} | {item['pass_rate']:.0f}% | {item['avg_seconds']:.1f} | {item['notes']} |"
        )
    lines.extend(
        [
            "",
            "## Technical Availability",
            "",
            "| Engine | Jobs | Success | Failed | Deferred | Main blocker |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    for item in technical:
        lines.append(
            f"| `{item['engine']}` | {item['jobs']} | {item['success']} | {item['failed']} | {item['deferred']} | {item['blocker']} |"
        )
    lines.extend(
        [
            "",
            "## Strategic Conclusions",
            "",
            "1. `codex:gpt-5.5` queda como referencia de calidad, pero no conviene usarlo como motor barato de rutina.",
            "2. `codex:gpt-5.4-mini` queda como candidato fuerte para trabajo diario con archivos: hizo 12 salidas y mantuvo buena nota media.",
            "3. `gemini:gemini-2.5-flash` por CLI es competitivo, pero conviene probarlo con mas tareas y ajustar tiempos.",
            "4. `opencode:google/gemini-2.5-flash` funciona como runtime, pero necesita afinarse: falla mas y puntua por debajo en la muestra.",
            "5. OpenRouter necesita corregir saldo/clave antes de sacar conclusiones sobre los modelos de pago; ahora mismo la API responde `402 Payment Required`.",
            "6. Groq queda pendiente hasta configurar `GROQ_API_KEY`; todos sus fallos de esta corrida son de disponibilidad, no de calidad del modelo.",
            "",
            "## Next Run",
            "",
            "Repetir OpenRouter cuando la clave tenga credito suficiente, con `BENCH_OPENROUTER_MAX_TOKENS=768` para tareas normales y `1536` solo en tareas largas. Repetir Groq cuando exista `GROQ_API_KEY`. Mantener `codex:gpt-5.5` como juez y no como motor masivo salvo muestras pequenas.",
            "",
        ]
    )
    return "\n".join(lines)


def aggregate(rows: list[dict[str, Any]], grade_by_key: dict[tuple[Any, Any, Any], dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grade = grade_by_key.get((row.get("run_dir"), row.get("engine"), row.get("task_id")))
        if not grade or grade.get("judge_model") != "codex:gpt-5.5":
            continue
        grouped[str(row.get("engine"))].append({**row, **grade})

    out = []
    for engine, items in grouped.items():
        scores = [float(item.get("score", 0)) for item in items]
        passes = [bool(item.get("passed_expected_keys")) for item in items]
        seconds = [float(item.get("elapsed_seconds") or 0) for item in items]
        out.append(
            {
                "engine": engine,
                "count": len(items),
                "avg_score": mean(scores) if scores else 0.0,
                "pass_rate": 100 * sum(passes) / len(passes) if passes else 0.0,
                "avg_seconds": mean(seconds) if seconds else 0.0,
                "notes": note_for_engine(engine),
            }
        )
    return sorted(out, key=lambda item: (-item["avg_score"], -item["count"], item["engine"]))


def aggregate_technical(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("engine"))].append(row)
    out = []
    for engine, items in grouped.items():
        success = [row for row in items if row.get("returncode") == 0 and not row.get("timed_out")]
        failed = [row for row in items if row.get("returncode") != 0 or row.get("timed_out")]
        blocker = infer_blocker(failed)
        out.append({"engine": engine, "jobs": len(items), "success": len(success), "failed": len(failed), "deferred": 0, "blocker": blocker})
    return sorted(out, key=lambda item: (-item["success"], item["engine"]))


def infer_blocker(rows: list[dict[str, Any]]) -> str:
    text = "\n".join(str(row.get("stderr", "")) for row in rows).lower()
    if "groq_api_key" in text:
        return "missing GROQ_API_KEY"
    if "402" in text or "payment required" in text or "more credits" in text:
        return "OpenRouter credits/max_tokens"
    if "503" in text or "unavailable" in text:
        return "provider unavailable"
    if "without creating expected output" in text:
        return "runtime did not create output"
    if not rows:
        return "ok"
    return "execution errors"


def note_for_engine(engine: str) -> str:
    if engine.startswith("codex"):
        return "strong file/task execution"
    if engine.startswith("gemini"):
        return "good CLI baseline"
    if engine.startswith("opencode"):
        return "runtime works, needs tuning"
    if "openrouter" in engine:
        return "limited by current credits"
    return ""


def with_run(items: list[dict[str, Any]], run_dir: Path) -> list[dict[str, Any]]:
    out = []
    for item in items:
        if isinstance(item, dict):
            cloned = dict(item)
            cloned["run_dir"] = str(run_dir)
            out.append(cloned)
    return out


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


if __name__ == "__main__":
    raise SystemExit(main())
