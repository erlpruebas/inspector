from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from env_utils import google_api_key, key_status, load_env_files


def main() -> int:
    parser = argparse.ArgumentParser(description="Check benchmark provider readiness without printing secrets.")
    parser.add_argument("--live", action="store_true", help="Run tiny live API generation tests.")
    parser.add_argument("--output", default="benchmarks/results/provider_health.json")
    args = parser.parse_args()

    load_env_files()
    report = {
        "commands": command_status(["codex", "gemini", "opencode", "groq", "openrouter"]),
        "keys": key_status(),
        "api": {},
    }
    if args.live:
        report["api"] = live_api_tests()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(redact_report(report), ensure_ascii=False, indent=2))
    print(f"saved={output}")
    return 0


def command_status(names: list[str]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for name in names:
        path = find_command(name)
        item = {"status": "found" if path else "missing", "path": path or ""}
        if path:
            try:
                process = subprocess.run(
                    [path, "--version"],
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=10,
                )
                item["version"] = (process.stdout or process.stderr).strip().splitlines()[0][:160]
            except Exception as exc:
                item["version_error"] = f"{type(exc).__name__}: {exc}"
        result[name] = item
    return result


def live_api_tests() -> dict[str, dict[str, Any]]:
    tests: dict[str, dict[str, Any]] = {}
    if os.getenv("GROQ_API_KEY", "").strip():
        tests["groq"] = openai_compatible_chat(
            "https://api.groq.com/openai/v1/chat/completions",
            os.environ["GROQ_API_KEY"],
            os.getenv("BENCH_GROQ_MODEL", "llama-3.1-8b-instant"),
            groq=True,
        )
    else:
        tests["groq"] = {"status": "skipped", "reason": "missing key"}

    if os.getenv("OPENROUTER_API_KEY", "").strip():
        tests["openrouter"] = openai_compatible_chat(
            "https://openrouter.ai/api/v1/chat/completions",
            os.environ["OPENROUTER_API_KEY"],
            os.getenv("BENCH_OPENROUTER_MODEL", "deepseek/deepseek-v3.2"),
            extra_headers={"HTTP-Referer": "http://localhost/ai-arena", "X-Title": "AI Arena Benchmark"},
        )
    else:
        tests["openrouter"] = {"status": "skipped", "reason": "missing key"}

    gkey = google_api_key()
    if gkey:
        tests["gemini_api"] = gemini_chat(gkey, os.getenv("BENCH_GEMINI_API_MODEL", "gemini-2.5-flash-lite"))
    else:
        tests["gemini_api"] = {"status": "skipped", "reason": "missing key"}
    tests["lmstudio"] = openai_compatible_chat(
        os.getenv("BENCH_LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1/chat/completions"),
        os.getenv("LMSTUDIO_API_KEY", ""),
        os.getenv("BENCH_LMSTUDIO_MODEL", "qwen3.5-0.8b:2"),
    )
    return tests


def find_command(name: str) -> str | None:
    if os.name == "nt":
        return shutil.which(f"{name}.cmd") or shutil.which(name)
    return shutil.which(name)


def openai_compatible_chat(
    url: str,
    key: str,
    model: str,
    extra_headers: dict[str, str] | None = None,
    groq: bool = False,
) -> dict[str, Any]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "groq-smoke-test/1.0" if groq else "ai-arena-smoke-test/1.0",
    }
    if key:
        headers["Authorization"] = f"Bearer {key}"
    headers.update(extra_headers or {})
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Responde solo OK"}],
        "temperature": 0,
    }
    if groq:
        payload["max_completion_tokens"] = 8
    else:
        payload["max_tokens"] = 8
    return post_json(url, payload, headers, model)


def gemini_chat(key: str, model: str) -> dict[str, Any]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": "Responde solo OK"}]}],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 8},
    }
    return post_json(url, payload, {"Content-Type": "application/json"}, model)


def post_json(url: str, payload: dict[str, Any], headers: dict[str, str], model: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers=headers,
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8", errors="replace"))
        return {"status": "ok", "model": model, "usage": data.get("usage") or data.get("usageMetadata") or {}}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        return {"status": "fail", "model": model, "error": f"HTTP {exc.code}", "detail": detail}
    except Exception as exc:
        return {"status": "fail", "model": model, "error": f"{type(exc).__name__}: {exc}"}


def redact_report(report: dict[str, Any]) -> dict[str, Any]:
    return report


if __name__ == "__main__":
    raise SystemExit(main())
