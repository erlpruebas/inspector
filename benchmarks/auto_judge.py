from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
from typing import Any

from env_utils import google_api_key, load_env_files
from judge import judge_pair
from task_loader import RESULTS_DIR, load_tasks


def main() -> int:
    parser = argparse.ArgumentParser(description="Run pairwise Gemini judgements for a benchmark run.")
    parser.add_argument("--run-dir", default="")
    parser.add_argument("--model", default="gemini-2.5-flash-lite")
    args = parser.parse_args()

    load_env_files()
    api_key = google_api_key()
    if not api_key:
        raise SystemExit("Missing GOOGLE_API_KEY, GEMINI_API_KEY or ORCH_GOOGLE_API_KEY")

    run_dir = Path(args.run_dir) if args.run_dir else latest_run_dir()
    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        raise SystemExit(f"Missing summary file: {summary_path}")

    tasks = {task.id: task for task in load_tasks()}
    rows = json.loads(summary_path.read_text(encoding="utf-8"))
    by_task: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if row.get("returncode") != 0 or row.get("timed_out"):
            continue
        outputs = row.get("copied_outputs") or []
        if not outputs:
            continue
        by_task.setdefault(str(row.get("task_id")), []).append(row)

    judgements: list[dict[str, Any]] = []
    for task_id, task_rows in by_task.items():
        task = tasks.get(task_id)
        if task is None or len(task_rows) < 2:
            continue
        for left, right in itertools.combinations(task_rows, 2):
            left_file = first_text_output(left)
            right_file = first_text_output(right)
            if left_file is None or right_file is None:
                continue
            judgement = judge_pair(
                model=args.model,
                api_key=api_key,
                task_prompt=task.prompt,
                answer_a=left_file.read_text(encoding="utf-8", errors="replace"),
                answer_b=right_file.read_text(encoding="utf-8", errors="replace"),
            )
            judgements.append(
                {
                    "task_id": task_id,
                    "engine_a": left.get("engine"),
                    "engine_b": right.get("engine"),
                    "file_a": str(left_file),
                    "file_b": str(right_file),
                    "judgement": judgement,
                }
            )

    output = run_dir / "judgements.json"
    output.write_text(json.dumps(judgements, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output)
    return 0


def latest_run_dir() -> Path:
    candidates = [path for path in RESULTS_DIR.iterdir() if path.is_dir()]
    if not candidates:
        raise SystemExit("No benchmark runs found")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def first_text_output(row: dict[str, Any]) -> Path | None:
    for value in row.get("copied_outputs") or []:
        path = Path(value)
        if path.suffix.lower() in {".md", ".txt", ".csv", ".json", ".ics", ".py", ".log", ".html"} and path.exists():
            return path
    return None


if __name__ == "__main__":
    raise SystemExit(main())
