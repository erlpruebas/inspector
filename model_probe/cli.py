from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


INSPECTOR_ROOT = Path(__file__).resolve().parents[1]
RESULTS_ROOT = Path(__file__).resolve().parent / "runs"


@dataclass(frozen=True)
class ProbeRequest:
    provider: str
    intent: str
    model: str
    docs_url: str
    api_key_env: str
    started_at: str


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Investigate and test an API provider/model with Codex CLI.")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run a provider/model probe.")
    run_parser.add_argument("--provider", required=True, help="Provider name, for example groq, gemini, openrouter.")
    run_parser.add_argument("--intent", required=True, help="What we want to test or prove.")
    run_parser.add_argument("--model", default="", help="Optional model name to test.")
    run_parser.add_argument("--docs-url", default="", help="Optional official documentation URL.")
    run_parser.add_argument("--api-key-env", default="", help="Environment variable that contains the provider API key.")
    run_parser.add_argument("--api-key", default="", help="Raw API key. Not written to disk; prefer --api-key-env.")
    run_parser.add_argument("--codex-command", default=os.getenv("MODEL_PROBE_CODEX_COMMAND", "codex"))
    run_parser.add_argument("--codex-model", default=os.getenv("MODEL_PROBE_CODEX_MODEL", "gpt-5.5"))
    run_parser.add_argument("--timeout", type=int, default=1800)

    args = parser.parse_args(argv)
    if args.command != "run":
        parser.print_help()
        return 2

    return run_probe(args)


def run_probe(args: argparse.Namespace) -> int:
    provider = clean_name(args.provider)
    run_dir = RESULTS_ROOT / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{provider}"
    run_dir.mkdir(parents=True, exist_ok=True)

    provider_key_env = args.api_key_env.strip() or default_key_env(provider)
    api_key = args.api_key.strip() or os.getenv(provider_key_env, "").strip()
    if not api_key:
        discovered = load_key_from_known_files(provider_key_env)
        api_key = discovered

    request = ProbeRequest(
        provider=provider,
        intent=args.intent.strip(),
        model=args.model.strip(),
        docs_url=args.docs_url.strip(),
        api_key_env=provider_key_env,
        started_at=datetime.now().isoformat(timespec="seconds"),
    )
    write_json(run_dir / "request.json", {**asdict(request), "api_key_present": bool(api_key)})

    prompt_path = run_dir / "codex_prompt.md"
    prompt_path.write_text(build_codex_prompt(request), encoding="utf-8")

    env = os.environ.copy()
    if api_key:
        env[provider_key_env] = api_key
        env["PROVIDER_API_KEY"] = api_key
    env["MODEL_PROBE_PROVIDER"] = provider
    if request.model:
        env["MODEL_PROBE_MODEL"] = request.model

    codex_stdout, codex_stderr, returncode = run_codex(
        args.codex_command,
        args.codex_model,
        prompt_path.read_text(encoding="utf-8"),
        run_dir,
        env,
        args.timeout,
    )
    (run_dir / "codex_stdout.jsonl").write_text(codex_stdout, encoding="utf-8", errors="replace")
    (run_dir / "codex_stderr.txt").write_text(codex_stderr, encoding="utf-8", errors="replace")
    (run_dir / "codex_report.md").write_text(extract_codex_messages(codex_stdout), encoding="utf-8", errors="replace")

    evaluation = evaluate_with_gemini(request, run_dir, returncode)
    if evaluation:
        (run_dir / "gemini_evaluation.md").write_text(evaluation, encoding="utf-8", errors="replace")

    summary = build_summary(request, run_dir, returncode, bool(evaluation))
    (run_dir / "summary.md").write_text(summary, encoding="utf-8", errors="replace")
    print(summary)
    return 0 if returncode == 0 else returncode


def build_codex_prompt(request: ProbeRequest) -> str:
    docs_line = f"- Official docs URL to start from: {request.docs_url}" if request.docs_url else "- Find the official documentation yourself before using third-party sources."
    model_line = f"- Model to test: {request.model}" if request.model else "- If no model is specified, discover the most relevant current model for the stated intent."
    return f"""
We are inside a dedicated model probe run directory.

Goal:
Investigate whether provider `{request.provider}` works for this intent:
{request.intent}

Inputs:
{model_line}
{docs_line}
- The provider API key is available only through environment variables:
  - `{request.api_key_env}`
  - `PROVIDER_API_KEY`

Rules:
- Do not print or write the API key.
- Prefer official documentation and official API endpoints.
- Create small reproducible tests in this run directory.
- Execute the tests and record exact commands, timings, HTTP status, and observed errors.
- If a test fails, propose the most likely fixes and how to verify them.
- Keep artifacts local to this run directory.

Required final report:
1. Verdict: works / partially works / does not work.
2. What was tested.
3. Exact result of each test.
4. Recommended configuration.
5. Next fixes if blocked.
""".strip()


def run_codex(command_text: str, model: str, prompt: str, run_dir: Path, env: dict[str, str], timeout: int) -> tuple[str, str, int]:
    command = shlex.split(command_text, posix=False)
    command.extend(["--cd", str(run_dir), "exec"])
    if model:
        command.extend(["--model", model])
    command.extend(["--json", "--skip-git-repo-check", prompt])
    process = subprocess.run(
        command,
        cwd=str(INSPECTOR_ROOT),
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    return process.stdout or "", process.stderr or "", process.returncode


def evaluate_with_gemini(request: ProbeRequest, run_dir: Path, codex_returncode: int) -> str:
    google_key = os.getenv("ORCH_GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or load_key_from_known_files("GOOGLE_API_KEY")
    if not google_key:
        return ""
    report = safe_read(run_dir / "codex_report.md", 16000)
    stderr = safe_read(run_dir / "codex_stderr.txt", 4000)
    prompt = f"""
Evalua este probe de proveedor/modelo.

Proveedor: {request.provider}
Modelo: {request.model or "(no especificado)"}
Intencion: {request.intent}
Codigo de salida de Codex: {codex_returncode}

Reporte de Codex:
{report}

Errores:
{stderr}

Devuelve una evaluacion breve en espanol con:
- veredicto
- confianza
- riesgos
- siguiente accion recomendada
""".strip()
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1},
    }
    model = os.getenv("MODEL_PROBE_GEMINI_MODEL", os.getenv("ORCH_GOOGLE_INTENT_MODEL", "gemini-2.5-flash-lite"))
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        + urllib.parse.quote(model, safe="")
        + ":generateContent?key="
        + urllib.parse.quote(google_key, safe="")
    )
    try:
        request_obj = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request_obj, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8", errors="replace"))
    except Exception as exc:
        return f"No se pudo evaluar con Gemini: {exc}"
    parts = (((result.get("candidates") or [{}])[0].get("content") or {}).get("parts") or [])
    return "".join(str(part.get("text", "")) for part in parts if isinstance(part, dict)).strip()


def build_summary(request: ProbeRequest, run_dir: Path, returncode: int, evaluated: bool) -> str:
    lines = [
        "# Model probe summary",
        "",
        f"- Provider: `{request.provider}`",
        f"- Model: `{request.model or '(auto)'}`",
        f"- Intent: {request.intent}",
        f"- Return code: `{returncode}`",
        f"- Gemini evaluation: {'yes' if evaluated else 'no'}",
        f"- Run directory: `{run_dir}`",
        "",
        "Artifacts:",
        "",
        "- `request.json`",
        "- `codex_prompt.md`",
        "- `codex_stdout.jsonl`",
        "- `codex_stderr.txt`",
        "- `codex_report.md`",
        "- `gemini_evaluation.md` if evaluation was available",
    ]
    return "\n".join(lines)


def extract_codex_messages(stdout: str) -> str:
    messages: list[str] = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get("item")
        if isinstance(item, dict) and item.get("type") == "agent_message" and item.get("text"):
            messages.append(str(item["text"]))
    if messages:
        return "\n\n".join(messages)
    return stdout


def load_key_from_known_files(env_name: str) -> str:
    for path in (Path("D:/credenciales"), INSPECTOR_ROOT / ".env", Path("D:/variables/.env")):
        if not path.exists():
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line in lines:
            if f"{env_name}=" not in line:
                continue
            return line.split(f"{env_name}=", 1)[1].strip().strip('"').strip("'")
    return ""


def default_key_env(provider: str) -> str:
    mapping = {
        "groq": "GROQ_API_KEY",
        "gemini": "GOOGLE_API_KEY",
        "google": "GOOGLE_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }
    return mapping.get(provider.casefold(), f"{provider.upper()}_API_KEY")


def clean_name(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value.strip().lower())
    return cleaned or "provider"


def safe_read(path: Path, max_chars: int) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:max_chars]
    except OSError:
        return ""


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
