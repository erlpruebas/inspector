from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Local smoke-test engine for AI Arena.")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output", default="resultado.md")
    args = parser.parse_args()

    Path(args.output).write_text(
        "# Resultado local\n\n"
        "Este archivo fue generado por el motor local de prueba.\n\n"
        f"Prompt recibido:\n\n{args.prompt}\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
