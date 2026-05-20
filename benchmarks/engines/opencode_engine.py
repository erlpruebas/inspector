from __future__ import annotations

import json
import os
import shlex
import subprocess
import time
import shutil
from pathlib import Path

from .base_engine import EngineResult
from .codex_engine import _collect_outputs


class OpenCodeEngine:
    def __init__(
        self,
        command: list[str] | None = None,
        model: str = "",
        agent: str = "",
        timeout_seconds: int = 1800,
        name: str = "opencode",
    ) -> None:
        self.name = name
        command_text = os.getenv("BENCH_OPENCODE_COMMAND", os.getenv("ORCH_OPENCODE_COMMAND", "opencode"))
        self.command = command or shlex.split(_resolve_command(command_text), posix=False)
        self.model = model.strip() or os.getenv("BENCH_OPENCODE_MODEL", os.getenv("ORCH_OPENCODE_MODEL", "")).strip()
        self.agent = agent.strip() or os.getenv("BENCH_OPENCODE_AGENT", "build").strip()
        self.timeout_seconds = int(os.getenv("BENCH_OPENCODE_TIMEOUT_SECONDS", str(timeout_seconds)))
        self.dangerously_skip_permissions = _truthy(
            os.getenv("BENCH_OPENCODE_DANGEROUSLY_SKIP_PERMISSIONS", "true")
        )
        self.pure = _truthy(os.getenv("BENCH_OPENCODE_PURE", "true"))

    def run(self, task_id: str, prompt: str, workdir: Path, expected_outputs: list[str]) -> EngineResult:
        output_name = expected_outputs[0] if expected_outputs else "resultado.md"
        prompt = (
            prompt
            + f"\n\nArchivo de salida esperado: {output_name}."
            + "\nCrea o actualiza ese archivo en el directorio de trabajo con la respuesta final."
            + "\nNo termines la tarea hasta que el archivo exista."
        )
        prompt_file = workdir / "_benchmark_prompt.md"
        prompt_file.write_text(prompt, encoding="utf-8")

        command = [*self.command, "run"]
        if self.pure:
            command.append("--pure")
        if self.model:
            command.extend(["--model", self.model])
        if self.agent:
            command.extend(["--agent", self.agent])
        command.extend(["--dir", str(workdir)])
        command.extend(["--file", str(prompt_file)])
        if self.dangerously_skip_permissions:
            command.append("--dangerously-skip-permissions")
        command.extend(["--format", "json"])
        command.append("Ejecuta la tarea adjunta en _benchmark_prompt.md y crea el archivo de salida esperado.")

        started = time.monotonic()
        try:
            env = os.environ.copy()
            if env.get("GEMINI_API_KEY") and not env.get("GOOGLE_GENERATIVE_AI_API_KEY"):
                env["GOOGLE_GENERATIVE_AI_API_KEY"] = env["GEMINI_API_KEY"]
            process = subprocess.run(
                command,
                cwd=str(workdir),
                env=env,
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout_seconds,
            )
            stdout = fix_mojibake(process.stdout or "")
            stderr = fix_mojibake(process.stderr or "")
            timed_out = False
            returncode = process.returncode
        except subprocess.TimeoutExpired as exc:
            stdout = _clean(exc.stdout)
            stderr = _clean(exc.stderr)
            timed_out = True
            returncode = 124

        _repair_expected_outputs(workdir, expected_outputs)
        text_output = fix_mojibake(_extract_text_from_json(stdout))
        if text_output:
            _ensure_expected_output(workdir, expected_outputs, text_output)
        output_files = _collect_outputs(workdir, expected_outputs)
        if expected_outputs and returncode == 0 and not output_files:
            returncode = 1
            stderr = (stderr + "\n" if stderr else "") + "OpenCode finished without creating expected output."
        result = EngineResult(
            engine=self.name,
            task_id=task_id,
            returncode=returncode,
            stdout=text_output or stdout,
            stderr=stderr,
            output_files=output_files,
            elapsed_seconds=time.monotonic() - started,
            timed_out=timed_out,
            model=self.model,
        )
        return result


def _truthy(value: str) -> bool:
    return value.strip().lower() not in {"", "0", "false", "no", "off"}


def _resolve_command(command_text: str) -> str:
    if os.name == "nt":
        appdata = os.getenv("APPDATA", "")
        native = Path(appdata) / "npm" / "node_modules" / "opencode-ai" / "node_modules" / "opencode-windows-x64" / "bin" / "opencode.exe"
        if command_text == "opencode" and native.exists():
            return str(native)
        baseline = Path(appdata) / "npm" / "node_modules" / "opencode-ai" / "node_modules" / "opencode-windows-x64-baseline" / "bin" / "opencode.exe"
        if command_text == "opencode" and baseline.exists():
            return str(baseline)
        candidate = Path(appdata) / "npm" / f"{command_text}.cmd"
        if candidate.exists():
            return str(candidate)
    resolved = shutil.which(command_text) or shutil.which(f"{command_text}.cmd")
    if resolved:
        return resolved
    return command_text


def _clean(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _ensure_expected_output(workdir: Path, expected_outputs: list[str], stdout: str) -> None:
    if not expected_outputs or not stdout.strip():
        return
    target = workdir / expected_outputs[0]
    if target.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(stdout.strip() + "\n", encoding="utf-8")


def _repair_expected_outputs(workdir: Path, expected_outputs: list[str]) -> None:
    for relative in expected_outputs:
        path = workdir / relative
        if not path.exists() or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        repaired = fix_mojibake(text)
        if repaired != text:
            path.write_text(repaired, encoding="utf-8")


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


def _extract_text_from_json(stdout: str) -> str:
    lines = []
    for raw_line in stdout.splitlines():
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        text = _pick_event_text(event)
        if text:
            lines.append(text)
    return "\n".join(lines).strip()


def _pick_event_text(event: object) -> str:
    if not isinstance(event, dict):
        return ""
    if event.get("type") == "text":
        part = event.get("part")
        if isinstance(part, dict):
            text = part.get("text")
            if isinstance(text, str):
                return text
    if event.get("type") in {"message", "assistant_message"}:
        return _pick_text(event)
    return ""


def _pick_text(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = [_pick_text(item) for item in value]
        return "\n".join(part for part in parts if part).strip()
    if isinstance(value, dict):
        for key in ("text", "content", "message", "output", "delta", "value"):
            if key in value:
                picked = _pick_text(value[key])
                if picked:
                    return picked
        if "item" in value:
            picked = _pick_text(value["item"])
            if picked:
                return picked
        for key in ("type", "role"):
            if key in value and isinstance(value[key], str) and value[key]:
                return ""
    return ""
