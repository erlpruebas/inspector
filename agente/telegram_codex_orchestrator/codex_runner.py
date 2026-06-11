from __future__ import annotations

import json
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from config import Settings


@dataclass(frozen=True)
class CodexResult:
    returncode: int
    stdout: str
    stderr: str
    thread_id: str = ""
    timed_out: bool = False
    cancelled: bool = False

    @property
    def text(self) -> str:
        parts: list[str] = []
        if self.cancelled:
            parts.append("Tarea de Codex cancelada.")
        if self.timed_out:
            parts.append("Codex agoto el tiempo maximo de ejecucion.")
        clean_stdout = _codex_text_from_stdout(self.stdout)
        if clean_stdout.strip():
            parts.append(clean_stdout.strip())
        if self.stderr.strip() and not self.cancelled and (self.returncode != 0 or self.timed_out):
            parts.append("STDERR:\n" + self.stderr.strip())
        if not parts:
            parts.append(f"Codex termino sin salida. Codigo: {self.returncode}")
        return "\n\n".join(parts)


class CodexRunner:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._lock = threading.Lock()
        self._process: subprocess.Popen[str] | None = None
        self._cancel_requested = False

    def run(self, instruction: str, thread_id: str = "") -> CodexResult:
        workdir = self.settings.codex_workdir
        workdir.mkdir(parents=True, exist_ok=True)

        command = self._build_command(workdir, instruction, thread_id=thread_id)
        with self._lock:
            self._cancel_requested = False
            self._process = subprocess.Popen(
                command,
                cwd=str(workdir),
                text=True,
                encoding="utf-8",
                errors="replace",
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            process = self._process

        try:
            stdout, stderr = process.communicate(timeout=self.settings.codex_timeout_seconds)
            cancelled = self._cancel_requested or process.returncode in {-15, -9}
            return CodexResult(
                returncode=process.returncode if process.returncode is not None else 1,
                stdout=stdout or "",
                stderr=stderr or "",
                thread_id=_thread_id_from_stdout(stdout or ""),
                cancelled=cancelled,
            )
        except subprocess.TimeoutExpired as exc:
            self.cancel()
            stdout, stderr = process.communicate(timeout=10)
            return CodexResult(
                returncode=124,
                stdout=_clean_output(stdout or exc.stdout),
                stderr=_clean_output(stderr or exc.stderr),
                thread_id=_thread_id_from_stdout(_clean_output(stdout or exc.stdout)),
                timed_out=True,
            )
        finally:
            with self._lock:
                if self._process is process:
                    self._process = None

    def cancel(self) -> bool:
        with self._lock:
            process = self._process
            self._cancel_requested = True
        if process is None or process.poll() is not None:
            return False
        try:
            process.terminate()
            deadline = time.monotonic() + 5
            while process.poll() is None and time.monotonic() < deadline:
                time.sleep(0.1)
            if process.poll() is None:
                process.kill()
            return True
        except OSError:
            return False

    def is_running(self) -> bool:
        with self._lock:
            return self._process is not None and self._process.poll() is None

    def preview_command(self, instruction: str, thread_id: str = "") -> str:
        command = self._build_command(self.settings.codex_workdir, instruction, thread_id=thread_id)
        return subprocess.list2cmdline(command)

    def _build_command(self, workdir: Path, instruction: str, thread_id: str = "") -> list[str]:
        command = [*self.settings.codex_command]
        if self.settings.codex_approval:
            command.extend(["--ask-for-approval", self.settings.codex_approval])
        if self.settings.codex_sandbox:
            command.extend(["--sandbox", self.settings.codex_sandbox])
        command.extend(["--cd", str(workdir)])
        for extra_dir in self.settings.codex_extra_dirs:
            command.extend(["--add-dir", str(extra_dir)])
        command.append("exec")
        if thread_id:
            command.extend(["resume", "--json", "--skip-git-repo-check"])
            if self.settings.codex_model:
                command.extend(["--model", self.settings.codex_model])
            command.extend([thread_id, instruction])
        else:
            if self.settings.codex_model:
                command.extend(["--model", self.settings.codex_model])
            command.extend(["--json", "--skip-git-repo-check", instruction])
        return command


def _clean_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _thread_id_from_stdout(stdout: str) -> str:
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "thread.started" and event.get("thread_id"):
            return str(event["thread_id"])
    return ""


def _codex_text_from_stdout(stdout: str) -> str:
    messages: list[str] = []
    saw_json = False
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        saw_json = True
        item = event.get("item")
        if isinstance(item, dict) and item.get("type") == "agent_message" and item.get("text"):
            messages.append(str(item["text"]))
    if messages:
        return "\n\n".join(messages)
    return "" if saw_json else stdout
