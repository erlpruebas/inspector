from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from env_utils import load_env_files
from benchmark_context import prompt_for_execution
from engines.engine_factory import create_engine
from task_loader import RESULTS_DIR, TASKS_FILE, BenchmarkTask, load_tasks, prefixed_result_name, prepare_workdir


def run_benchmark(engine_names: list[str], task_ids: list[str] | None = None, tasks_file: Path = TASKS_FILE) -> Path:
    load_env_files()
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_dir = RESULTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    selected = select_tasks(load_tasks(tasks_file), task_ids)
    engines = [create_engine(name) for name in engine_names]
    summary: list[dict[str, object]] = []

    for task in selected:
        for engine in engines:
            workdir = prepare_workdir(task, engine.name, run_id)
            execution_prompt = prompt_for_execution(task, workdir)
            result = engine.run(task.id, execution_prompt, workdir, task.expected_outputs)
            copied_outputs = copy_prefixed_outputs(result.output_files, run_dir, engine.name, task.id)
            result_payload = asdict(result)
            result_payload["copied_outputs"] = [str(path) for path in copied_outputs]
            result_payload["task_prompt"] = task.prompt
            result_payload["execution_prompt"] = execution_prompt
            result_payload["workdir"] = str(workdir)
            result_path = run_dir / f"{engine.name}_{task.id}.json"
            result_path.write_text(json.dumps(result_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            summary.append(result_payload)

    (run_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return run_dir


def select_tasks(tasks: list[BenchmarkTask], task_ids: list[str] | None) -> list[BenchmarkTask]:
    if not task_ids:
        return tasks
    requested = set(task_ids)
    selected = [task for task in tasks if task.id in requested]
    missing = requested.difference(task.id for task in selected)
    if missing:
        raise ValueError("Unknown task ids: " + ", ".join(sorted(missing)))
    return selected


def copy_prefixed_outputs(output_files: list[str], run_dir: Path, engine_name: str, task_id: str) -> list[Path]:
    copied: list[Path] = []
    for output in output_files:
        source = Path(output)
        if not source.exists() or not source.is_file():
            continue
        target = run_dir / prefixed_result_name(engine_name, task_id, source.name)
        shutil.copy2(source, target)
        copied.append(target)
    return copied
