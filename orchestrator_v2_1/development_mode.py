from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import threading
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .conversation_state import load_state, save_state
from .memory_store import DEFAULT_RUNTIME_ROOT


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEVELOPMENT_ROOT = DEFAULT_RUNTIME_ROOT / "development"
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
    "required": ["title", "understanding", "changes", "files", "tests", "risks", "open_questions"],
    "additionalProperties": False,
}

SendMessage = Callable[[int | str, str], None]
CompleteImplementation = Callable[[int | str, str, str, bool], None]


@dataclass
class RunningTask:
    process: subprocess.Popen[str] | None = None
    cancelled: bool = False


class DevelopmentModeController:
    def __init__(self, project_root: Path = PROJECT_ROOT) -> None:
        self.project_root = project_root.resolve()
        self.runtime_root = DEVELOPMENT_ROOT.resolve()
        self._tasks: dict[str, RunningTask] = {}
        self._lock = threading.Lock()
        self._publication_lock = threading.Lock()

    def is_active(self, chat_id: int | str) -> bool:
        return bool(self._development_state(chat_id).get("active", False))

    def activate(self, chat_id: int | str) -> None:
        state = load_state(str(chat_id), str(chat_id))
        state["development"] = {
            "active": True,
            "phase": "idle",
            "activated_at": now_timestamp(),
            "proposal_version": 0,
        }
        state.pop("pending_confirmation", None)
        save_state(str(chat_id), str(chat_id), state)

    def deactivate(self, chat_id: int | str) -> bool:
        cancelled = self.cancel_running_task(chat_id)
        state = load_state(str(chat_id), str(chat_id))
        state.pop("development", None)
        state.pop("pending_confirmation", None)
        save_state(str(chat_id), str(chat_id), state)
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
                "Describe el cambio que quieres hacer. Preparare una propuesta sin modificar el codigo.",
            )
            return True
        if command == "desactivar modo desarrollo":
            cancelled = self.deactivate(chat_id)
            suffix = " La tarea en curso se ha cancelado." if cancelled else ""
            send_message(chat_id, f"Modo desarrollo desactivado.{suffix}")
            return True
        if not self.is_active(chat_id):
            return False

        development = self._development_state(chat_id)
        phase = str(development.get("phase", "idle"))
        if phase in {"proposing", "implementing"} and not self._has_running_task(chat_id):
            phase = "awaiting_approval" if phase == "implementing" and development.get("proposal") else "idle"
            development = {**development, "phase": phase}
            self._set_development_state(chat_id, development)
        if phase in {"proposing", "implementing"}:
            send_message(
                chat_id,
                "Hay una tarea de desarrollo en curso. Puedes esperar o escribir "
                "'desactivar modo desarrollo' para cancelarla.",
            )
            return True
        if phase == "awaiting_approval":
            if is_yes(text):
                self._start_implementation(
                    chat_id,
                    send_message=send_message,
                    complete_implementation=complete_implementation,
                )
                return True
            if is_no(text):
                self._set_development_state(
                    chat_id,
                    {
                        **development,
                        "phase": "idle",
                        "pending_request": "",
                        "proposal": None,
                    },
                )
                send_message(chat_id, "Propuesta descartada. Puedes describir una nueva tarea.")
                return True
            self._start_proposal(chat_id, text, send_message=send_message, revision=True)
            return True

        self._start_proposal(chat_id, text, send_message=send_message, revision=False)
        return True

    def cancel_running_task(self, chat_id: int | str) -> bool:
        key = str(chat_id)
        with self._lock:
            task = self._tasks.get(key)
            if task is None:
                return False
            task.cancelled = True
            process = task.process
        if process is not None and process.poll() is None:
            terminate_process_tree(process)
        return True

    def _start_proposal(
        self,
        chat_id: int | str,
        text: str,
        *,
        send_message: SendMessage,
        revision: bool,
    ) -> None:
        development = self._development_state(chat_id)
        original_request = str(development.get("pending_request", "")).strip() if revision else text.strip()
        previous_proposal = development.get("proposal") if revision else None
        version = int(development.get("proposal_version", 0)) + 1
        updated = {
            **development,
            "active": True,
            "phase": "proposing",
            "pending_request": original_request,
            "proposal_version": version,
            "last_feedback": text.strip() if revision else "",
        }
        self._set_development_state(chat_id, updated)
        task = RunningTask()
        self._register_task(chat_id, task)
        send_message(
            chat_id,
            "Revisando el proyecto y preparando "
            + ("una nueva version de la propuesta." if revision else "la propuesta."),
        )
        thread = threading.Thread(
            target=self._proposal_worker,
            args=(chat_id, original_request, text.strip() if revision else "", previous_proposal, version, task, send_message),
            name=f"development-proposal-{chat_id}",
            daemon=True,
        )
        thread.start()

    def _proposal_worker(
        self,
        chat_id: int | str,
        request_text: str,
        feedback: str,
        previous_proposal: Any,
        version: int,
        task: RunningTask,
        send_message: SendMessage,
    ) -> None:
        started = time.monotonic()
        try:
            proposal = self._run_proposal_codex(request_text, feedback, previous_proposal, task)
            if task.cancelled or not self.is_active(chat_id):
                return
            elapsed_seconds = time.monotonic() - started
            development = self._development_state(chat_id)
            self._set_development_state(
                chat_id,
                {
                    **development,
                    "phase": "awaiting_approval",
                    "proposal": proposal,
                    "proposal_version": version,
                    "last_proposal_seconds": round(elapsed_seconds, 3),
                },
            )
            send_message(chat_id, format_proposal(proposal, version, elapsed_seconds))
        except Exception as exc:
            logging.exception("Development proposal failed")
            if not task.cancelled and self.is_active(chat_id):
                elapsed_seconds = time.monotonic() - started
                development = self._development_state(chat_id)
                self._set_development_state(
                    chat_id,
                    {
                        **development,
                        "phase": "idle",
                        "last_proposal_seconds": round(elapsed_seconds, 3),
                    },
                )
                send_message(
                    chat_id,
                    f"No he podido preparar la propuesta: {short_error(exc)}\n\n"
                    f"Propuesta hasta el fallo: {format_duration(elapsed_seconds)}",
                )
        finally:
            self._unregister_task(chat_id, task)

    def _start_implementation(
        self,
        chat_id: int | str,
        *,
        send_message: SendMessage,
        complete_implementation: CompleteImplementation,
    ) -> None:
        development = self._development_state(chat_id)
        request_text = str(development.get("pending_request", "")).strip()
        proposal = development.get("proposal")
        if not request_text or not isinstance(proposal, dict):
            self._set_development_state(chat_id, {**development, "phase": "idle"})
            send_message(chat_id, "La propuesta pendiente no es valida. Describe de nuevo el cambio.")
            return
        self._set_development_state(chat_id, {**development, "phase": "implementing"})
        task = RunningTask()
        self._register_task(chat_id, task)
        send_message(
            chat_id,
            "Propuesta aprobada. Codex esta implementando el cambio en un entorno Git aislado.",
        )
        thread = threading.Thread(
            target=self._implementation_worker,
            args=(chat_id, request_text, proposal, task, send_message, complete_implementation),
            name=f"development-implementation-{chat_id}",
            daemon=True,
        )
        thread.start()

    def _implementation_worker(
        self,
        chat_id: int | str,
        request_text: str,
        proposal: dict[str, Any],
        task: RunningTask,
        send_message: SendMessage,
        complete_implementation: CompleteImplementation,
    ) -> None:
        worktree: Path | None = None
        branch = ""
        commit_sha = ""
        published = False
        started = time.monotonic()
        try:
            worktree, branch = self._create_worktree(chat_id)
            final_message = self._run_implementation_codex(worktree, request_text, proposal, task)
            if task.cancelled or not self.is_active(chat_id):
                return
            commit_sha = self._commit_worktree(worktree, proposal)
            if task.cancelled or not self.is_active(chat_id):
                return
            with self._publication_lock:
                if task.cancelled or not self.is_active(chat_id):
                    return
                commit_sha = self._rebase_onto_current_head(worktree)
                self._apply_commit(commit_sha)
                pushed, push_detail = self._push_current_branch()
                published = True
            report = build_implementation_report(final_message, commit_sha, pushed, push_detail)
            elapsed_seconds = time.monotonic() - started
            report = f"{report}\n\nImplementacion completa: {format_duration(elapsed_seconds)}"
            development = self._development_state(chat_id)
            self._set_development_state(
                chat_id,
                {
                    **development,
                    "phase": "idle",
                    "pending_request": "",
                    "proposal": None,
                    "last_commit": commit_sha,
                    "last_completed_at": now_timestamp(),
                    "last_implementation_seconds": round(elapsed_seconds, 3),
                },
            )
            complete_implementation(chat_id, request_text, report, True)
        except Exception as exc:
            logging.exception("Development implementation failed")
            elapsed_seconds = time.monotonic() - started
            error_detail = readable_error(exc)
            self._record_failure(
                chat_id,
                request_text=request_text,
                branch=branch,
                commit_sha=commit_sha,
                error=error_detail,
            )
            if not task.cancelled and self.is_active(chat_id):
                development = self._development_state(chat_id)
                self._set_development_state(
                    chat_id,
                    {
                        **development,
                        "phase": "awaiting_approval",
                        "last_error": error_detail,
                        "recovery_branch": branch if commit_sha else "",
                        "recovery_commit": commit_sha,
                        "last_implementation_seconds": round(elapsed_seconds, 3),
                    },
                )
                recovery_note = (
                    f"El trabajo se conserva en `{branch}` (`{commit_sha[:8]}`).\n\n"
                    if commit_sha
                    else ""
                )
                failure_message = (
                    "La implementacion no se ha incorporado al proyecto.\n\n"
                    f"Motivo: {error_detail}\n\n"
                    f"{recovery_note}"
                    f"Implementacion hasta el fallo: {format_duration(elapsed_seconds)}\n\n"
                    "La propuesta sigue pendiente: puedes corregirla, responder 'si' para reintentar "
                    "o 'no' para descartarla."
                )
                complete_implementation(
                    chat_id,
                    request_text,
                    failure_message,
                    False,
                )
        finally:
            self._cleanup_worktree(worktree, branch, delete_branch=published or not commit_sha)
            self._unregister_task(chat_id, task)

    def _run_proposal_codex(
        self,
        request_text: str,
        feedback: str,
        previous_proposal: Any,
        task: RunningTask,
    ) -> dict[str, Any]:
        run_dir = self._new_run_dir("proposal")
        schema_path = run_dir / "proposal-schema.json"
        output_path = run_dir / "proposal.json"
        schema_path.write_text(json.dumps(PROPOSAL_SCHEMA, indent=2), encoding="utf-8")
        prompt = build_proposal_prompt(request_text, feedback, previous_proposal)
        worktree: Path | None = None
        branch = ""
        try:
            worktree, branch = self._create_worktree("proposal")
            command = self._codex_command(
                sandbox="workspace-write",
                cwd=worktree,
                prompt=prompt,
                output_path=output_path,
                schema_path=schema_path,
            )
            self._run_codex_process(command, task, timeout_seconds=900)
            return json.loads(output_path.read_text(encoding="utf-8"))
        finally:
            self._cleanup_worktree(worktree, branch)

    def _run_implementation_codex(
        self,
        worktree: Path,
        request_text: str,
        proposal: dict[str, Any],
        task: RunningTask,
    ) -> str:
        run_dir = self._new_run_dir("implementation")
        output_path = run_dir / "final.md"
        prompt = build_implementation_prompt(request_text, proposal)
        command = self._codex_command(
            sandbox="workspace-write",
            cwd=worktree,
            prompt=prompt,
            output_path=output_path,
        )
        self._run_codex_process(command, task, timeout_seconds=3600)
        if not output_path.exists():
            raise RuntimeError("Codex no devolvio un resumen final.")
        return output_path.read_text(encoding="utf-8", errors="replace").strip()

    def _codex_command(
        self,
        *,
        sandbox: str,
        cwd: Path,
        prompt: str,
        output_path: Path,
        schema_path: Path | None = None,
    ) -> list[str]:
        command = [
            find_codex_executable(),
            "exec",
            "--ephemeral",
            "--sandbox",
            sandbox,
            "-c",
            'approval_policy="never"',
            "-c",
            'windows.sandbox="unelevated"',
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

    def _run_codex_process(
        self,
        command: list[str],
        task: RunningTask,
        *,
        timeout_seconds: int,
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
        with self._lock:
            task.process = process
        try:
            _, stderr = process.communicate(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            terminate_process_tree(process)
            process.communicate()
            raise TimeoutError("Codex supero el tiempo maximo de ejecucion.")
        finally:
            with self._lock:
                task.process = None
        if task.cancelled:
            raise RuntimeError("Tarea cancelada.")
        if process.returncode != 0:
            raise RuntimeError(last_nonempty_line(stderr) or f"Codex termino con codigo {process.returncode}.")

    def _create_worktree(self, chat_id: int | str) -> tuple[Path, str]:
        stamp = f"{int(time.time())}-{os.getpid()}"
        branch = f"codex/telegram-dev-{safe_identifier(str(chat_id))}-{stamp}"
        worktree = self.runtime_root / "worktrees" / safe_identifier(str(chat_id)) / stamp
        worktree.parent.mkdir(parents=True, exist_ok=True)
        run_git(self.project_root, "worktree", "add", "-b", branch, str(worktree), "HEAD")
        return worktree, branch

    def _commit_worktree(self, worktree: Path, proposal: dict[str, Any]) -> str:
        status = run_git(worktree, "status", "--porcelain").strip()
        if not status:
            raise RuntimeError("Codex termino sin producir cambios en el codigo.")
        run_git(worktree, "add", "--all")
        title = " ".join(str(proposal.get("title", "Telegram development change")).split())
        message = f"feat: {title[:65]}"
        run_git(worktree, "commit", "-m", message)
        return run_git(worktree, "rev-parse", "HEAD").strip()

    def _rebase_onto_current_head(self, worktree: Path) -> str:
        current_head = run_git(self.project_root, "rev-parse", "HEAD").strip()
        worktree_parent = run_git(worktree, "rev-parse", "HEAD^").strip()
        if worktree_parent == current_head:
            return run_git(worktree, "rev-parse", "HEAD").strip()
        try:
            run_git(worktree, "rebase", current_head)
        except Exception:
            try:
                run_git(worktree, "rebase", "--abort")
            except Exception:
                logging.exception("Could not abort failed development rebase")
            raise
        return run_git(worktree, "rev-parse", "HEAD").strip()

    def _apply_commit(self, commit_sha: str) -> None:
        try:
            run_git(self.project_root, "cherry-pick", commit_sha)
        except Exception:
            try:
                run_git(self.project_root, "cherry-pick", "--abort")
            except Exception:
                logging.exception("Could not abort failed development cherry-pick")
            raise

    def _push_current_branch(self) -> tuple[bool, str]:
        try:
            branch = run_git(self.project_root, "branch", "--show-current").strip()
            if not branch:
                return False, "No hay una rama activa; el commit quedo aplicado solo en local."
            run_git(self.project_root, "push", "origin", branch)
            return True, branch
        except Exception as exc:
            return False, short_error(exc)

    def _cleanup_worktree(
        self,
        worktree: Path | None,
        branch: str,
        *,
        delete_branch: bool = True,
    ) -> None:
        if worktree is not None:
            try:
                run_git(self.project_root, "worktree", "remove", "--force", str(worktree))
            except Exception:
                logging.exception("Could not remove development worktree %s", worktree)
                shutil.rmtree(worktree, ignore_errors=True)
        if branch and delete_branch:
            try:
                run_git(self.project_root, "branch", "-D", branch)
            except Exception:
                logging.exception("Could not remove development branch %s", branch)

    def _record_failure(
        self,
        chat_id: int | str,
        *,
        request_text: str,
        branch: str,
        commit_sha: str,
        error: str,
    ) -> None:
        path = self.runtime_root / "failures.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        entry = (
            f"\n## {now_timestamp()} - chat {chat_id}\n\n"
            f"- Request: {request_text}\n"
            f"- Branch: {branch or '(none)'}\n"
            f"- Commit: {commit_sha or '(none)'}\n"
            f"- Error: {error}\n"
        )
        with path.open("a", encoding="utf-8") as handle:
            handle.write(entry)

    def _new_run_dir(self, kind: str) -> Path:
        path = self.runtime_root / "runs" / f"{int(time.time() * 1000)}-{kind}"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _development_state(self, chat_id: int | str) -> dict[str, Any]:
        state = load_state(str(chat_id), str(chat_id))
        development = state.get("development")
        return development if isinstance(development, dict) else {}

    def _set_development_state(self, chat_id: int | str, development: dict[str, Any]) -> None:
        state = load_state(str(chat_id), str(chat_id))
        state["development"] = development
        save_state(str(chat_id), str(chat_id), state)

    def _register_task(self, chat_id: int | str, task: RunningTask) -> None:
        with self._lock:
            self._tasks[str(chat_id)] = task

    def _unregister_task(self, chat_id: int | str, task: RunningTask) -> None:
        with self._lock:
            if self._tasks.get(str(chat_id)) is task:
                self._tasks.pop(str(chat_id), None)

    def _has_running_task(self, chat_id: int | str) -> bool:
        with self._lock:
            return str(chat_id) in self._tasks


def build_proposal_prompt(request_text: str, feedback: str, previous_proposal: Any) -> str:
    revision_context = ""
    if feedback:
        revision_context = (
            "\nThe user is revising an earlier proposal.\n"
            f"Previous proposal:\n{json.dumps(previous_proposal, ensure_ascii=False, indent=2)}\n"
            f"User feedback:\n{feedback}\n"
        )
    return f"""
You are the planning stage of Inspector's Telegram development mode.
Inspect the repository at the current working directory and prepare a concrete implementation proposal.
Do not edit files, do not create commits, and do not execute the requested change.

User request:
{request_text}
{revision_context}

Return only the JSON object required by the supplied schema.
Use Spanish for every user-facing field.
Keep the proposal concise but specific enough to approve.
List likely files, verification commands, material risks, and only genuinely blocking open questions.
Respect existing architecture, preserve unrelated dirty changes, keep Codex Desktop isolated, and do not migrate the multibot laboratory.
""".strip()


def build_implementation_prompt(request_text: str, proposal: dict[str, Any]) -> str:
    return f"""
Implement the approved Telegram development request in this isolated Git worktree.

Original request:
{request_text}

Approved proposal:
{json.dumps(proposal, ensure_ascii=False, indent=2)}

Requirements:
- Work autonomously until the approved change is complete.
- Inspect the repository before editing and preserve its established architecture.
- Make only changes required by the approved proposal.
- Do not access or expose secrets.
- Do not commit, push, create branches, or manipulate worktrees; the parent controller handles Git publication.
- Update the relevant human-readable documentation and PROJECT_JOURNEY.md.
- Run focused tests and any broader tests justified by the change.
- Never import the legacy visual operator outside orchestrator_v2_1/desktop_adapter.py.
- Leave the multibot laboratory untouched.
- Finish with a concise Spanish report covering files changed, behavior, tests, and any residual limitation.
""".strip()


def format_proposal(proposal: dict[str, Any], version: int, elapsed_seconds: float = 0) -> str:
    lines = [
        f"Propuesta de desarrollo v{version}: {proposal.get('title', 'Cambio solicitado')}",
        "",
        str(proposal.get("understanding", "")).strip(),
    ]
    append_section(lines, "Cambios", proposal.get("changes"))
    append_section(lines, "Archivos probables", proposal.get("files"))
    append_section(lines, "Pruebas", proposal.get("tests"))
    append_section(lines, "Riesgos", proposal.get("risks"))
    append_section(lines, "Preguntas abiertas", proposal.get("open_questions"))
    lines.extend(
        [
            "",
            f"Propuesta: {format_duration(elapsed_seconds)}",
            "",
            "Responde:",
            "- `si` para implementar.",
            "- `no` para descartar.",
            "- Escribe cualquier correccion para generar otra version.",
            "- `desactivar modo desarrollo` para volver al modo normal.",
        ]
    )
    return "\n".join(lines).strip()


def format_duration(seconds: float) -> str:
    rounded = max(0, round(seconds))
    minutes, remaining_seconds = divmod(rounded, 60)
    if minutes:
        return f"{minutes}m {remaining_seconds}s"
    return f"{remaining_seconds}s"


def append_section(lines: list[str], title: str, values: Any) -> None:
    if not isinstance(values, list) or not values:
        return
    lines.extend(["", f"{title}:"])
    lines.extend(f"- {str(value).strip()}" for value in values if str(value).strip())


def build_implementation_report(
    final_message: str,
    commit_sha: str,
    pushed: bool,
    push_detail: str,
) -> str:
    publication = (
        f"Commit `{commit_sha[:8]}` creado y publicado en `{push_detail}`."
        if pushed
        else f"Commit `{commit_sha[:8]}` creado en local. Push pendiente: {push_detail}"
    )
    return f"{final_message.strip()}\n\n{publication}".strip()


def normalize_command(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return " ".join(without_accents.strip().split()).strip(" .,!¡?¿")


def is_yes(text: str) -> bool:
    return normalize_command(text) in {"si", "confirmo", "adelante", "vale", "ok", "continua", "continuar"}


def is_no(text: str) -> bool:
    return normalize_command(text) in {"no", "descartar", "rechazar", "cancela", "cancelar"}


def find_codex_executable() -> str:
    local = Path(os.getenv("LOCALAPPDATA", "")) / "Programs" / "OpenAI" / "Codex" / "bin" / "codex.exe"
    if local.is_file():
        return str(local)
    executable = shutil.which("codex") or shutil.which("codex.exe")
    if not executable:
        raise RuntimeError("No se encontro Codex CLI.")
    return executable


def run_git(cwd: Path, *args: str) -> str:
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
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(detail or f"git {' '.join(args)} fallo.")
    return completed.stdout


def terminate_process_tree(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return
    process.terminate()


def safe_identifier(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in "-_" else "-" for char in value)
    return cleaned.strip("-") or "chat"


def last_nonempty_line(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def short_error(exc: Exception) -> str:
    return str(exc).strip().splitlines()[-1][:500] or exc.__class__.__name__


def readable_error(exc: Exception) -> str:
    lines = [line.strip() for line in str(exc).splitlines() if line.strip()]
    if not lines:
        return exc.__class__.__name__
    relevant = [
        line
        for line in lines
        if any(
            marker in line.casefold()
            for marker in ("error", "fatal", "conflict", "would be overwritten", "could not apply")
        )
    ]
    selected = relevant[-4:] if relevant else lines[-4:]
    return " | ".join(selected)[:1200]


def now_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")
