from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from ..config import load_config
from ..scheduling.codex_quota import CodexQuotaMonitor
from .preferences import PreferenceStore


SendMessage = Callable[[int | str, str], None]
CompleteImplementation = Callable[[int | str, str, str, bool], None]

PROPOSAL_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "understanding": {"type": "string"},
        "changes": {"type": "array", "items": {"type": "string"}},
        "files": {"type": "array", "items": {"type": "string"}},
        "tests": {"type": "array", "items": {"type": "string"}},
        "risks": {"type": "array", "items": {"type": "string"}},
        "open_questions": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "title",
        "understanding",
        "changes",
        "files",
        "tests",
        "risks",
        "open_questions",
    ],
    "additionalProperties": False,
}


@dataclass
class RunningTask:
    process: Optional[subprocess.Popen[str]] = None
    cancelled: bool = False


class DevelopmentModeController:
    """Persistent proposal/approval workflow for Telegram development tasks."""

    def __init__(
        self,
        project_root: Optional[Path] = None,
        *,
        quota_monitor: Optional[CodexQuotaMonitor] = None,
    ) -> None:
        config = load_config()
        self.project_root = (project_root or Path.cwd()).resolve()
        self.runtime_root = (config.workspace_root / "development").resolve()
        self.state_root = self.runtime_root / "state"
        self.quota_monitor = quota_monitor or CodexQuotaMonitor()
        self.preferences = PreferenceStore()
        self._tasks: dict[str, RunningTask] = {}
        self._task_lock = threading.Lock()
        self._publication_lock = threading.Lock()

    def is_active(self, chat_id: int | str) -> bool:
        return bool(self._load_state(chat_id).get("active", False))

    def activate(self, chat_id: int | str) -> None:
        self._save_state(
            chat_id,
            {
                "active": True,
                "phase": "idle",
                "proposal_version": 0,
                "activated_at": _timestamp(),
            },
        )
        self.preferences.set_development_mode(True)

    def deactivate(self, chat_id: int | str) -> bool:
        cancelled = self.cancel_running_task(chat_id)
        path = self._state_path(chat_id)
        if path.exists():
            path.unlink()
        self.preferences.set_development_mode(False)
        return cancelled

    def process(
        self,
        chat_id: int | str,
        text: str,
        *,
        send_message: SendMessage,
        complete_implementation: CompleteImplementation,
    ) -> bool:
        command = normalize_command(text)
        if command == "activar modo desarrollo":
            self.activate(chat_id)
            send_message(
                chat_id,
                "Modo desarrollo activado.\n\n"
                "Describe el cambio. Preparare una propuesta sin modificar el codigo.",
            )
            return True
        if command == "desactivar modo desarrollo":
            cancelled = self.deactivate(chat_id)
            suffix = " La tarea en curso se ha cancelado." if cancelled else ""
            send_message(chat_id, f"Modo desarrollo desactivado.{suffix}")
            return True
        if not self.is_active(chat_id):
            return False

        state = self._load_state(chat_id)
        phase = str(state.get("phase", "idle"))
        if phase in {"proposing", "implementing"}:
            if self._has_running_task(chat_id):
                send_message(
                    chat_id,
                    "Hay una tarea de desarrollo en curso. "
                    "Puedes desactivar el modo desarrollo para cancelarla.",
                )
                return True
            state["phase"] = "awaiting_approval" if state.get("proposal") else "idle"
            self._save_state(chat_id, state)
            phase = str(state["phase"])

        if phase == "awaiting_approval":
            if _is_yes(command):
                self._start_implementation(
                    chat_id,
                    send_message=send_message,
                    complete_implementation=complete_implementation,
                )
                return True
            if _is_no(command):
                state.update(
                    phase="idle",
                    pending_request="",
                    proposal=None,
                )
                self._save_state(chat_id, state)
                send_message(chat_id, "Propuesta descartada. Describe una nueva tarea.")
                return True
            self._start_proposal(
                chat_id,
                text,
                send_message=send_message,
                revision=True,
            )
            return True

        self._start_proposal(
            chat_id,
            text,
            send_message=send_message,
            revision=False,
        )
        return True

    def cancel_running_task(self, chat_id: int | str) -> bool:
        with self._task_lock:
            task = self._tasks.get(str(chat_id))
            if task is None:
                return False
            task.cancelled = True
            process = task.process
        if process is not None and process.poll() is None:
            _terminate_process_tree(process)
        return True

    def _start_proposal(
        self,
        chat_id: int | str,
        text: str,
        *,
        send_message: SendMessage,
        revision: bool,
    ) -> None:
        if not self._codex_available(send_message, chat_id):
            return
        state = self._load_state(chat_id)
        request_text = (
            str(state.get("pending_request", "")).strip()
            if revision
            else text.strip()
        )
        previous = state.get("proposal") if revision else None
        version = int(state.get("proposal_version", 0)) + 1
        state.update(
            phase="proposing",
            pending_request=request_text,
            proposal_version=version,
            last_feedback=text.strip() if revision else "",
        )
        self._save_state(chat_id, state)
        task = RunningTask()
        self._register_task(chat_id, task)
        send_message(chat_id, "Revisando el proyecto y preparando la propuesta.")
        threading.Thread(
            target=self._proposal_worker,
            args=(chat_id, request_text, text.strip() if revision else "", previous, version, task, send_message),
            daemon=True,
            name=f"agent22-development-proposal-{chat_id}",
        ).start()

    def _proposal_worker(
        self,
        chat_id: int | str,
        request_text: str,
        feedback: str,
        previous: Any,
        version: int,
        task: RunningTask,
        send_message: SendMessage,
    ) -> None:
        started = time.monotonic()
        try:
            proposal = self._run_proposal(request_text, feedback, previous, task)
            if task.cancelled or not self.is_active(chat_id):
                return
            state = self._load_state(chat_id)
            state.update(
                phase="awaiting_approval",
                proposal=proposal,
                proposal_version=version,
                last_proposal_seconds=round(time.monotonic() - started, 3),
            )
            self._save_state(chat_id, state)
            send_message(
                chat_id,
                _format_proposal(proposal, version, time.monotonic() - started),
            )
        except Exception as exc:
            if not task.cancelled and self.is_active(chat_id):
                state = self._load_state(chat_id)
                state.update(phase="idle", last_error=_short_error(exc))
                self._save_state(chat_id, state)
                send_message(chat_id, f"No he podido preparar la propuesta: {_short_error(exc)}")
        finally:
            self._unregister_task(chat_id, task)

    def _start_implementation(
        self,
        chat_id: int | str,
        *,
        send_message: SendMessage,
        complete_implementation: CompleteImplementation,
    ) -> None:
        if not self._codex_available(send_message, chat_id):
            return
        state = self._load_state(chat_id)
        request_text = str(state.get("pending_request", "")).strip()
        proposal = state.get("proposal")
        if not request_text or not isinstance(proposal, dict):
            state["phase"] = "idle"
            self._save_state(chat_id, state)
            send_message(chat_id, "La propuesta pendiente no es valida.")
            return
        state["phase"] = "implementing"
        self._save_state(chat_id, state)
        task = RunningTask()
        self._register_task(chat_id, task)
        send_message(
            chat_id,
            "Propuesta aprobada. Codex trabajara en un worktree Git aislado.",
        )
        threading.Thread(
            target=self._implementation_worker,
            args=(chat_id, request_text, proposal, task, complete_implementation),
            daemon=True,
            name=f"agent22-development-implementation-{chat_id}",
        ).start()

    def _implementation_worker(
        self,
        chat_id: int | str,
        request_text: str,
        proposal: dict[str, Any],
        task: RunningTask,
        complete_implementation: CompleteImplementation,
    ) -> None:
        worktree: Optional[Path] = None
        branch = ""
        commit_sha = ""
        integrated = False
        started = time.monotonic()
        try:
            worktree, branch = self._create_worktree(chat_id)
            final_message = self._run_implementation(
                worktree,
                request_text,
                proposal,
                task,
            )
            if task.cancelled or not self.is_active(chat_id):
                return
            commit_sha = self._commit_worktree(worktree, proposal)
            with self._publication_lock:
                commit_sha = self._rebase_onto_head(worktree)
                _run_git(self.project_root, "cherry-pick", commit_sha)
                integrated = True
                pushed, detail = self._push_current_branch()
            state = self._load_state(chat_id)
            state.update(
                phase="idle",
                pending_request="",
                proposal=None,
                last_commit=commit_sha,
                last_completed_at=_timestamp(),
            )
            self._save_state(chat_id, state)
            publication = (
                f"Publicado en `{detail}`."
                if pushed
                else f"Commit local `{commit_sha[:8]}`. Push pendiente: {detail}"
            )
            complete_implementation(
                chat_id,
                request_text,
                f"{final_message}\n\n{publication}\n"
                f"Duracion: {_duration(time.monotonic() - started)}",
                True,
            )
        except Exception as exc:
            state = self._load_state(chat_id)
            state.update(
                phase="awaiting_approval",
                last_error=_short_error(exc),
                recovery_branch=branch,
                recovery_commit=commit_sha,
            )
            self._save_state(chat_id, state)
            if not task.cancelled and self.is_active(chat_id):
                complete_implementation(
                    chat_id,
                    request_text,
                    "La implementacion no se ha incorporado.\n\n"
                    f"Motivo: {_short_error(exc)}\n"
                    "La propuesta sigue pendiente para corregirla o reintentar.",
                    False,
                )
        finally:
            self._cleanup_worktree(
                worktree,
                branch,
                delete_branch=integrated or not commit_sha,
            )
            self._unregister_task(chat_id, task)

    def _run_proposal(
        self,
        request_text: str,
        feedback: str,
        previous: Any,
        task: RunningTask,
    ) -> dict[str, Any]:
        run_dir = self._new_run_dir("proposal")
        schema_path = run_dir / "schema.json"
        output_path = run_dir / "proposal.json"
        schema_path.write_text(json.dumps(PROPOSAL_SCHEMA, indent=2), encoding="utf-8")
        revision = ""
        if feedback:
            revision = (
                "\nPrevious proposal:\n"
                f"{json.dumps(previous, ensure_ascii=False, indent=2)}\n"
                f"User feedback:\n{feedback}\n"
            )
        prompt = (
            "Inspect this repository and prepare a concrete implementation proposal. "
            "Do not edit files. Return only the JSON required by the supplied schema. "
            "Write user-facing fields in Spanish.\n\n"
            f"Request:\n{request_text}\n{revision}"
        )
        command = self._codex_command(
            cwd=self.project_root,
            prompt=prompt,
            output_path=output_path,
            schema_path=schema_path,
            sandbox="read-only",
        )
        self._run_process(command, task, timeout=900)
        return json.loads(output_path.read_text(encoding="utf-8"))

    def _run_implementation(
        self,
        worktree: Path,
        request_text: str,
        proposal: dict[str, Any],
        task: RunningTask,
    ) -> str:
        output_path = self._new_run_dir("implementation") / "final.md"
        prompt = (
            "Implement the approved request in this isolated Git worktree. "
            "Inspect first, preserve architecture and unrelated work, update relevant "
            "documentation, and run focused tests. Do not commit, push or manipulate "
            "worktrees; the parent controller handles Git.\n\n"
            f"Request:\n{request_text}\n\n"
            f"Approved proposal:\n{json.dumps(proposal, ensure_ascii=False, indent=2)}"
        )
        command = self._codex_command(
            cwd=worktree,
            prompt=prompt,
            output_path=output_path,
            sandbox="workspace-write",
        )
        self._run_process(command, task, timeout=3600)
        if not output_path.exists():
            raise RuntimeError("Codex no devolvio un resumen final.")
        return output_path.read_text(encoding="utf-8", errors="replace").strip()

    def _codex_command(
        self,
        *,
        cwd: Path,
        prompt: str,
        output_path: Path,
        sandbox: str,
        schema_path: Optional[Path] = None,
    ) -> list[str]:
        command = [
            _find_codex(),
            "exec",
            "--ephemeral",
            "--sandbox",
            sandbox,
            "-c",
            'approval_policy="never"',
            "--color",
            "never",
            "--cd",
            str(cwd),
            "--output-last-message",
            str(output_path),
        ]
        if schema_path is not None:
            command.extend(["--output-schema", str(schema_path)])
        command.append(prompt)
        return command

    def _run_process(
        self,
        command: list[str],
        task: RunningTask,
        *,
        timeout: int,
    ) -> None:
        process = subprocess.Popen(
            command,
            cwd=self.project_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        with self._task_lock:
            task.process = process
        try:
            _, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            _terminate_process_tree(process)
            process.communicate()
            raise TimeoutError("Codex supero el tiempo maximo.")
        finally:
            with self._task_lock:
                task.process = None
        if task.cancelled:
            raise RuntimeError("Tarea cancelada.")
        if process.returncode != 0:
            raise RuntimeError(_last_line(stderr) or f"Codex termino con codigo {process.returncode}.")

    def _create_worktree(self, chat_id: int | str) -> tuple[Path, str]:
        stamp = f"{int(time.time())}-{os.getpid()}"
        branch = f"codex/telegram-dev-{_safe_id(str(chat_id))}-{stamp}"
        worktree = self.runtime_root / "worktrees" / _safe_id(str(chat_id)) / stamp
        worktree.parent.mkdir(parents=True, exist_ok=True)
        _run_git(self.project_root, "worktree", "add", "-b", branch, str(worktree), "HEAD")
        return worktree, branch

    def _commit_worktree(self, worktree: Path, proposal: dict[str, Any]) -> str:
        if not _run_git(worktree, "status", "--porcelain").strip():
            raise RuntimeError("Codex termino sin producir cambios.")
        _run_git(worktree, "add", "--all")
        title = " ".join(str(proposal.get("title", "development change")).split())
        _run_git(worktree, "commit", "-m", f"feat: {title[:65]}")
        return _run_git(worktree, "rev-parse", "HEAD").strip()

    def _rebase_onto_head(self, worktree: Path) -> str:
        current = _run_git(self.project_root, "rev-parse", "HEAD").strip()
        parent = _run_git(worktree, "rev-parse", "HEAD^").strip()
        if parent != current:
            _run_git(worktree, "rebase", current)
        return _run_git(worktree, "rev-parse", "HEAD").strip()

    def _push_current_branch(self) -> tuple[bool, str]:
        try:
            branch = _run_git(self.project_root, "branch", "--show-current").strip()
            if not branch:
                return False, "no hay una rama activa"
            _run_git(self.project_root, "push", "origin", branch)
            return True, branch
        except Exception as exc:
            return False, _short_error(exc)

    def _cleanup_worktree(
        self,
        worktree: Optional[Path],
        branch: str,
        *,
        delete_branch: bool,
    ) -> None:
        if worktree is not None:
            try:
                _run_git(self.project_root, "worktree", "remove", "--force", str(worktree))
            except Exception:
                shutil.rmtree(worktree, ignore_errors=True)
        if branch and delete_branch:
            try:
                _run_git(self.project_root, "branch", "-D", branch)
            except Exception:
                pass

    def _codex_available(self, send_message: SendMessage, chat_id: int | str) -> bool:
        if self.quota_monitor.can_schedule_codex(refresh=True):
            return True
        reason = self.quota_monitor.pause_reason() or "cuota Codex no disponible"
        send_message(chat_id, f"Modo desarrollo en pausa: {reason}")
        return False

    def _state_path(self, chat_id: int | str) -> Path:
        return self.state_root / f"{_safe_id(str(chat_id))}.json"

    def _load_state(self, chat_id: int | str) -> dict[str, Any]:
        path = self._state_path(chat_id)
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except Exception:
            return {}

    def _save_state(self, chat_id: int | str, state: dict[str, Any]) -> None:
        path = self._state_path(chat_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(state, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
        temporary.replace(path)

    def _new_run_dir(self, kind: str) -> Path:
        path = self.runtime_root / "runs" / f"{int(time.time() * 1000)}-{kind}"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _register_task(self, chat_id: int | str, task: RunningTask) -> None:
        with self._task_lock:
            self._tasks[str(chat_id)] = task

    def _unregister_task(self, chat_id: int | str, task: RunningTask) -> None:
        with self._task_lock:
            if self._tasks.get(str(chat_id)) is task:
                self._tasks.pop(str(chat_id), None)

    def _has_running_task(self, chat_id: int | str) -> bool:
        with self._task_lock:
            return str(chat_id) in self._tasks


def normalize_command(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", (text or "").casefold())
    command = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    command = " ".join(command.strip().split()).strip(" .,!¡?¿")
    aliases = {
        "activar modo de desarrollo": "activar modo desarrollo",
        "activar el modo desarrollo": "activar modo desarrollo",
        "activar el modo de desarrollo": "activar modo desarrollo",
        "activar modo desarrollador": "activar modo desarrollo",
        "activar el modo desarrollador": "activar modo desarrollo",
        "desactivar modo de desarrollo": "desactivar modo desarrollo",
        "desactivar el modo desarrollo": "desactivar modo desarrollo",
        "desactivar el modo de desarrollo": "desactivar modo desarrollo",
        "desactivar modo desarrollador": "desactivar modo desarrollo",
        "desactivar el modo desarrollador": "desactivar modo desarrollo",
    }
    return aliases.get(command, command)


def _is_yes(command: str) -> bool:
    return command in {"si", "confirmo", "adelante", "vale", "ok", "continua", "continuar"}


def _is_no(command: str) -> bool:
    return command in {"no", "descartar", "rechazar", "cancela", "cancelar"}


def _format_proposal(proposal: dict[str, Any], version: int, seconds: float) -> str:
    lines = [
        f"Propuesta de desarrollo v{version}: {proposal.get('title', 'Cambio solicitado')}",
        "",
        str(proposal.get("understanding", "")).strip(),
    ]
    for title, key in (
        ("Cambios", "changes"),
        ("Archivos probables", "files"),
        ("Pruebas", "tests"),
        ("Riesgos", "risks"),
        ("Preguntas abiertas", "open_questions"),
    ):
        values = proposal.get(key)
        if isinstance(values, list) and values:
            lines.extend(["", f"{title}:"])
            lines.extend(f"- {value}" for value in values)
    lines.extend(
        [
            "",
            f"Propuesta: {_duration(seconds)}",
            "",
            "Responde `si` para implementar, `no` para descartar o escribe una correccion.",
        ]
    )
    return "\n".join(lines)


def _run_git(cwd: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return completed.stdout


def _find_codex() -> str:
    local = (
        Path(os.getenv("LOCALAPPDATA", ""))
        / "Programs"
        / "OpenAI"
        / "Codex"
        / "bin"
        / "codex.exe"
    )
    executable = str(local) if local.is_file() else shutil.which("codex")
    if not executable:
        raise RuntimeError("No se encontro Codex CLI.")
    return executable


def _terminate_process_tree(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    else:
        process.terminate()


def _safe_id(value: str) -> str:
    cleaned = "".join(
        character if character.isalnum() or character in "-_" else "-"
        for character in value
    )
    return cleaned.strip("-") or "chat"


def _last_line(text: str) -> str:
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    return lines[-1] if lines else ""


def _short_error(exc: Exception) -> str:
    return (_last_line(str(exc)) or exc.__class__.__name__)[:700]


def _duration(seconds: float) -> str:
    rounded = max(0, round(seconds))
    minutes, remainder = divmod(rounded, 60)
    return f"{minutes}m {remainder}s" if minutes else f"{remainder}s"


def _timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")
