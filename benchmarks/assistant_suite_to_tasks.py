from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SUITE_ROOT = ROOT / "tasks" / "assistant_suite"
OUTPUT = ROOT / "tasks" / "assistant_tasks.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert assistant_suite test folders to runner-compatible tasks JSON.")
    parser.add_argument("--suite-root", default=str(SUITE_ROOT))
    parser.add_argument("--output", default=str(OUTPUT))
    args = parser.parse_args()

    suite_root = Path(args.suite_root)
    tasks = []
    for folder in sorted(path for path in suite_root.iterdir() if path.is_dir() and path.name.startswith("test-")):
        task_md = folder / "task.md"
        metadata_path = folder / "metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        prompt = task_md.read_text(encoding="utf-8").strip()
        skills = [str(item) for item in metadata.get("skills", [])]
        tasks.append(
            {
                "id": metadata["id"],
                "level": f"L{metadata.get('difficulty', '')}",
                "category": "assistant_digital",
                "prompt": prompt,
                "required_files": metadata.get("required_files", []),
                "expected_outputs": ["resultado.md"],
                "requires_network": "web_search" in skills,
                "skills": skills,
                "expected_keys": metadata.get("expected_keys", []),
                "rubric": {
                    "correctness": 4,
                    "expected_keys": 3,
                    "format": 2,
                    "traceability": 1,
                },
            }
        )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"written={output}")
    print(f"count={len(tasks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
