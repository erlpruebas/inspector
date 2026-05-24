from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from env_utils import load_env_files
from benchmark_context import prompt_for_execution
from engines.engine_factory import create_engine
from privacy_guard import DEFAULT_STORE_PATH, MiniNanoPrivacyReviewer, apply_privacy_to_workdir
from task_loader import RESULTS_DIR, TASKS_FILE, BenchmarkTask, load_tasks, prefixed_result_name, prepare_workdir
from memory_guard import wait_for_memory_budget
from token_accounting import record_usage, summarize_usage


def run_benchmark(
    engine_names: list[str],
    task_ids: list[str] | None = None,
    tasks_file: Path = TASKS_FILE,
    *,
    min_free_memory_mb: int = 512,
    memory_poll_seconds: int = 30,
    privacy_mode: str = "clear",
    privacy_review: str = "none",
    privacy_map: Path | None = None,
) -> Path:
    load_env_files()
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_dir = RESULTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    selected = select_tasks(load_tasks(tasks_file), task_ids)
    engines = [create_engine(name) for name in engine_names]
    summary: list[dict[str, object]] = []
    reviewer = MiniNanoPrivacyReviewer.from_env() if privacy_review == "mini-nano" else None

    for task in selected:
        for engine in engines:
            wait_for_memory_budget(min_free_memory_mb, memory_poll_seconds)
            workdir = prepare_workdir(task, engine.name, run_id)
            privacy_result = None
            if privacy_mode != "clear":
                privacy_result = apply_privacy_to_workdir(
                    workdir,
                    mode=privacy_mode,
                    store_path=privacy_map or DEFAULT_STORE_PATH,
                    reviewer=reviewer,
                )
            execution_prompt = prompt_for_execution(task, workdir)
            result = engine.run(task.id, execution_prompt, workdir, task.expected_outputs)
            copied_outputs = copy_prefixed_outputs(result.output_files, run_dir, engine.name, task.id)
            result_payload = asdict(result)
            result_payload["copied_outputs"] = [str(path) for path in copied_outputs]
            result_payload["task_prompt"] = task.prompt
            result_payload["execution_prompt"] = execution_prompt
            result_payload["workdir"] = str(workdir)
            result_payload["privacy"] = privacy_result.to_dict() if privacy_result is not None else {"mode": "clear"}
            result_path = run_dir / f"{engine.name}_{task.id}.json"
            result_path.write_text(json.dumps(result_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            record_usage(
                run_dir / "token_usage.jsonl",
                source="benchmark",
                component=engine.name,
                provider=str(engine.name).split(":", 1)[0],
                model=str(getattr(engine, "model", "")),
                operation="task_run",
                usage=result.usage,
                prompt_text=execution_prompt,
                completion_text=result.stdout,
                task_id=task.id,
                run_id=run_id,
                metadata={"engine_spec": engine.name, "privacy_mode": privacy_mode},
            )
            summary.append(result_payload)

    (run_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "token_usage_summary.json").write_text(
        json.dumps(summarize_usage(run_dir / "token_usage.jsonl"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
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
