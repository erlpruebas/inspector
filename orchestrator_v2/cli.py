from __future__ import annotations

import argparse
from pathlib import Path

from benchmarks.env_utils import load_env_files

from .models import TaskRequest
from .orchestrator import GestorOrquestador
from .router import choose_tool
from .tool_registry import TOOLS


def main() -> int:
    parser = argparse.ArgumentParser(description="Orchestrator v2 local CLI.")
    parser.add_argument("text", nargs="*", help="Task text.")
    parser.add_argument("--file", action="append", default=[], help="Input file. Can be repeated.")
    parser.add_argument("--tool", default="", help="Force herramienta id.")
    parser.add_argument("--privacy", choices=("ask", "clear", "mixed", "redacted"), default="ask")
    parser.add_argument("--list-tools", action="store_true")
    parser.add_argument("--route-only", action="store_true")
    parser.add_argument("--desktop-send", action="store_true", help="Permite que desktop_codex_operator tome raton/teclado y envie el prompt.")
    parser.add_argument("--desktop-wait-seconds", type=int, default=1800)
    args = parser.parse_args()

    load_env_files()
    if args.list_tools:
        for tool in TOOLS.values():
            print(f"{tool.id}\t{tool.kind}\t{tool.engine}\t{tool.role}\t{tool.reliability}")
        return 0

    text = " ".join(args.text).strip()
    if not text:
        raise SystemExit("Missing task text.")
    request = TaskRequest(
        text=text,
        files=tuple(Path(item) for item in args.file),
        privacy_mode=args.privacy,
        metadata={"desktop_send": args.desktop_send, "desktop_wait_seconds": args.desktop_wait_seconds},
    )
    if args.route_only:
        decision = choose_tool(request)
        print(decision)
        return 0
    result = GestorOrquestador().handle(request, tool_id=args.tool)
    print(f"ok={result.ok} tool={result.tool_id} engine={result.engine} privacy={result.privacy_mode} elapsed={result.elapsed_seconds}s")
    if result.error:
        print(f"error={result.error}")
    if result.output:
        print(result.output)
    print(f"workdir={result.workdir}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
