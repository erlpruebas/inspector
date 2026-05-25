from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.engines.codex_engine import CodexEngine  # noqa: E402
from orchestrator_v2.desktop_codex_operator import run_desktop_codex_operator  # noqa: E402


RUN_ROOT = ROOT / "assistant" / "runtime" / "codex_oneshot"


def safe_name(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in "._-" else "_" for char in value)
    cleaned = cleaned.strip("._-")
    return cleaned or "archivo"


def copy_files(files: list[str], workdir: Path) -> list[Path]:
    copied: list[Path] = []
    input_dir = workdir / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    for raw in files:
        source = Path(raw)
        if not source.exists() or not source.is_file():
            continue
        target = input_dir / safe_name(source.name)
        if target.exists():
            target = input_dir / f"{source.stem}_{datetime.now().strftime('%H%M%S_%f')}{source.suffix}"
        shutil.copy2(source, target)
        copied.append(target)
    return copied


def build_prompt(text: str, files: list[Path], source: str, thread_id: str) -> str:
    file_lines = "\n".join(f"- {path.relative_to(path.parents[1])}" for path in files) or "- Ninguno"
    return f"""
Eres Codex CLI ejecutando una peticion unica del gestor Inspector.

Objetivo:
Resuelve completamente la peticion del usuario en este turno. No abras una conversacion,
no pidas confirmacion salvo que exista un bloqueo real de credenciales, login, pago,
destruccion de datos o riesgo claro.

Peticion del usuario:
{text}

Origen:
- source: {source}
- thread_id: {thread_id}

Archivos disponibles:
{file_lines}

Reglas:
- Trabaja dentro de este directorio de ejecucion.
- Si el usuario dice "lo que te acabo de enviar", "el archivo adjunto" o similar,
  revisa los archivos de `input/`.
- Si creas archivos finales, mencionalos en la respuesta.
- Escribe siempre la respuesta final en `resultado.md`.
- La respuesta final debe ser util por si sola: que hiciste, resultado, archivos
  creados/modificados y cualquier pendiente real.
""".strip()


def run_cli(text: str, files: list[str], source: str, thread_id: str, model: str) -> dict:
    run_dir = RUN_ROOT / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_dir.mkdir(parents=True, exist_ok=True)
    copied = copy_files(files, run_dir)
    prompt = build_prompt(text, copied, source, thread_id)
    (run_dir / "prompt.md").write_text(prompt, encoding="utf-8")

    engine = CodexEngine(model=model, name=f"codex_{model.replace('.', '_').replace('-', '_')}")
    result = engine.run("assistant-oneshot", prompt, run_dir, ["resultado.md"])
    output = ""
    result_path = run_dir / "resultado.md"
    if result_path.exists():
        output = result_path.read_text(encoding="utf-8", errors="replace").strip()
    if not output:
        output = (result.stdout or "").strip()
    return {
        "ok": result.ok,
        "mode": "codex_cli",
        "model": result.model,
        "output": output,
        "workdir": str(run_dir),
        "elapsed_seconds": round(result.elapsed_seconds, 3),
        "files": [str(path) for path in copied],
        "stderr": result.stderr,
        "returncode": result.returncode,
    }


def run_desktop(text: str, files: list[str], source: str, thread_id: str, wait_seconds: int) -> dict:
    run_dir = RUN_ROOT / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_dir.mkdir(parents=True, exist_ok=True)
    copied = copy_files(files, run_dir)
    prompt = build_prompt(text, copied, source, thread_id)
    result = run_desktop_codex_operator(prompt, send=True, wait_seconds=wait_seconds)
    return {
        "ok": result.ok,
        "mode": "codex_desktop",
        "model": "codex-desktop",
        "output": (
            f"Codex Desktop: {result.status}\n\n"
            f"Prompt: {result.prompt_path}\n"
            f"Evidencias: {result.run_dir}\n"
            f"Captura: {result.screenshot_path or '-'}\n"
            f"Error: {result.error or '-'}"
        ).strip(),
        "workdir": str(result.run_dir),
        "elapsed_seconds": None,
        "files": [str(path) for path in copied],
        "stderr": result.error,
        "returncode": 0 if result.ok else 1,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["cli", "desktop"], default="cli")
    parser.add_argument("--text", required=True)
    parser.add_argument("--files-json", default="[]")
    parser.add_argument("--source", default="desktop")
    parser.add_argument("--thread-id", default="default")
    parser.add_argument("--model", default="gpt-5.4-mini")
    parser.add_argument("--desktop-wait-seconds", type=int, default=1800)
    args = parser.parse_args()

    try:
        files = json.loads(args.files_json)
        if not isinstance(files, list):
            files = []
    except json.JSONDecodeError:
        files = []

    if args.mode == "desktop":
        payload = run_desktop(args.text, [str(item) for item in files], args.source, args.thread_id, args.desktop_wait_seconds)
    else:
        payload = run_cli(args.text, [str(item) for item in files], args.source, args.thread_id, args.model)
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
