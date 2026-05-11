from __future__ import annotations

import argparse
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from env_utils import google_api_key, load_env_files
from task_loader import load_tasks


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two benchmark outputs with Gemini.")
    parser.add_argument("--task", required=True)
    parser.add_argument("--a", required=True)
    parser.add_argument("--b", required=True)
    parser.add_argument("--model", default=os.getenv("BENCH_JUDGE_MODEL", "gemini-2.5-flash-lite"))
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    load_env_files()
    api_key = google_api_key()
    if not api_key:
        raise SystemExit("Missing GOOGLE_API_KEY, GEMINI_API_KEY or ORCH_GOOGLE_API_KEY")

    task = next((item for item in load_tasks() if item.id == args.task), None)
    if task is None:
        raise SystemExit(f"Unknown task: {args.task}")

    result = judge_pair(
        model=args.model,
        api_key=api_key,
        task_prompt=task.prompt,
        answer_a=Path(args.a).read_text(encoding="utf-8", errors="replace"),
        answer_b=Path(args.b).read_text(encoding="utf-8", errors="replace"),
    )
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    print(text)
    return 0


def judge_pair(model: str, api_key: str, task_prompt: str, answer_a: str, answer_b: str) -> dict[str, Any]:
    prompt = f"""
Eres un juez tecnico ciego de una arena de IA.
Evalua dos respuestas para la misma tarea. No sabes que motor genero cada una.
Devuelve solo JSON valido con estos campos:
- winner: "a", "b" o "tie"
- score_a: numero de 1 a 10
- score_b: numero de 1 a 10
- reasoning: explicacion tecnica breve

Tarea original:
{task_prompt}

Respuesta A:
{answer_a}

Respuesta B:
{answer_b}
""".strip()
    payload = call_gemini(model, api_key, prompt)
    text = extract_text(payload)
    parsed = parse_json_object(text)
    return normalize_judgement(parsed)


def call_gemini(model: str, api_key: str, prompt: str) -> dict[str, Any]:
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        + urllib.parse.quote(model, safe="")
        + ":generateContent?key="
        + urllib.parse.quote(api_key, safe="")
    )
    body = json.dumps(
        {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def extract_text(payload: dict[str, Any]) -> str:
    candidates = payload.get("candidates") or []
    if not candidates:
        return ""
    parts = (((candidates[0] or {}).get("content") or {}).get("parts") or [])
    return "".join(str(part.get("text", "")) for part in parts if isinstance(part, dict)).strip()


def parse_json_object(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return {}
        parsed = json.loads(match.group(0))
    return parsed if isinstance(parsed, dict) else {}


def normalize_judgement(raw: dict[str, Any]) -> dict[str, Any]:
    winner = str(raw.get("winner", "tie")).lower()
    if winner not in {"a", "b", "tie"}:
        winner = "tie"
    return {
        "winner": winner,
        "score_a": _score(raw.get("score_a")),
        "score_b": _score(raw.get("score_b")),
        "reasoning": str(raw.get("reasoning", "")).strip(),
    }


def _score(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(1.0, min(10.0, number))


if __name__ == "__main__":
    raise SystemExit(main())
