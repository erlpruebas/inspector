from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description="Check benchmark outputs against metadata expected_keys.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--tasks-file", default="benchmarks/tasks/assistant_tasks.json")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    tasks = {item["id"]: item for item in json.loads(Path(args.tasks_file).read_text(encoding="utf-8"))}
    checks = []
    for row in summary:
        task = tasks.get(str(row.get("task_id")), {})
        keys = [str(item) for item in task.get("expected_keys", [])]
        outputs = [Path(path) for path in row.get("copied_outputs", [])]
        text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in outputs if path.exists())
        lowered = normalize(text)
        missing = [key for key in keys if not any(normalize(variant) in lowered for variant in key_variants(key))]
        checks.append(
            {
                "task_id": row.get("task_id"),
                "engine": row.get("engine"),
                "expected_keys": keys,
                "missing_keys": missing,
                "passed": not missing,
            }
        )

    output = Path(args.output) if args.output else run_dir / "expected_key_checks.json"
    output.write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output)
    return 0


def normalize(value: Any) -> str:
    return str(value).casefold().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")


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


if __name__ == "__main__":
    raise SystemExit(main())
