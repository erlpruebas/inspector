from __future__ import annotations

import os
import json
import shlex
import subprocess
import time
import re
from pathlib import Path

from .base_engine import EngineResult
from .codex_engine import _collect_outputs


class CommandEngine:
    def __init__(
        self,
        name: str,
        command_template: str,
        timeout_seconds: int = 1800,
        model: str = "",
        inject_workspace: bool = True,
        stdin_prompt: bool = False,
    ) -> None:
        self.name = name
        self.model = model
        self.command_template = command_template
        self.inject_workspace = inject_workspace
        self.stdin_prompt = stdin_prompt
        self.timeout_seconds = int(os.getenv(f"BENCH_{name.upper()}_TIMEOUT_SECONDS", str(timeout_seconds)))

    def run(self, task_id: str, prompt: str, workdir: Path, expected_outputs: list[str]) -> EngineResult:
        if self.inject_workspace:
            prompt = prompt_with_workspace_files(prompt, workdir, expected_outputs[0] if expected_outputs else "resultado.md")
        prompt_file = workdir / "_benchmark_prompt.md"
        prompt_file.write_text(prompt, encoding="utf-8")
        rendered = self.command_template.format(
            prompt=_quote_arg(prompt),
            prompt_file=_quote_arg(prompt_file.read_text(encoding="utf-8")),
            prompt_path=_quote_arg(str(prompt_file)),
            task_id=_quote_arg(task_id),
            workdir=_quote_arg(str(workdir)),
            output=_quote_arg(expected_outputs[0] if expected_outputs else "resultado.md"),
        )
        command = [_unquote_arg(part) for part in shlex.split(rendered, posix=False)]
        started = time.monotonic()
        try:
            process = subprocess.run(
                command,
                cwd=str(workdir),
                input=prompt if self.stdin_prompt else None,
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout_seconds,
            )
            stdout = strip_ansi(process.stdout or "")
            stderr = strip_ansi(process.stderr or "")
            _ensure_expected_output(workdir, expected_outputs, stdout)
            return EngineResult(
                engine=self.name,
                task_id=task_id,
                returncode=process.returncode,
                stdout=stdout,
                stderr=stderr,
                output_files=_collect_outputs(workdir, expected_outputs),
                elapsed_seconds=time.monotonic() - started,
                usage=_read_usage(workdir),
                model=self.model or _read_usage(workdir).get("model", ""),
            )
        except subprocess.TimeoutExpired as exc:
            return EngineResult(
                engine=self.name,
                task_id=task_id,
                returncode=124,
                stdout=_clean(exc.stdout),
                stderr=_clean(exc.stderr),
                output_files=_collect_outputs(workdir, expected_outputs),
                elapsed_seconds=time.monotonic() - started,
                timed_out=True,
                usage=_read_usage(workdir),
                model=self.model or _read_usage(workdir).get("model", ""),
            )


def _clean(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _quote_arg(value: str) -> str:
    return '"' + value.replace('"', '\\"') + '"'


def _unquote_arg(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return value[1:-1].replace('\\"', '"')
    return value


def _read_usage(workdir: Path) -> dict[str, object]:
    path = workdir / "usage.json"
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _ensure_expected_output(workdir: Path, expected_outputs: list[str], stdout: str) -> None:
    if not expected_outputs or not stdout.strip():
        return
    target = workdir / expected_outputs[0]
    if target.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(stdout.strip() + "\n", encoding="utf-8")


def prompt_with_workspace_files(prompt: str, workdir: Path, output: str) -> str:
    context = workspace_file_context(workdir)
    prompt = (
        prompt
        + f"\n\nArchivo de salida esperado: {output}."
        + "\nDevuelve el contenido final o crea ese archivo en el directorio de trabajo."
    )
    if not context:
        return prompt
    return prompt + "\n\nArchivos disponibles en el directorio de trabajo:\n\n" + context


def workspace_file_context(workdir: Path) -> str:
    parts: list[str] = []
    skip_names = {"resultado.md", "usage.json", "_benchmark_prompt.md"}
    for path in sorted(workdir.rglob("*")):
        if not path.is_file() or path.name in skip_names or "privacy" in path.parts:
            continue
        if path.stat().st_size > 80_000:
            parts.append(f"### {path.relative_to(workdir)}\n[archivo omitido por tamano: {path.stat().st_size} bytes]")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        parts.append(f"### {path.relative_to(workdir)}\n```text\n{text}\n```")
    return "\n\n".join(parts)


def strip_ansi(value: str) -> str:
    return re.sub(r"\x1b\[[0-9;?]*[ -/]*[@-~]", "", value)
