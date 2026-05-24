from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from task_loader import RESULTS_DIR, load_tasks


def main() -> int:
    parser = argparse.ArgumentParser(description="Judge successful benchmark outputs with Codex CLI.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--tasks-file", default="benchmarks/tasks/assistant_tasks.json")
    parser.add_argument("--model", default="gpt-5.5")
    parser.add_argument("--output", default="")
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument("--max-items", type=int, default=0)
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    output = Path(args.output) if args.output else run_dir / f"codex_{safe_label(args.model)}_judgements.json"
    existing = load_json(output, default=[])
    completed = {(row.get("engine"), row.get("task_id")) for row in existing if isinstance(row, dict)}

    tasks = {task.id: task for task in load_tasks(Path(args.tasks_file))}
    rows = load_json(run_dir / "summary.json", default=[])
    command = resolve_codex_command()

    count = 0
    for row in rows:
        task_id = str(row.get("task_id", ""))
        engine = str(row.get("engine", ""))
        if (engine, task_id) in completed:
            continue
        if row.get("returncode") != 0 or row.get("timed_out"):
            continue
        answer = read_answer(row)
        task = tasks.get(task_id)
        if not answer.strip() or task is None:
            continue
        judgement = judge_with_codex(command, args.model, task.prompt, task.expected_keys, answer, run_dir, args.timeout_seconds)
        existing.append({"engine": engine, "task_id": task_id, "judge_model": f"codex:{args.model}", **judgement})
        output.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
        count += 1
        if args.max_items and count >= args.max_items:
            break

    merge_into_grades(run_dir, existing)
    print(output)
    print(f"judged_now={count}")
    return 0


def judge_with_codex(
    command: list[str],
    model: str,
    task_prompt: str,
    expected_keys: list[str],
    answer: str,
    cwd: Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    prompt = f"""
Eres un juez tecnico de una arena de IA.
Evalua una respuesta frente a la tarea original.
Ten en cuenta exactitud, completitud, formato, trazabilidad y si inventa datos.
Devuelve solo JSON valido con estos campos:
- score: numero de 1 a 10
- passed: boolean
- comment: comentario breve y especifico en espanol
- strengths: lista corta
- issues: lista corta

Tarea original:
{task_prompt}

Claves esperadas:
{json.dumps(expected_keys, ensure_ascii=False)}

Respuesta evaluada:
{answer[:12000]}
""".strip()
    started = time.monotonic()
    cwd = cwd.resolve()
    args = [*command, "--ask-for-approval", "never", "--sandbox", "workspace-write", "--cd", str(cwd), "exec", "--model", model, "--json", "--skip-git-repo-check", prompt]
    try:
        process = subprocess.run(
            args,
            cwd=str(cwd),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "score": 0.0,
            "passed_expected_keys": False,
            "comment": "Timeout del juez Codex.",
            "strengths": [],
            "issues": ["timeout"],
            "judge_error": f"TimeoutExpired after {timeout_seconds}s",
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }
    text = codex_text_from_stdout(process.stdout or "") or process.stdout or ""
    parsed = parse_json_object(text)
    if process.returncode != 0 or not parsed:
        return {
            "score": 0.0,
            "passed_expected_keys": False,
            "comment": "El juez Codex no devolvio JSON valido.",
            "strengths": [],
            "issues": ["judge_invalid_json"],
            "judge_error": (process.stderr or text)[-2000:],
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }
    grade = normalize_grade(parsed)
    grade["elapsed_seconds"] = round(time.monotonic() - started, 3)
    return grade


def merge_into_grades(run_dir: Path, judgements: list[dict[str, Any]]) -> None:
    grades_path = run_dir / "grades.json"
    grades = load_json(grades_path, default=[])
    by_key = {(row.get("engine"), row.get("task_id")): row for row in judgements if isinstance(row, dict)}
    for grade in grades:
        replacement = by_key.get((grade.get("engine"), grade.get("task_id")))
        if not replacement:
            continue
        for key in ("score", "passed_expected_keys", "comment", "strengths", "issues", "judge_model", "judge_error"):
            if key in replacement:
                grade[key] = replacement[key]
    grades_path.write_text(json.dumps(grades, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve_codex_command() -> list[str]:
    command_text = os.getenv("BENCH_CODEX_COMMAND", os.getenv("ORCH_CODEX_COMMAND", "codex"))
    command = shlex.split(command_text, posix=False)
    if command and (Path(command[0]).exists() or shutil.which(command[0])):
        return command
    if command and command[0].lower() == "codex":
        found = find_codex()
        if found:
            return [found, *command[1:]]
    return command or ["codex"]


def find_codex() -> str:
    candidates: list[Path] = []
    home = os.getenv("USERPROFILE", "")
    if home:
        candidates.extend(Path(home).glob(".vscode/extensions/openai.chatgpt-*/bin/windows-x86_64/codex.exe"))
        candidates.extend(Path(home).glob(".vscode-insiders/extensions/openai.chatgpt-*/bin/windows-x86_64/codex.exe"))
    for name in ("codex.cmd", "codex.exe", "codex"):
        resolved = shutil.which(name)
        if resolved:
            return resolved
    existing = [path for path in candidates if path.exists()]
    return str(max(existing, key=lambda path: path.stat().st_mtime)) if existing else ""


def read_answer(row: dict[str, Any]) -> str:
    chunks: list[str] = []
    for value in row.get("copied_outputs") or []:
        path = Path(value)
        if path.exists() and path.is_file():
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n\n".join(chunks)


def parse_json_object(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return {}
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}
    return parsed if isinstance(parsed, dict) else {}


def codex_text_from_stdout(stdout: str) -> str:
    messages: list[str] = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get("item")
        if isinstance(item, dict) and item.get("type") == "agent_message" and item.get("text"):
            messages.append(str(item["text"]))
    return "\n\n".join(messages)


def normalize_grade(raw: dict[str, Any]) -> dict[str, Any]:
    try:
        score = float(raw.get("score", 0))
    except (TypeError, ValueError):
        score = 0.0
    score = round(max(1.0, min(10.0, score)), 1)
    return {
        "score": score,
        "passed_expected_keys": bool(raw.get("passed", score >= 7)),
        "comment": str(raw.get("comment", "")).strip(),
        "strengths": [str(item) for item in raw.get("strengths", [])] if isinstance(raw.get("strengths"), list) else [],
        "issues": [str(item) for item in raw.get("issues", [])] if isinstance(raw.get("issues"), list) else [],
    }


def safe_label(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower() or "model"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


if __name__ == "__main__":
    raise SystemExit(main())
