from __future__ import annotations

import argparse
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from env_utils import google_api_key, load_env_files
from task_loader import RESULTS_DIR, load_tasks
from token_accounting import record_usage


def main() -> int:
    parser = argparse.ArgumentParser(description="Grade benchmark outputs with expected keys and an optional Gemini judge.")
    parser.add_argument("--run-dir", default="")
    parser.add_argument("--tasks-file", default="benchmarks/tasks/assistant_tasks.json")
    parser.add_argument("--model", default=os.getenv("BENCH_JUDGE_MODEL", "gemini-2.5-flash-lite"))
    parser.add_argument("--heuristic-only", action="store_true")
    args = parser.parse_args()

    load_env_files()
    run_dir = Path(args.run_dir) if args.run_dir else latest_run_dir()
    grades = build_grades(run_dir, Path(args.tasks_file), model=args.model, heuristic_only=args.heuristic_only)

    output = run_dir / "grades.json"
    output.write_text(json.dumps(grades, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output)
    return 0


def build_grades(
    run_dir: Path,
    tasks_file: Path,
    model: str | None = None,
    heuristic_only: bool = False,
) -> list[dict[str, Any]]:
    model = model or os.getenv("BENCH_JUDGE_MODEL", "gemini-2.5-flash-lite")
    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        raise SystemExit(f"Missing summary file: {summary_path}")

    tasks = {task.id: task for task in load_tasks(tasks_file)}
    rows = json.loads(summary_path.read_text(encoding="utf-8"))
    api_key = judge_api_key(model)
    use_judge = bool(api_key) and not heuristic_only

    grades: list[dict[str, Any]] = []
    for row in rows:
        task_id = str(row.get("task_id", ""))
        engine = str(row.get("engine", ""))
        task = tasks.get(task_id)
        outputs = [Path(path) for path in row.get("copied_outputs", [])]
        answer = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in outputs if path.exists())
        expected_keys = list(task.expected_keys if task else [])
        missing = missing_keys(answer, expected_keys)
        heuristic_score = score_from_keys(expected_keys, missing, row)
        grade = {
            "task_id": task_id,
            "engine": engine,
            "engine_spec": row.get("engine_spec", ""),
            "passed_expected_keys": not missing and row.get("returncode") == 0 and not row.get("timed_out"),
            "expected_keys": expected_keys,
            "missing_keys": missing,
            "heuristic_score": heuristic_score,
            "score": heuristic_score,
            "comment": heuristic_comment(expected_keys, missing, row),
            "judge_model": "",
        }
        if use_judge and task and answer.strip() and row.get("returncode") == 0 and not row.get("timed_out"):
            try:
                judged = judge_single(model, api_key or "", task.prompt, expected_keys, answer, usage_log_path=run_dir / "token_usage.jsonl", task_id=task_id, engine=engine)
            except Exception as exc:
                judged = {}
                grade["judge_error"] = f"{type(exc).__name__}: {exc}"
            if judged:
                grade.update(judged)
                grade["judge_model"] = model
        grades.append(grade)
    return grades


def latest_run_dir() -> Path:
    candidates = [path for path in RESULTS_DIR.iterdir() if path.is_dir()]
    if not candidates:
        raise SystemExit("No benchmark runs found")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def missing_keys(answer: str, expected_keys: list[str]) -> list[str]:
    lowered = normalize(answer)
    return [key for key in expected_keys if not any(normalize(variant) in lowered for variant in key_variants(key))]


def normalize(value: Any) -> str:
    text = str(value).casefold()
    replacements = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u",
        "ñ": "n",
        "Ã¡": "a",
        "Ã©": "e",
        "Ã­": "i",
        "Ã³": "o",
        "Ãº": "u",
        "Ã±": "n",
    }
    for source, target in replacements.items():
        text = text.replace(source.casefold(), target)
    return text


def key_variants(key: str) -> list[str]:
    variants = [key]
    months = {
        "enero": "01",
        "febrero": "02",
        "marzo": "03",
        "abril": "04",
        "mayo": "05",
        "junio": "06",
        "julio": "07",
        "agosto": "08",
        "septiembre": "09",
        "octubre": "10",
        "noviembre": "11",
        "diciembre": "12",
    }
    parts = normalize(key).split()
    if len(parts) >= 3 and parts[1] == "de" and parts[2] in months:
        day = parts[0].zfill(2)
        month = months[parts[2]]
        variants.extend([f"{day}/{month}", f"2026-{month}-{day}", f"{day}-{month}-2026"])
    return variants


def score_from_keys(expected_keys: list[str], missing: list[str], row: dict[str, Any]) -> float:
    if row.get("returncode") != 0 or row.get("timed_out"):
        return 0.0
    if not expected_keys:
        return 6.0
    found = len(expected_keys) - len(missing)
    return round(10.0 * found / len(expected_keys), 1)


def heuristic_comment(expected_keys: list[str], missing: list[str], row: dict[str, Any]) -> str:
    if row.get("timed_out"):
        return "Timeout durante la ejecución."
    if row.get("returncode") != 0:
        return f"Ejecución fallida con returncode={row.get('returncode')}."
    if not expected_keys:
        return "Ejecución completada; no hay claves esperadas para una nota automática fina."
    if not missing:
        return "Incluye todas las claves esperadas."
    return "Faltan claves esperadas: " + ", ".join(missing)


def judge_api_key(model: str) -> str:
    if model.startswith("openrouter:"):
        return os.getenv("OPENROUTER_API_KEY", "").strip()
    if model.startswith("openai:"):
        return os.getenv("OPENAI_API_KEY", "").strip()
    return google_api_key()


def judge_single(
    model: str,
    api_key: str,
    task_prompt: str,
    expected_keys: list[str],
    answer: str,
    *,
    usage_log_path: Path | None = None,
    task_id: str = "",
    engine: str = "",
) -> dict[str, Any]:
    prompt = f"""
Eres un juez técnico de una arena de IA.
Evalúa una respuesta frente a la tarea original.
Ten en cuenta exactitud, completitud, formato, trazabilidad y si inventa datos.
Devuelve solo JSON válido con estos campos:
- score: número de 1 a 10
- passed: boolean
- comment: comentario breve y específico en español
- strengths: lista corta
- issues: lista corta

Tarea original:
{task_prompt}

Claves esperadas:
{json.dumps(expected_keys, ensure_ascii=False)}

Respuesta evaluada:
{answer[:12000]}
""".strip()
    if model.startswith("openrouter:") or model.startswith("openai:"):
        payload = call_openai_compatible_judge(model, api_key, prompt)
        text = extract_openai_content(payload)
        if usage_log_path is not None:
            provider, model_name = model.split(":", 1)
            record_usage(
                usage_log_path,
                source="benchmark_judge",
                component="judge",
                provider=provider,
                model=model_name,
                operation="judge",
                usage=payload,
                prompt_text=prompt,
                completion_text=text,
                task_id=task_id,
                metadata={"engine": engine, "judge_model": model},
            )
        parsed = parse_json_object(text)
        if not parsed:
            return {}
        return normalize_grade(parsed)
    payload = call_gemini(model, api_key, prompt)
    text = extract_text(payload)
    if usage_log_path is not None:
        record_usage(
            usage_log_path,
            source="benchmark_judge",
            component="judge",
            provider="gemini",
            model=model,
            operation="judge",
            usage=payload,
            prompt_text=prompt,
            completion_text=text,
            task_id=task_id,
            metadata={"engine": engine, "judge_model": model},
        )
    parsed = parse_json_object(text)
    if not parsed:
        return {}
    return normalize_grade(parsed)


def call_openai_compatible_judge(model: str, api_key: str, prompt: str) -> dict[str, Any]:
    provider, model_name = model.split(":", 1)
    if provider == "openrouter":
        url = "https://openrouter.ai/api/v1/chat/completions"
    elif provider == "openai":
        url = "https://api.openai.com/v1/chat/completions"
    else:
        raise ValueError(f"Unsupported judge provider: {provider}")
    body = json.dumps(
        {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        },
        ensure_ascii=False,
    ).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost/ai-arena",
        "X-Title": "AI Arena Judge",
    }
    request = urllib.request.Request(url, data=body, method="POST", headers=headers)
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def extract_openai_content(payload: dict[str, Any]) -> str:
    choices = payload.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    return str(message.get("content", "")).strip()


def call_gemini(model: str, api_key: str, prompt: str) -> dict[str, Any]:
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        + urllib.parse.quote(model, safe="")
        + ":generateContent?key="
        + urllib.parse.quote(api_key, safe="")
    )
    body = json.dumps(
        {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def extract_text(payload: dict[str, Any]) -> str:
    candidates = payload.get("candidates") or []
    if not candidates:
        return ""
    parts = (((candidates[0] or {}).get("content") or {}).get("parts") or [])
    return "".join(str(part.get("text", "")) for part in parts if isinstance(part, dict)).strip()


def parse_json_object(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return {}
        parsed = json.loads(match.group(0))
    return parsed if isinstance(parsed, dict) else {}


def normalize_grade(raw: dict[str, Any]) -> dict[str, Any]:
    try:
        score = float(raw.get("score", 0))
    except (TypeError, ValueError):
        score = 0.0
    score = round(max(1.0, min(10.0, score)), 1)
    return {
        "score": score,
        "passed_expected_keys": bool(raw.get("passed", score >= 7)),
        "comment": fix_mojibake(str(raw.get("comment", "")).strip()),
        "strengths": [fix_mojibake(str(item)) for item in raw.get("strengths", [])] if isinstance(raw.get("strengths"), list) else [],
        "issues": [fix_mojibake(str(item)) for item in raw.get("issues", [])] if isinstance(raw.get("issues"), list) else [],
    }


def fix_mojibake(text: str) -> str:
    if not any(marker in text for marker in ("Ã", "Â", "ï¿½")):
        return text
    try:
        return text.encode("latin-1").decode("utf-8")
    except UnicodeError:
        return text


if __name__ == "__main__":
    raise SystemExit(main())
