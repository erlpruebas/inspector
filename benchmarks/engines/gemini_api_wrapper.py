from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
from env_utils import google_api_key, load_env_files


def main() -> int:
    parser = argparse.ArgumentParser(description="Gemini API wrapper for benchmark engines.")
    parser.add_argument("--prompt", default="")
    parser.add_argument("--prompt-file", default="")
    parser.add_argument("--output", default="resultado.md")
    parser.add_argument("--model", default=os.getenv("BENCH_GEMINI_API_MODEL", "gemini-2.5-flash-lite"))
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max-output-tokens", type=int, default=2048)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    load_env_files()
    api_key = google_api_key()
    if not api_key:
        raise SystemExit("Missing GOOGLE_API_KEY, GEMINI_API_KEY or ORCH_GOOGLE_API_KEY")

    started = time.monotonic()
    prompt = prompt_with_workspace_files(read_prompt(args.prompt, args.prompt_file), args.output)
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": args.temperature,
            "maxOutputTokens": args.max_output_tokens,
        },
    }
    data = call_gemini(args.model, api_key, payload, args.timeout)
    content = clean_model_output(extract_text(data), args.output)
    Path(args.output).write_text(content, encoding="utf-8")
    usage = {
        "provider": "gemini_api",
        "model": args.model,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "usage": data.get("usageMetadata", {}),
    }
    Path("usage.json").write_text(json.dumps(usage, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(usage, ensure_ascii=False))
    return 0


def read_prompt(prompt: str, prompt_file: str) -> str:
    if prompt_file:
        return Path(prompt_file).read_text(encoding="utf-8")
    if prompt:
        return prompt
    raise SystemExit("--prompt or --prompt-file is required")


def call_gemini(model: str, api_key: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        + urllib.parse.quote(model, safe="")
        + ":generateContent?key="
        + urllib.parse.quote(api_key, safe="")
    )
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def extract_text(data: dict[str, Any]) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        return json.dumps(data, ensure_ascii=False, indent=2)
    parts = (((candidates[0] or {}).get("content") or {}).get("parts") or [])
    return "".join(str(part.get("text", "")) for part in parts if isinstance(part, dict)).strip()


def prompt_with_workspace_files(prompt: str, output: str) -> str:
    prompt = (
        prompt
        + f"\n\nArchivo de salida esperado: {output}."
        + "\nDevuelve exclusivamente el contenido final de ese archivo. No escribas codigo para generarlo. Si es CSV, JSON o ICS, no uses markdown ni bloques de codigo."
    )
    context = workspace_file_context()
    if not context:
        return prompt
    return prompt + "\n\nArchivos disponibles en el directorio de trabajo:\n\n" + context


def clean_model_output(content: str, output: str) -> str:
    suffix = Path(output).suffix.lower()
    if suffix in {".csv", ".json", ".ics", ".txt", ".py"}:
        fenced = re.search(r"```(?:[a-zA-Z0-9_-]+)?\s*(.*?)```", content, flags=re.DOTALL)
        if fenced:
            return fenced.group(1).strip() + "\n"
    return content.strip() + "\n"


def workspace_file_context() -> str:
    parts: list[str] = []
    skip_names = {"resultado.md", "usage.json"}
    cwd = Path.cwd()
    for path in sorted(cwd.rglob("*")):
        if not path.is_file() or path.name in skip_names:
            continue
        if path.stat().st_size > 80_000:
            parts.append(f"### {path.relative_to(cwd)}\n[archivo omitido por tamano: {path.stat().st_size} bytes]")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        parts.append(f"### {path.relative_to(cwd)}\n```text\n{text}\n```")
    return "\n\n".join(parts)


if __name__ == "__main__":
    raise SystemExit(main())
