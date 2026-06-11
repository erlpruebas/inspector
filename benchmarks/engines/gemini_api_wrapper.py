from __future__ import annotations

import argparse
import base64
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
    parser.add_argument(
        "--grounding",
        choices=("none", "google_search", "google_search_retrieval"),
        default=os.getenv("BENCH_GEMINI_API_GROUNDING", "none"),
    )
    parser.add_argument(
        "--grounding-threshold",
        type=float,
        default=float(os.getenv("BENCH_GEMINI_API_GROUNDING_THRESHOLD", "0.7")),
    )
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
    generation_config: dict[str, Any] = {
        "temperature": args.temperature,
        "maxOutputTokens": args.max_output_tokens,
    }
    if Path(args.output).suffix.casefold() == ".json":
        generation_config["responseMimeType"] = "application/json"
    payload = {
        "contents": [{"role": "user", "parts": content_parts(prompt)}],
        "generationConfig": generation_config,
    }
    tools = build_tools(args.grounding, args.grounding_threshold)
    if tools:
        payload["tools"] = tools
    data = call_gemini(args.model, api_key, payload, args.timeout)
    content = clean_model_output(extract_text(data), args.output)
    Path(args.output).write_text(content, encoding="utf-8")
    usage = {
        "provider": "gemini_api",
        "model": args.model,
        "grounding": args.grounding,
        "max_output_tokens": args.max_output_tokens,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "usage": data.get("usageMetadata", {}),
    }
    grounding_metadata = extract_grounding_metadata(data)
    if grounding_metadata:
        Path("grounding.json").write_text(json.dumps(grounding_metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        usage["grounding_metadata"] = grounding_metadata
    response_metadata = extract_response_metadata(data)
    if response_metadata:
        Path("response_metadata.json").write_text(
            json.dumps(response_metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        usage["response_metadata"] = response_metadata
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


def build_tools(grounding: str, grounding_threshold: float) -> list[dict[str, Any]]:
    if grounding == "google_search":
        return [{"google_search": {}}]
    if grounding == "google_search_retrieval":
        return [
            {
                "google_search_retrieval": {
                    "dynamic_retrieval_config": {
                        "mode": "MODE_DYNAMIC",
                        "dynamic_threshold": grounding_threshold,
                    }
                }
            }
        ]
    return []


def extract_grounding_metadata(data: dict[str, Any]) -> dict[str, Any]:
    candidates = data.get("candidates") or []
    if not candidates:
        return {}
    grounding = candidates[0].get("groundingMetadata") or candidates[0].get("grounding_metadata")
    return grounding if isinstance(grounding, dict) else {}


def extract_response_metadata(data: dict[str, Any]) -> dict[str, Any]:
    candidates = data.get("candidates") or []
    if not candidates or not isinstance(candidates[0], dict):
        return {}
    candidate = candidates[0]
    metadata: dict[str, Any] = {}
    for source_key, target_key in (
        ("finishReason", "finish_reason"),
        ("finishMessage", "finish_message"),
        ("safetyRatings", "safety_ratings"),
        ("citationMetadata", "citation_metadata"),
    ):
        if source_key in candidate:
            metadata[target_key] = candidate[source_key]
    return metadata


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


def content_parts(prompt: str) -> list[dict[str, Any]]:
    parts: list[dict[str, Any]] = [{"text": prompt}]
    for path in workspace_binary_files():
        mime_type = binary_mime_type(path)
        if not mime_type:
            continue
        parts.append(
            {
                "inlineData": {
                    "mimeType": mime_type,
                    "data": base64.b64encode(path.read_bytes()).decode("ascii"),
                }
            }
        )
    return parts


def clean_model_output(content: str, output: str) -> str:
    suffix = Path(output).suffix.lower()
    if suffix in {".csv", ".json", ".ics", ".txt", ".py"}:
        fenced = re.search(r"```(?:[a-zA-Z0-9_-]+)?\s*(.*?)```", content, flags=re.DOTALL)
        if fenced:
            return fenced.group(1).strip() + "\n"
    return content.strip() + "\n"


def workspace_file_context() -> str:
    parts: list[str] = []
    skip_names = {"resultado.md", "usage.json", "response_metadata.json"}
    cwd = Path.cwd()
    for path in sorted(cwd.rglob("*")):
        if not path.is_file() or path.name in skip_names or "privacy" in path.parts:
            continue
        if binary_mime_type(path):
            parts.append(
                f"### {path.relative_to(cwd)}\n"
                f"[archivo binario enviado como {binary_mime_type(path)}]"
            )
            continue
        if path.stat().st_size > 80_000:
            parts.append(f"### {path.relative_to(cwd)}\n[archivo omitido por tamano: {path.stat().st_size} bytes]")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        parts.append(f"### {path.relative_to(cwd)}\n```text\n{text}\n```")
    return "\n\n".join(parts)


def workspace_binary_files() -> list[Path]:
    cwd = Path.cwd()
    return [
        path
        for path in sorted(cwd.rglob("*"))
        if path.is_file()
        and "privacy" not in path.parts
        and binary_mime_type(path)
    ]


def binary_mime_type(path: Path) -> str:
    return {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".ogg": "audio/ogg",
    }.get(path.suffix.casefold(), "")


if __name__ == "__main__":
    raise SystemExit(main())
