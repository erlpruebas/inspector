from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:  # pragma: no cover - import convenience for direct script execution
    from .anonymizer import apply_privacy_to_path, apply_privacy_to_workdir, hydrate_text
    from .entity_store import PrivacyEntityStore
    from .mini_nano_review import MiniNanoPrivacyReviewer
    from .verifier import verify_redacted_text
except ImportError:  # pragma: no cover
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from benchmarks.privacy_guard.anonymizer import apply_privacy_to_path, apply_privacy_to_workdir, hydrate_text
    from benchmarks.privacy_guard.entity_store import PrivacyEntityStore
    from benchmarks.privacy_guard.mini_nano_review import MiniNanoPrivacyReviewer
    from benchmarks.privacy_guard.verifier import verify_redacted_text


def main() -> int:
    parser = argparse.ArgumentParser(description="Local privacy guard for benchmark documents.")
    sub = parser.add_subparsers(dest="command", required=True)

    anonymize = sub.add_parser("anonymize", help="Create original, mixed and redacted copies.")
    anonymize.add_argument("--input", required=True)
    anonymize.add_argument("--out-dir", required=True)
    anonymize.add_argument("--mode", choices=("clear", "mixed", "redacted"), default="redacted")
    anonymize.add_argument("--store", default="")
    anonymize.add_argument("--review", choices=("none", "mini-nano"), default="none")

    hydrate = sub.add_parser("hydrate", help="Restore canonical values from tokens.")
    hydrate.add_argument("--input", required=True)
    hydrate.add_argument("--output", required=True)
    hydrate.add_argument("--store", default="")

    scan = sub.add_parser("scan", help="Scan text for residual sensitive data.")
    scan.add_argument("--input", required=True)
    scan.add_argument("--store", default="")

    args = parser.parse_args()
    store_path = Path(args.store) if getattr(args, "store", "") else None

    if args.command == "anonymize":
        reviewer = MiniNanoPrivacyReviewer.from_env() if args.review == "mini-nano" else None
        source = Path(args.input)
        out_dir = Path(args.out_dir)
        if source.is_dir():
            result = apply_privacy_to_workdir(source, mode=args.mode, store_path=store_path, reviewer=reviewer)
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
            return 0
        result = apply_privacy_to_path(source, out_dir=out_dir, mode=args.mode, store_path=store_path, reviewer=reviewer)
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "hydrate":
        store = PrivacyEntityStore(store_path or default_store_path())
        source = Path(args.input).read_text(encoding="utf-8", errors="replace")
        hydrated = hydrate_text(source, store)
        Path(args.output).write_text(hydrated, encoding="utf-8")
        print(json.dumps({"ok": True, "output": str(args.output)}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "scan":
        store = PrivacyEntityStore(store_path or default_store_path())
        text = Path(args.input).read_text(encoding="utf-8", errors="replace")
        result = verify_redacted_text(text, store)
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return 0

    raise SystemExit(f"Unknown command: {args.command}")


def default_store_path() -> Path:
    return Path(__file__).resolve().parents[1] / "privacy_store" / "entity_map.jsonl"


if __name__ == "__main__":
    raise SystemExit(main())
