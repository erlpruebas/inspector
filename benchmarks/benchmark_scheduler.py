from __future__ import annotations

import argparse
import json
import shutil
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from env_utils import load_env_files
from benchmark_context import prompt_for_execution
from engines.engine_factory import create_engine
from privacy_guard import DEFAULT_STORE_PATH, MiniNanoPrivacyReviewer, apply_privacy_to_workdir
from expected_key_check import build_checks
from grade_outputs import build_grades
from memory_guard import wait_for_memory_budget
from task_loader import RESULTS_DIR, TASKS_FILE, BenchmarkTask, load_tasks, prefixed_result_name, prepare_workdir


TRANSIENT_MARKERS = (
    "429",
    "503",
    "524",
    "rate limit",
    "ratelimit",
    "quota",
    "too many requests",
    "high demand",
    "unavailable",
    "overloaded",
    "capacity",
    "temporarily",
    "try again later",
    "resource_exhausted",
    "timed out",
    "timeouterror",
    "gateway timeout",
    "api error 524",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run benchmark jobs with deferred retries for rate limits/capacity errors.")
    parser.add_argument("--engine", action="append", default=[], help="Engine spec. Can be repeated.")
    parser.add_argument("--engine-matrix", default="", help="JSON file with grouped engine specs.")
    parser.add_argument("--job", action="append", default=[], help="Exact job as engine::task_id. Can be repeated.")
    parser.add_argument("--tasks-file", default=str(TASKS_FILE))
    parser.add_argument("--task", action="append", default=[], help="Task id. Can be repeated.")
    parser.add_argument("--level", action="append", default=[], help="Task level/difficulty filter, e.g. L1 or 3.")
    parser.add_argument("--cooldown-seconds", type=int, default=7200)
    parser.add_argument("--rest-seconds", type=int, default=0, help="Pause between successful jobs.")
    parser.add_argument("--cycle-sleep-seconds", type=int, default=7200, help="Sleep between cycles when pending jobs are deferred.")
    parser.add_argument(
        "--min-free-memory-mb",
        type=int,
        default=512,
        help="Pause before launching a job when free RAM drops below this threshold. Use 0 to disable.",
    )
    parser.add_argument(
        "--memory-poll-seconds",
        type=int,
        default=30,
        help="How long to sleep between memory checks while the guard is active.",
    )
    parser.add_argument("--once", action="store_true", help="Run currently due jobs once and exit.")
    parser.add_argument("--state", default="")
    parser.add_argument("--resume", action="store_true", help="Resume an existing scheduler state file instead of creating a new run.")
    parser.add_argument("--no-grade", action="store_true", help="Do not generate expected-key checks and grades at the end.")
    parser.add_argument("--heuristic-only", action="store_true", help="Generate grades without calling the LLM judge.")
    parser.add_argument("--privacy-mode", choices=("clear", "mixed", "redacted"), default="clear")
    parser.add_argument("--privacy-review", choices=("none", "mini-nano"), default="none")
    parser.add_argument("--privacy-map", default=str(DEFAULT_STORE_PATH))
    args = parser.parse_args()

    load_env_files()
    privacy_review = MiniNanoPrivacyReviewer.from_env() if args.privacy_review == "mini-nano" else None
    privacy_map = Path(args.privacy_map)
    tasks_file = Path(args.tasks_file)
    if args.resume and args.state and Path(args.state).exists():
        state_path = Path(args.state)
        state = json.loads(state_path.read_text(encoding="utf-8"))
        run_dir = Path(state["run_dir"])
    else:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        run_dir = RESULTS_DIR / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        state_path = Path(args.state) if args.state else run_dir / "scheduler_state.json"
        jobs = build_jobs(args, tasks_file)
        state = {"run_dir": str(run_dir), "jobs": jobs, "completed": [], "deferred": [], "failed": []}
        save_state(state_path, state)

    while True:
        now = time.time()
        due = [job for job in state["jobs"] if not job.get("done") and float(job.get("next_run_at", 0)) <= now]
        if not due:
            if args.once or all(job.get("done") for job in state["jobs"]):
                break
            save_state(state_path, state)
            time.sleep(max(1, args.cycle_sleep_seconds))
            continue

        for job in due:
            wait_for_memory_budget(args.min_free_memory_mb, args.memory_poll_seconds)
            print(f"[run] {job_key(job)} attempt={int(job.get('attempts', 0)) + 1}", flush=True)
            state["running"] = {"job": job_key(job), "at": utc_now()}
            save_state(state_path, state)
            result_payload = run_job(
                job,
                run_dir,
                tasks_file,
                privacy_mode=args.privacy_mode,
                privacy_review=privacy_review,
                privacy_map=privacy_map,
            )
            transient = transient_error(result_payload)
            if transient:
                job["attempts"] = int(job.get("attempts", 0)) + 1
                job["next_run_at"] = time.time() + args.cooldown_seconds
                state["deferred"].append(
                    {
                        "job": job_key(job),
                        "at": utc_now(),
                        "next_run_at": utc_from_timestamp(job["next_run_at"]),
                        "reason": transient,
                    }
                )
                print(
                    f"[defer] {job_key(job)} reason={transient} next={utc_from_timestamp(job['next_run_at'])}",
                    flush=True,
                )
            else:
                job["done"] = True
                if result_payload.get("returncode") == 0 and not result_payload.get("timed_out"):
                    state["completed"].append({"job": job_key(job), "at": utc_now()})
                    print(f"[done] {job_key(job)}", flush=True)
                else:
                    state["failed"].append({"job": job_key(job), "at": utc_now(), "returncode": result_payload.get("returncode")})
                    print(f"[fail] {job_key(job)} returncode={result_payload.get('returncode')}", flush=True)
            state["running"] = None
            save_state(state_path, state)
            if args.rest_seconds:
                time.sleep(args.rest_seconds)

        if args.once:
            break

    write_summary_from_results(run_dir)
    if not args.no_grade:
        write_checks_and_grades(run_dir, tasks_file, args.heuristic_only)
    save_state(state_path, state)
    print(run_dir)
    print(state_path)
    return 0


def build_jobs(args: argparse.Namespace, tasks_file: Path) -> list[dict[str, Any]]:
    if args.job:
        jobs: list[dict[str, Any]] = []
        for raw_job in args.job:
            if "::" not in raw_job:
                raise ValueError(f"Invalid --job value {raw_job!r}; expected engine::task_id")
            engine, task_id = raw_job.rsplit("::", 1)
            jobs.append({"engine": engine, "task_id": task_id, "next_run_at": 0, "attempts": 0, "done": False})
        return jobs

    engines = [*args.engine]
    if args.engine_matrix:
        engines.extend(load_engine_matrix(Path(args.engine_matrix)))
    if not engines:
        engines = ["codex:gpt-5.5", "codex:gpt-5.4-mini", "gemini:gemini-2.5-flash-lite", "openrouter:deepseek/deepseek-v3.2", "lmstudio:qwen3.5-0.8b:2"]
    tasks = select_tasks(load_tasks(tasks_file), args.task, args.level)
    return [
        {"engine": engine, "task_id": task.id, "next_run_at": 0, "attempts": 0, "done": False}
        for task in tasks
        for engine in engines
    ]


def load_engine_matrix(path: Path) -> list[str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    engines: list[str] = []
    for group in raw:
        if isinstance(group, dict):
            engines.extend(str(item) for item in group.get("engines", []))
        elif isinstance(group, str):
            engines.append(group)
    return engines


def select_tasks(tasks: list[BenchmarkTask], task_ids: list[str], levels: list[str]) -> list[BenchmarkTask]:
    selected = tasks
    if task_ids:
        requested = set(task_ids)
        selected = [task for task in selected if task.id in requested]
    if levels:
        normalized = {level.upper() if level.upper().startswith("L") else f"L{level}" for level in levels}
        selected = [task for task in selected if task.level.upper() in normalized]
    return selected


def run_job(
    job: dict[str, Any],
    run_dir: Path,
    tasks_file: Path,
    *,
    privacy_mode: str = "clear",
    privacy_review: MiniNanoPrivacyReviewer | None = None,
    privacy_map: Path | None = None,
) -> dict[str, Any]:
    tasks = {task.id: task for task in load_tasks(tasks_file)}
    task = tasks[job["task_id"]]
    engine = create_engine(job["engine"])
    workdir = prepare_workdir(task, engine.name, run_dir.name)
    privacy_result = None
    if privacy_mode != "clear":
        privacy_result = apply_privacy_to_workdir(
            workdir,
            mode=privacy_mode,
            store_path=privacy_map or DEFAULT_STORE_PATH,
            reviewer=privacy_review,
        )
    execution_prompt = prompt_for_execution(task, workdir)
    try:
        result = engine.run(task.id, execution_prompt, workdir, task.expected_outputs)
    except Exception as exc:
        from engines.base_engine import EngineResult

        result = EngineResult(
            engine=engine.name,
            task_id=task.id,
            returncode=1,
            stdout="",
            stderr=f"{type(exc).__name__}: {exc}",
            elapsed_seconds=0,
            timed_out=False,
            model=getattr(engine, "model", ""),
            error_type=type(exc).__name__,
        )
    copied = copy_prefixed_outputs(result.output_files, run_dir, engine.name, task.id)
    payload = asdict(result)
    payload["engine_spec"] = job["engine"]
    payload["copied_outputs"] = [str(path) for path in copied]
    payload["task_prompt"] = task.prompt
    payload["execution_prompt"] = execution_prompt
    payload["workdir"] = str(workdir)
    payload["privacy"] = privacy_result.to_dict() if privacy_result is not None else {"mode": "clear"}
    (run_dir / f"{engine.name}_{task.id}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def copy_prefixed_outputs(output_files: list[str], run_dir: Path, engine_name: str, task_id: str) -> list[Path]:
    copied: list[Path] = []
    for output in output_files:
        source = Path(output)
        if source.exists() and source.is_file():
            target = run_dir / prefixed_result_name(engine_name, task_id, source.name)
            shutil.copy2(source, target)
            copied.append(target)
    return copied


def transient_error(result: dict[str, Any]) -> str:
    if result.get("timed_out"):
        return "timeout"
    if result.get("returncode") == 0:
        return ""
    text = " ".join(str(result.get(key, "")) for key in ("stdout", "stderr"))
    text += " " + json.dumps(result.get("usage", {}), ensure_ascii=False)
    lowered = text.casefold()
    for marker in TRANSIENT_MARKERS:
        if marker in lowered:
            return marker
    return ""


def write_summary_from_results(run_dir: Path) -> None:
    rows = []
    for path in sorted(run_dir.glob("*.json")):
        if path.name in {"summary.json", "scheduler_state.json"}:
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(raw, dict) and "task_id" in raw and "engine" in raw:
            rows.append(raw)
    (run_dir / "summary.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def write_checks_and_grades(run_dir: Path, tasks_file: Path, heuristic_only: bool) -> None:
    try:
        checks = build_checks(run_dir, tasks_file)
        (run_dir / "expected_key_checks.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        (run_dir / "expected_key_checks_error.txt").write_text(f"{type(exc).__name__}: {exc}", encoding="utf-8")
    try:
        grades = build_grades(run_dir, tasks_file, heuristic_only=heuristic_only)
        (run_dir / "grades.json").write_text(json.dumps(grades, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        (run_dir / "grades_error.txt").write_text(f"{type(exc).__name__}: {exc}", encoding="utf-8")


def job_key(job: dict[str, Any]) -> str:
    return f"{job['engine']}::{job['task_id']}"


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def utc_from_timestamp(value: float) -> str:
    return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
