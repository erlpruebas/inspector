from __future__ import annotations

import argparse
from pathlib import Path

from multi_runner import run_benchmark
from multi_user_orchestrator import run_multi_user_benchmark


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the AI Arena benchmark.")
    parser.add_argument("--engine", action="append", default=[], help="Engine to run: codex, groq, openrouter or command.")
    parser.add_argument("--task", action="append", default=[], help="Optional task id. Can be repeated.")
    parser.add_argument("--tasks-file", default="", help="Optional JSON task file. Defaults to benchmarks/tasks/tasks.json.")
    parser.add_argument("--privacy-mode", choices=("clear", "mixed", "redacted"), default="clear")
    parser.add_argument("--privacy-review", choices=("none", "mini-nano"), default="none")
    parser.add_argument("--privacy-map", default="")
    parser.add_argument("--users", type=int, default=1, help="Number of isolated user lanes to run in parallel.")
    args = parser.parse_args()

    engines = args.engine or ["codex"]
    tasks_file = Path(args.tasks_file) if args.tasks_file else None
    run_kwargs = {
        "privacy_mode": args.privacy_mode,
        "privacy_review": args.privacy_review,
        "privacy_map": Path(args.privacy_map) if args.privacy_map else None,
    }
    if int(args.users) > 1:
        run_dir = run_multi_user_benchmark(
            engines,
            tasks_file=tasks_file or Path("benchmarks/tasks/tasks.json"),
            task_ids=args.task or None,
            users=int(args.users),
            **run_kwargs,
        )
    else:
        run_dir = (
            run_benchmark(engines, args.task or None, tasks_file=tasks_file, **run_kwargs)
            if tasks_file
            else run_benchmark(engines, args.task or None, **run_kwargs)
        )
    print(f"Benchmark run completed: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
