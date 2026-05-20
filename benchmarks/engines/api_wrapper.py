from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
from env_utils import load_env_files


PROVIDER_DEFAULTS = {
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "key_env": "GROQ_API_KEY",
        "model_env": "BENCH_GROQ_MODEL",
        "model": "llama-3.1-8b-instant",
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "key_env": "OPENROUTER_API_KEY",
        "model_env": "BENCH_OPENROUTER_MODEL",
        "model": "deepseek/deepseek-v3.2",
    },
    "vikingnano": {
        "url": "https://viking-occasion-married-dimensional.trycloudflare.com/v1/chat/completions",
        "key_env": "BENCH_VIKING_NANO_API_KEY",
        "model_env": "BENCH_VIKING_NANO_MODEL",
        "model": "gemini-nano-local",
        "default_key": "local",
    },
    "lmstudio": {
        "url": "http://127.0.0.1:1234/v1/chat/completions",
        "key_env": "LMSTUDIO_API_KEY",
        "model_env": "BENCH_LMSTUDIO_MODEL",
        "model": "qwen3.5-0.8b:2",
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenAI-compatible API wrapper for benchmark engines.")
    parser.add_argument("--provider", choices=sorted(PROVIDER_DEFAULTS), required=True)
    parser.add_argument("--prompt", default="")
    parser.add_argument("--prompt-file", default="")
    parser.add_argument("--output", default="resultado.md")
    parser.add_argument("--model", default="")
    parser.add_argument("--base-url", default="")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--context-mode", choices=("full", "compact"), default="full")
    args = parser.parse_args()

    load_env_files()
    defaults = PROVIDER_DEFAULTS[args.provider]
    api_key = os.getenv(defaults["key_env"], "").strip()
    if not api_key and defaults.get("default_key"):
        api_key = str(defaults["default_key"]).strip()
    if args.provider not in {"lmstudio", "vikingnano"} and not api_key:
        raise SystemExit(f"Missing API key env var: {defaults['key_env']}")

    model = args.model.strip() or os.getenv(defaults["model_env"], defaults["model"]).strip()
    url = args.base_url.strip() or defaults["url"]
    started = time.monotonic()
    raw_prompt = read_prompt(args.prompt, args.prompt_file)
    prompt = prompt_with_workspace_files(raw_prompt, args.output, args.context_mode)
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "Eres un motor de benchmark. Devuelve solo el contenido final del archivo solicitado. No expliques como hacerlo, no digas que lo guardarias y no incluyas pasos salvo que el archivo esperado sea Markdown.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": args.temperature,
    }
    if args.provider == "groq":
        payload["max_completion_tokens"] = args.max_tokens
    else:
        payload["max_tokens"] = args.max_tokens
    data = post_json(url, payload, api_key, timeout=args.timeout)
    content = clean_model_output(extract_content(data), args.output)

    output_path = Path(args.output)
    output_path.write_text(content, encoding="utf-8")

    usage = {
        "provider": args.provider,
        "model": model,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "usage": data.get("usage", {}),
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


def post_json(url: str, payload: dict[str, Any], api_key: str, timeout: int) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": f"ai-arena-{payload.get('model', 'model')}/1.0",
        "HTTP-Referer": "http://localhost/ai-arena",
        "X-Title": "AI Arena Benchmark",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(url, data=body, method="POST", headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API error {exc.code}: {detail}") from exc


def extract_content(data: dict[str, Any]) -> str:
    choices = data.get("choices") or []
    if not choices:
        return json.dumps(data, ensure_ascii=False, indent=2)
    message = choices[0].get("message") or {}
    return str(message.get("content", "")).strip()


def prompt_with_workspace_files(prompt: str, output: str, context_mode: str = "full") -> str:
    prompt = (
        prompt
        + f"\n\nArchivo de salida esperado: {output}."
        + "\nDevuelve exclusivamente el contenido final de ese archivo. Si es CSV, JSON o ICS, no uses markdown ni bloques de codigo."
    )
    context = workspace_file_context(prompt, compact=context_mode == "compact")
    if not context:
        return prompt
    return prompt + "\n\nArchivos disponibles en el directorio de trabajo:\n\n" + context


def clean_model_output(content: str, output: str) -> str:
    content = fix_mojibake(content)
    suffix = Path(output).suffix.lower()
    if suffix in {".csv", ".json", ".ics", ".txt", ".py"}:
        fenced = re.search(r"```(?:[a-zA-Z0-9_-]+)?\s*(.*?)```", content, flags=re.DOTALL)
        if fenced:
            return fenced.group(1).strip() + "\n"
    return content.strip() + "\n"


def fix_mojibake(value: str) -> str:
    if "Ã" not in value and "Â" not in value and "ï¿½" not in value:
        return value
    for encoding in ("latin1", "cp1252"):
        try:
            repaired = value.encode(encoding, errors="ignore").decode("utf-8", errors="ignore")
        except UnicodeError:
            continue
        if repaired and repaired.count("Ã") < value.count("Ã"):
            return repaired
    return value


def workspace_file_context(prompt: str = "", compact: bool = False) -> str:
    parts: list[str] = []
    skip_names = {"resultado.md", "usage.json", "_benchmark_prompt.md"}
    terms = prompt_terms(prompt)
    for path in sorted(Path.cwd().rglob("*")):
        if not path.is_file() or path.name in skip_names or "privacy" in path.parts:
            continue
        if path.stat().st_size > 80_000:
            parts.append(f"### {path.relative_to(Path.cwd())}\n[archivo omitido por tamano: {path.stat().st_size} bytes]")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if compact:
            text = compact_text(text, terms, path.suffix.lower())
        parts.append(f"### {path.relative_to(Path.cwd())}\n```text\n{text}\n```")
    return "\n\n".join(parts)


def prompt_terms(prompt: str) -> set[str]:
    stop = {
        "archivo",
        "archivos",
        "benchmark",
        "crear",
        "datos",
        "debe",
        "desde",
        "directorio",
        "empresa",
        "esperado",
        "fecha",
        "hora",
        "locales",
        "objetivo",
        "persona",
        "preparados",
        "respuesta",
        "revisa",
        "salida",
        "tarea",
        "trabajo",
        "usar",
        "usa",
    }
    terms = {term.casefold() for term in re.findall(r"[\w.-]{4,}", prompt, flags=re.UNICODE)}
    useful = {term for term in terms if term not in stop and not term.endswith((".csv", ".md", ".jsonl"))}
    return useful or terms


def compact_text(text: str, terms: set[str], suffix: str, window: int = 8, max_lines: int = 80) -> str:
    lines = text.splitlines()
    if not terms or len(lines) <= 20:
        return text
    selected: set[int] = set()
    if suffix == ".csv" and lines:
        selected.add(0)
    for index, line in enumerate(lines):
        lowered = line.casefold()
        if any(term in lowered for term in terms):
            for nearby in range(max(0, index - window), min(len(lines), index + window + 1)):
                selected.add(nearby)
    if not selected:
        return "\n".join(lines[:max_lines])
    ordered = sorted(selected)
    if len(ordered) > max_lines:
        ordered = ordered[:max_lines]
    return "\n".join(lines[index] for index in ordered)


if __name__ == "__main__":
    raise SystemExit(main())
