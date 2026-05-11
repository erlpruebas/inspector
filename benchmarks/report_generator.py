from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from task_loader import RESULTS_DIR


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Markdown report from benchmark results.")
    parser.add_argument("--run-dir", default="")
    args = parser.parse_args()

    run_dir = Path(args.run_dir) if args.run_dir else latest_run_dir()
    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        raise SystemExit(f"Missing summary file: {summary_path}")

    rows = json.loads(summary_path.read_text(encoding="utf-8"))
    report = build_report(run_dir, rows)
    target = run_dir / "report.md"
    target.write_text(report, encoding="utf-8")
    print(target)
    return 0


def latest_run_dir() -> Path:
    candidates = [path for path in RESULTS_DIR.iterdir() if path.is_dir()]
    if not candidates:
        raise SystemExit("No benchmark runs found")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def build_report(run_dir: Path, rows: list[dict[str, Any]]) -> str:
    lines = [
        "# AI Arena Benchmark Report",
        "",
        f"Run: `{run_dir.name}`",
        "",
        "| Task | Engine | Model | OK | Seconds | Outputs | Tokens/Cost |",
        "| --- | --- | --- | --- | ---: | --- | --- |",
    ]
    for row in rows:
        usage = row.get("usage") or {}
        copied = row.get("copied_outputs") or []
        outputs = "<br>".join(Path(path).name for path in copied) if copied else "-"
        lines.append(
            "| {task} | {engine} | {model} | {ok} | {seconds:.2f} | {outputs} | {usage} |".format(
                task=row.get("task_id", ""),
                engine=row.get("engine", ""),
                model=model_name(row),
                ok="yes" if row.get("returncode") == 0 and not row.get("timed_out") else "no",
                seconds=float(row.get("elapsed_seconds") or 0),
                outputs=outputs,
                usage=compact_usage(usage),
            )
        )
    lines.extend(["", "## Notes", "", "- Pairwise judge outputs can be added beside this report as JSON files."])
    return "\n".join(lines) + "\n"


def compact_usage(usage: dict[str, Any]) -> str:
    if not usage:
        return "-"
    nested = usage.get("usage") if isinstance(usage.get("usage"), dict) else usage
    parts = []
    for key in ("prompt_tokens", "completion_tokens", "total_tokens", "cost"):
        if key in nested:
            parts.append(f"{key}={nested[key]}")
    return ", ".join(parts) if parts else "-"


def model_name(row: dict[str, Any]) -> str:
    if row.get("model"):
        return str(row["model"])
    usage = row.get("usage") or {}
    if isinstance(usage, dict) and usage.get("model"):
        return str(usage["model"])
    if row.get("engine_spec"):
        return str(row["engine_spec"])
    return "-"


if __name__ == "__main__":
    raise SystemExit(main())
