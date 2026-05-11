from __future__ import annotations

import argparse
from pathlib import Path

from multi_runner import run_benchmark


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the AI Arena benchmark.")
    parser.add_argument("--engine", action="append", default=[], help="Engine to run: codex, groq, openrouter or command.")
    parser.add_argument("--task", action="append", default=[], help="Optional task id. Can be repeated.")
    parser.add_argument("--tasks-file", default="", help="Optional JSON task file. Defaults to benchmarks/tasks/tasks.json.")
    args = parser.parse_args()

    engines = args.engine or ["codex"]
    tasks_file = Path(args.tasks_file) if args.tasks_file else None
    run_dir = run_benchmark(engines, args.task or None, tasks_file=tasks_file) if tasks_file else run_benchmark(engines, args.task or None)
    print(f"Benchmark run completed: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
