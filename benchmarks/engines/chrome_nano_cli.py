from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

try:
    from .chrome_nano_bridge import ChromeNanoBridge, ChromeNanoError
except ImportError:  # pragma: no cover - script execution fallback
    from chrome_nano_bridge import ChromeNanoBridge, ChromeNanoError


def main() -> int:
    parser = argparse.ArgumentParser(description="CLI bridge for Chrome Gemini Nano.")
    parser.add_argument("--prompt", default="")
    parser.add_argument("--prompt-file", default="")
    parser.add_argument("--output", default="resultado.md")
    parser.add_argument("--model", default="gemini-nano")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--health", action="store_true")
    args = parser.parse_args()

    started = time.monotonic()
    bridge = ChromeNanoBridge(timeout_seconds=args.timeout)
    try:
        if args.health:
            print(json.dumps(bridge.health(), ensure_ascii=False, indent=2))
            return 0
        prompt = read_prompt(args.prompt, args.prompt_file)
        response = bridge.prompt(
            prompt=prompt,
            system_prompt="Devuelve solo el contenido final solicitado. No expliques pasos salvo que el resultado sea Markdown.",
            temperature=args.temperature,
        )
        Path(args.output).write_text(response.content.strip() + "\n", encoding="utf-8")
        usage = {
            "provider": "chrome-nano",
            "model": args.model,
            "availability": response.availability,
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }
        Path("usage.json").write_text(json.dumps(usage, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(usage, ensure_ascii=False))
        return 0
    except ChromeNanoError as exc:
        print(json.dumps({"provider": "chrome-nano", "model": args.model, "error": str(exc)}, ensure_ascii=False))
        return 1
    finally:
        bridge.close()


def read_prompt(prompt: str, prompt_file: str) -> str:
    if prompt_file:
        return Path(prompt_file).read_text(encoding="utf-8")
    if prompt:
        return prompt
    raise SystemExit("--prompt or --prompt-file is required")


if __name__ == "__main__":
    raise SystemExit(main())
