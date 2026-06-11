from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import threading
import time
from pathlib import Path

from .base_engine import EngineResult

DEFAULT_CODEX_MODEL = "gpt-5.5"


class CodexEngine:
    def __init__(
        self,
        command: list[str] | None = None,
        sandbox: str = "workspace-write",
        approval: str = "never",
        model: str = "",
        name: str = "codex",
        timeout_seconds: int = 1800,
    ) -> None:
        self.name = name
        command_text = os.getenv("BENCH_CODEX_COMMAND", os.getenv("ORCH_CODEX_COMMAND", "codex"))
        self.command = command or _resolve_command(shlex.split(command_text, posix=False))
        self.sandbox = os.getenv("BENCH_CODEX_SANDBOX", os.getenv("ORCH_CODEX_SANDBOX", sandbox)).strip()
        self.approval = os.getenv("BENCH_CODEX_APPROVAL", os.getenv("ORCH_CODEX_APPROVAL", approval)).strip()
        self.model = model.strip() or DEFAULT_CODEX_MODEL
        self.timeout_seconds = int(os.getenv("BENCH_CODEX_TIMEOUT_SECONDS", str(timeout_seconds)))
        self._processes: dict[str, subprocess.Popen[str]] = {}
        self._process_lock = threading.RLock()

    def run(self, task_id: str, prompt: str, workdir: Path, expected_outputs: list[str]) -> EngineResult:
        command = [*self.command]
        if self.approval:
            command.extend(["--ask-for-approval", self.approval])
        if self.sandbox:
            command.extend(["--sandbox", self.sandbox])
        command.extend(["--cd", str(workdir), "exec"])
        if self.model:
            command.extend(["--model", self.model])
        command.extend(["--json", "--skip-git-repo-check", prompt])

        started = time.monotonic()
        try:
            process = subprocess.Popen(
                command,
                cwd=str(workdir),
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            with self._process_lock:
                self._processes[task_id] = process
            try:
                stdout, stderr = process.communicate(timeout=self.timeout_seconds)
            finally:
                with self._process_lock:
                    self._processes.pop(task_id, None)
            returncode = process.returncode
            timed_out = False
        except subprocess.TimeoutExpired as exc:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
            stdout = _clean(exc.stdout)
            stderr = _clean(exc.stderr)
            returncode = 124
            timed_out = True
        except OSError as exc:
            return EngineResult(
                engine=self.name,
                task_id=task_id,
                returncode=127,
                stdout="",
                stderr=f"{type(exc).__name__}: {exc}",
                output_files=[],
                elapsed_seconds=time.monotonic() - started,
                timed_out=False,
                model=self.model,
                error_type="command_not_found",
            )

        clean_stdout = _codex_text_from_stdout(stdout) or stdout
        combined_output = f"{clean_stdout}\n{stderr}".casefold()
        error_type = (
            "usage_limit"
            if "usage limit" in combined_output
            or "rate limit" in combined_output
            or "quota" in combined_output
            else ""
        )
        _ensure_expected_output(workdir, expected_outputs, clean_stdout)
        output_files = _collect_outputs(workdir, expected_outputs)
        if expected_outputs and returncode == 0 and not output_files:
            returncode = 1
            stderr = (stderr + "\n" if stderr else "") + "Codex finished without creating expected output."
        return EngineResult(
            engine=self.name,
            task_id=task_id,
            returncode=returncode,
            stdout=clean_stdout,
            stderr=stderr,
            output_files=output_files,
            elapsed_seconds=time.monotonic() - started,
            timed_out=timed_out,
            model=self.model,
            error_type=error_type,
        )

    def cancel(self, task_id: str) -> bool:
        with self._process_lock:
            process = self._processes.get(task_id)
        if process is None or process.poll() is not None:
            return False
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
        return True


def _resolve_command(command: list[str]) -> list[str]:
    if not command:
        return ["codex"]
    executable = command[0]
    if Path(executable).exists() or shutil.which(executable):
        return command
    if executable.lower() == "codex":
        found = _find_codex()
        if found:
            return [found, *command[1:]]
    return command


def _find_codex() -> str:
    candidates: list[Path] = []
    appdata = os.getenv("USERPROFILE", "")
    if appdata:
        candidates.extend(Path(appdata).glob(".vscode/extensions/openai.chatgpt-*/bin/windows-x86_64/codex.exe"))
        candidates.extend(Path(appdata).glob(".vscode-insiders/extensions/openai.chatgpt-*/bin/windows-x86_64/codex.exe"))
    for name in ("codex.cmd", "codex.exe", "codex"):
        resolved = shutil.which(name)
        if resolved:
            return resolved
    existing = [path for path in candidates if path.exists()]
    if existing:
        return str(max(existing, key=lambda path: path.stat().st_mtime))
    return ""


def _clean(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _codex_text_from_stdout(stdout: str) -> str:
    messages: list[str] = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get("item")
        if isinstance(item, dict) and item.get("type") == "agent_message" and item.get("text"):
            messages.append(str(item["text"]))
    return "\n\n".join(messages)


def _collect_outputs(workdir: Path, expected_outputs: list[str]) -> list[str]:
    found: list[str] = []
    for relative in expected_outputs:
        path = workdir / relative
        if path.exists():
            found.append(str(path))
    if not found:
        generated = [
            path
            for path in workdir.iterdir()
            if path.is_file() and path.name not in {"usage.json"} and path.name.startswith(("resultado", "output", "informe"))
        ]
        found.extend(str(path) for path in generated)
    return found


def _ensure_expected_output(workdir: Path, expected_outputs: list[str], stdout: str) -> None:
    if not expected_outputs or not stdout.strip():
        return
    target = workdir / expected_outputs[0]
    if target.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(stdout.strip() + "\n", encoding="utf-8")
