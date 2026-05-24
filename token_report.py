from __future__ import annotations

import argparse
import json
from pathlib import Path

from benchmarks.token_accounting import summarize_usage


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize token usage from a JSONL log.")
    parser.add_argument("path", nargs="?", default="orchestrator_v2/runtime/token_usage.jsonl")
    args = parser.parse_args()
    summary = summarize_usage(Path(args.path))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
