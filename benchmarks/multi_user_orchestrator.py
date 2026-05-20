from __future__ import annotations

import argparse
import json
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from env_utils import load_env_files
from benchmark_context import prompt_for_execution
try:  # pragma: no cover - convenience for direct execution
    from privacy_guard import DEFAULT_STORE_PATH, MiniNanoPrivacyReviewer, apply_privacy_to_workdir
except ImportError:  # pragma: no cover
    from benchmarks.privacy_guard import DEFAULT_STORE_PATH, MiniNanoPrivacyReviewer, apply_privacy_to_workdir
from expected_key_check import build_checks
from grade_outputs import build_grades
from memory_guard import wait_for_memory_budget
from task_loader import RESULTS_DIR, TASKS_FILE, BenchmarkTask, load_tasks, prefixed_result_name, prepare_workdir_in_root
from engines.engine_factory import create_engine
from engines.base_engine import EngineResult


def main() -> int:
    parser = argparse.ArgumentParser(description="Run isolated benchmark workers in parallel user lanes.")
    parser.add_argument("--engine", action="append", default=[], help="Engine spec. Can be repeated.")
    parser.add_argument("--tasks-file", default=str(TASKS_FILE))
    parser.add_argument("--task", action="append", default=[], help="Task id. Can be repeated.")
    parser.add_argument("--level", action="append", default=[], help="Task level filter. Can be repeated.")
    parser.add_argument("--users", type=int, default=4, help="Number of isolated user lanes.")
    parser.add_argument("--cooldown-seconds", type=int, default=7200)
    parser.add_argument("--rest-seconds", type=int, default=0)
    parser.add_argument("--min-free-memory-mb", type=int, default=512)
    parser.add_argument("--memory-poll-seconds", type=int, default=30)
    parser.add_argument("--privacy-mode", choices=("clear", "mixed", "redacted"), default="clear")
    parser.add_argument("--privacy-review", choices=("none", "mini-nano"), default="none")
    parser.add_argument("--privacy-map", default=str(DEFAULT_STORE_PATH))
    parser.add_argument("--no-grade", action="store_true")
    parser.add_argument("--heuristic-only", action="store_true")
    parser.add_argument("--shuffle", action="store_true", help="Shuffle tasks before assigning them to lanes.")
    args = parser.parse_args()

    run_dir = run_multi_user_benchmark(
        engine_names=args.engine or ["codex:gpt-5.4-mini", "gemini_api:gemini-2.5-flash-lite", "groq:llama-3.1-8b-instant", "openrouter:deepseek/deepseek-v3.2"],
        tasks_file=Path(args.tasks_file),
        task_ids=args.task or None,
        levels=args.level or None,
        users=max(1, int(args.users)),
        privacy_mode=args.privacy_mode,
        privacy_review=args.privacy_review,
        privacy_map=Path(args.privacy_map),
        cooldown_seconds=args.cooldown_seconds,
        rest_seconds=args.rest_seconds,
        min_free_memory_mb=args.min_free_memory_mb,
        memory_poll_seconds=args.memory_poll_seconds,
        shuffle=args.shuffle,
        no_grade=args.no_grade,
        heuristic_only=args.heuristic_only,
    )
    print(run_dir)
    return 0


def run_multi_user_benchmark(
    engine_names: list[str],
    *,
    tasks_file: Path = TASKS_FILE,
    task_ids: list[str] | None = None,
    levels: list[str] | None = None,
    users: int = 4,
    privacy_mode: str = "clear",
    privacy_review: str = "none",
    privacy_map: Path | None = None,
    cooldown_seconds: int = 7200,
    rest_seconds: int = 0,
    min_free_memory_mb: int = 512,
    memory_poll_seconds: int = 30,
    shuffle: bool = False,
    no_grade: bool = False,
    heuristic_only: bool = False,
) -> Path:
    load_env_files()
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_dir = RESULTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    user_root = run_dir / "users"
    user_root.mkdir(parents=True, exist_ok=True)

    tasks = select_tasks(load_tasks(tasks_file), task_ids, levels)
    if shuffle:
        import random

        random.shuffle(tasks)

    lanes = split_round_robin(tasks, users)
    reviewer = MiniNanoPrivacyReviewer.from_env() if privacy_review == "mini-nano" else None
    global_store = privacy_map or DEFAULT_STORE_PATH
    results: list[dict[str, Any]] = []
    results_lock = threading.Lock()

    def worker(user_index: int, assigned_tasks: list[BenchmarkTask]) -> list[dict[str, Any]]:
        user_name = f"user_{user_index + 1:02d}"
        lane_root = user_root / user_name
        lane_root.mkdir(parents=True, exist_ok=True)
        rows: list[dict[str, Any]] = []
        engines = [create_engine(name) for name in engine_names]
        for task in assigned_tasks:
            for engine in engines:
                wait_for_memory_budget(min_free_memory_mb, memory_poll_seconds)
                row = run_single_job(
                    task=task,
                    engine=engine,
                    run_id=run_id,
                    lane_root=lane_root,
                    user_name=user_name,
                    privacy_mode=privacy_mode,
                    reviewer=reviewer,
                    privacy_map=global_store,
                    cooldown_seconds=cooldown_seconds,
                    rest_seconds=rest_seconds,
                )
                rows.append(row)
                with results_lock:
                    results.append(row)
        (lane_root / "summary.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        return rows

    futures = []
    with ThreadPoolExecutor(max_workers=users) as pool:
        for index, lane in enumerate(lanes):
            futures.append(pool.submit(worker, index, lane))
        for future in as_completed(futures):
            future.result()

    (run_dir / "summary.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    if not no_grade:
        write_checks_and_grades(run_dir, tasks_file, heuristic_only)
    write_multi_user_manifest(run_dir, users, lanes, engine_names, privacy_mode, privacy_review)
    return run_dir


def run_single_job(
    *,
    task: BenchmarkTask,
    engine,
    run_id: str,
    lane_root: Path,
    user_name: str,
    privacy_mode: str,
    reviewer: MiniNanoPrivacyReviewer | None,
    privacy_map: Path,
    cooldown_seconds: int,
    rest_seconds: int,
) -> dict[str, Any]:
    workdir = prepare_workdir_in_root(lane_root, task, engine.name)
    privacy_result = None
    if privacy_mode != "clear":
        privacy_result = apply_privacy_to_workdir(
            workdir,
            mode=privacy_mode,
            store_path=privacy_map,
            reviewer=reviewer,
        )
    execution_prompt = prompt_for_execution(task, workdir)
    started = time.monotonic()
    attempts = 0
    result: EngineResult | None = None
    while True:
        attempts += 1
        try:
            result = engine.run(task.id, execution_prompt, workdir, task.expected_outputs)
        except Exception as exc:
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
        transient = transient_error(asdict(result))
        if transient and attempts < 2:
            time.sleep(max(1, min(cooldown_seconds, 10)))
            continue
        break
    copied_outputs = copy_prefixed_outputs(result.output_files, lane_root, user_name, engine.name, task.id)
    payload = asdict(result)
    payload.update(
        {
            "engine_spec": engine.name,
            "copied_outputs": [str(path) for path in copied_outputs],
            "task_prompt": task.prompt,
            "execution_prompt": execution_prompt,
            "workdir": str(workdir),
            "user": user_name,
            "privacy": privacy_result.to_dict() if privacy_result is not None else {"mode": "clear"},
            "attempts": attempts,
            "transient_error": transient,
            "elapsed_wall_seconds": round(time.monotonic() - started, 3),
        }
    )
    result_path = lane_root / f"{engine.name}_{task.id}.json"
    result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if rest_seconds:
        time.sleep(rest_seconds)
    return payload


def split_round_robin(tasks: list[BenchmarkTask], users: int) -> list[list[BenchmarkTask]]:
    users = max(1, users)
    lanes: list[list[BenchmarkTask]] = [[] for _ in range(users)]
    for index, task in enumerate(tasks):
        lanes[index % users].append(task)
    return lanes


def select_tasks(tasks: list[BenchmarkTask], task_ids: list[str] | None, levels: list[str] | None) -> list[BenchmarkTask]:
    selected = tasks
    if task_ids:
        requested = set(task_ids)
        selected = [task for task in selected if task.id in requested]
    if levels:
        normalized = {level.upper() if level.upper().startswith("L") else f"L{level}" for level in levels}
        selected = [task for task in selected if task.level.upper() in normalized]
    return selected


def copy_prefixed_outputs(output_files: list[str], run_dir: Path, user_name: str, engine_name: str, task_id: str) -> list[Path]:
    copied: list[Path] = []
    for output in output_files:
        source = Path(output)
        if not source.exists() or not source.is_file():
            continue
        target = run_dir / "outputs" / user_name / prefixed_result_name(engine_name, task_id, source.name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.append(target)
    return copied


def transient_error(result: dict[str, Any]) -> str:
    from benchmark_scheduler import transient_error as scheduler_transient_error

    return scheduler_transient_error(result)


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


def write_multi_user_manifest(
    run_dir: Path,
    users: int,
    lanes: list[list[BenchmarkTask]],
    engine_names: list[str],
    privacy_mode: str,
    privacy_review: str,
) -> None:
    manifest = {
        "users": users,
        "lanes": [[task.id for task in lane] for lane in lanes],
        "engines": engine_names,
        "privacy_mode": privacy_mode,
        "privacy_review": privacy_review,
    }
    (run_dir / "multi_user_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
