from __future__ import annotations

import hashlib
import json
import re
import sys
import threading
import time
import traceback
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from alarms import AlarmStore, confirmation_text, format_alarm, parse_alarm_request
from codex_runner import CodexRunner
from codex_dirs import CodexDirStore
from config import ROOT, Settings, load_settings
from intent import (
    ACTION_ADD_CODEX_DIR,
    ACTION_CANCEL_ALARM,
    ACTION_CODEX,
    ACTION_CREATE_ALARM,
    ACTION_CURRENT_THREAD,
    ACTION_HELP,
    ACTION_LIST_ALARMS,
    ACTION_LIST_CODEX_DIRS,
    ACTION_LIST_MEMORIES,
    ACTION_LIST_THREADS,
    ACTION_NEW_THREAD,
    ACTION_REMEMBER,
    ACTION_REMOVE_CODEX_DIR,
    ACTION_STATUS,
    ACTION_STATUS_DETAIL,
    ACTION_SWITCH_THREAD,
    ACTION_LIST_PENDING,
    ACTION_RUN_NEXT_PENDING,
    ACTION_CLEAR_PENDING,
    ACTION_CANCEL_CURRENT_TASK,
    ACTION_CODEX_DESKTOP,
    ACTION_DIRECT_LOCAL,
    Intent,
    IntentInterpreter,
    ACTION_QUERY_MEMORY,
)
from memories import RememberStore
from memory import MemoryLog
from pending_tasks import PendingTask, PendingTaskStore
from python_repair import repair_python_syntax_if_requested
from speech_io import SpeechIO
from thread_store import ThreadRecord, ThreadStore
from telegram_api import TelegramApi
from voice_state import VoiceStateStore
from benchmarks.token_accounting import record_usage
from orchestrator_v2.desktop_codex_operator import capture_desktop_screenshot, run_desktop_codex_operator


RESTART_EXIT_CODE = 75
VOICE_LONG_TEXT_CHARS = 900
VOICE_SUMMARY_MAX_CHARS = 650


AFFIRMATIVE_CONFIRMATIONS = {"si", "sí", "ok", "vale", "adelante", "confirma", "confirmo", "ejecuta", "dale"}
NEGATIVE_CONFIRMATIONS = {"no", "cancela", "cancelar", "para", "espera", "deten", "detén"}


class Orchestrator:
    def __init__(self) -> None:
        self.settings = load_settings()
        self.memory = MemoryLog(self.settings.memory_file)
        self.telegram = TelegramApi(self.settings.telegram_bot_token, self.settings.message_chunk_size)
        self.codex = CodexRunner(self.settings)
        self.codex_dirs = CodexDirStore(self.settings.codex_dirs_file)
        self.alarms = AlarmStore(self.settings.alarms_file)
        self.remembers = RememberStore(self.settings.memories_file)
        self.threads = ThreadStore(self.settings.threads_file, self.settings.codex_workdir, self.settings.codex_extra_dirs)
        self.pending = PendingTaskStore(self.settings.pending_tasks_file)
        self.interpreter = IntentInterpreter(self.settings)
        self.voice_store = VoiceStateStore(self.settings.voice_settings_file, self.settings.google_api_key, self.settings.groq_api_key)
        self.voice_state = self.voice_store.load()
        self.speech = SpeechIO(self.settings.voice_runtime_dir)
        self.offset: int | None = None
        self._busy = threading.Lock()
        self._current_task: dict[str, str] | None = None
        self._pending_codex_confirmation: dict[str, Any] | None = None
        self._stop = threading.Event()
        self._code_fingerprint = self._fingerprint_code()
        self._next_code_check = 0.0

    def run(self) -> int:
        if not self.settings.ready:
            print("Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_ALLOWED_USER_ID/ORCH_TELEGRAM_ALLOWED_USER_ID.")
            return 2

        self.memory.write("orchestrator_start", self._status_text(), "system", thread=self.threads.active_name())
        self._drain_pending_updates()
        self.telegram.send_message(self.settings.telegram_allowed_user_id, "Orquestador Codex listo. Ya puedes hablarme en lenguaje natural.")
        threading.Thread(target=self._alarm_loop, daemon=True).start()

        while not self._stop.is_set():
            if not self._busy.locked() and self._code_changed():
                self.memory.write("hot_reload_requested", "Cambio detectado en codigo Python. Reiniciando.", "system", thread=self.threads.active_name())
                self.telegram.send_message(self.settings.telegram_allowed_user_id, "Detecte cambios en el orquestador. Reinicio en caliente.")
                return RESTART_EXIT_CODE

            try:
                updates = self.telegram.get_updates(self.offset, self.settings.telegram_poll_timeout)
                for update in updates:
                    self.offset = int(update["update_id"]) + 1
                    self._handle_update(update)
            except KeyboardInterrupt:
                self.memory.write("orchestrator_stop", "Detenido por teclado.", "system", thread=self.threads.active_name())
                self._stop.set()
                return 0
            except Exception as exc:
                detail = f"{exc}\n{traceback.format_exc()}"
                self.memory.write("poll_error", detail, "system", thread=self.threads.active_name())
                time.sleep(5)
        self.memory.write("orchestrator_stop", "Detenido desde interfaz grafica.", "system", thread=self.threads.active_name())
        return 0

    def stop(self) -> None:
        self._stop.set()
        if self.codex.is_running():
            self.codex.cancel()

    def inject_text(self, text: str, source: str = "gui") -> None:
        clean_text = text.strip()
        if not clean_text:
            return
        chat_id = self.settings.telegram_allowed_user_id
        update = {
            "update_id": 0,
            "message": {
                "message_id": 0,
                "text": clean_text,
                "chat": {"id": chat_id},
                "from": {"id": chat_id},
            },
        }
        self.memory.write("gui_inject", clean_text, source, thread=self.threads.active_name())
        self._handle_update(update)

    def _handle_update(self, update: dict[str, Any]) -> None:
        message = update.get("message") or {}
        chat = message.get("chat") or {}
        user = message.get("from") or {}
        chat_id = int(chat.get("id") or 0)
        user_id = int(user.get("id") or 0)
        text = (message.get("text") or message.get("caption") or "").strip()
        source = f"telegram user_id={user_id} chat_id={chat_id}"

        # Download document if any
        document = message.get("document")
        if isinstance(document, dict):
            file_id = document.get("file_id")
            file_name = document.get("file_name") or f"file_{file_id}"
            if file_id:
                active_thread_record = self.threads.active()
                inbox_dir = Path(self.settings.codex_workdir) / "inbox"
                inbox_dir.mkdir(parents=True, exist_ok=True)
                inbox_path = inbox_dir / file_name
                
                dest_dir = Path(active_thread_record.workdir)
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_path = dest_dir / file_name
                try:
                    self.telegram.download_file(file_id, inbox_path)
                    import shutil
                    shutil.copy(inbox_path, dest_path)
                    self.memory.write(
                        "telegram_document_received",
                        f"name={file_name} size={document.get('file_size')} inbox_path={inbox_path} dest_path={dest_path}",
                        source,
                        thread=active_thread_record.name
                    )
                    if not self.settings.lab_mode:
                        self._reply(
                            chat_id,
                            f"Archivo `{file_name}` aceptado y guardado en bandeja de entrada e hilo `{active_thread_record.name}`.",
                            thread=active_thread_record.name
                        )
                except Exception as exc:
                    self.memory.write(
                        "telegram_document_error",
                        f"file={file_name} err={exc}",
                        source,
                        thread=active_thread_record.name
                    )
                    self._reply(
                        chat_id,
                        f"Error al descargar el archivo {file_name}: {exc}",
                        thread=active_thread_record.name
                    )

        if not text and self._telegram_audio_file_id(message):
            text = self._transcribe_telegram_audio(message, source)

        if not text:
            return

        active_thread = self.threads.active_name()
        self.memory.write("telegram_in", text, source, thread=active_thread)

        if user_id != self.settings.telegram_allowed_user_id and chat_id != self.settings.telegram_allowed_user_id:
            self.memory.write("telegram_rejected", text, source, thread=active_thread)
            return

        lower = text.lower()
        if lower == "/reload":
            self._reload(chat_id)
            return
        if lower == "/restart":
            self._reply(chat_id, "Reinicio solicitado. El supervisor lo levantara de nuevo.")
            self.memory.write("restart_requested", text, source, thread=active_thread)
            raise SystemExit(RESTART_EXIT_CODE)

        if self._handle_codex_confirmation_reply(chat_id, text, source):
            return

        voice_response = self._handle_voice_command(text)
        if voice_response is not None:
            self._reply(chat_id, voice_response, thread="voz")
            return

        intent = self.interpreter.interpret(text)
        self.memory.write(
            "intent",
            f"action={intent.action} source={intent.source} confidence={intent.confidence}\nargs={intent.args}",
            source,
            thread=active_thread,
        )
        self._dispatch_intent(chat_id, intent, source)

    def _dispatch_intent(self, chat_id: int, intent: Intent, source: str) -> None:
        if intent.action == ACTION_HELP:
            self._reply(chat_id, self._help_text())
            return
        if intent.action == ACTION_STATUS:
            self._reply(chat_id, self._status_text())
            return
        if intent.action == ACTION_STATUS_DETAIL:
            self._reply(chat_id, self._activity_text())
            return
        if intent.action == ACTION_LIST_PENDING:
            self._reply(chat_id, self._pending_text())
            return
        if intent.action == ACTION_CLEAR_PENDING:
            count = self.pending.clear()
            self.memory.write("pending_cleared", f"count={count}", source, thread=self.threads.active_name())
            self._reply(chat_id, f"He borrado {count} tarea(s) pendiente(s).")
            return
        if intent.action == ACTION_RUN_NEXT_PENDING:
            if self.settings.bypass_confirmation:
                self._start_next_pending(chat_id)
            else:
                self._request_next_pending_confirmation(chat_id, source)
            return
        if intent.action == ACTION_CANCEL_CURRENT_TASK:
            self._cancel_current_task(chat_id, source)
            return
        if intent.action == ACTION_LIST_THREADS:
            self._reply(chat_id, self._threads_text())
            return
        if intent.action == ACTION_CURRENT_THREAD:
            self._reply(chat_id, self._current_thread_text())
            return
        if intent.action == ACTION_NEW_THREAD:
            name = str(intent.args.get("name", "")).strip()
            record = self.threads.create(name or "nuevo_hilo")
            self.memory.write("thread_created", self._thread_line(record), source, thread=record.name)
            self._reply(chat_id, f"Hilo creado y activado:\n{self._thread_line(record)}", thread=record.name)
            return
        if intent.action == ACTION_SWITCH_THREAD:
            name = str(intent.args.get("name", "")).strip()
            record = self.threads.set_active(name or "desarrollo")
            self.memory.write("thread_switched", self._thread_line(record), source, thread=record.name)
            self._reply(chat_id, f"Hilo activo:\n{self._thread_line(record)}", thread=record.name)
            return
        if intent.action == ACTION_LIST_ALARMS:
            self._reply(chat_id, self._alarms_text(chat_id))
            return
        if intent.action == ACTION_LIST_MEMORIES:
            self._reply(chat_id, self._memories_text())
            return
        if intent.action == ACTION_LIST_CODEX_DIRS:
            self._reply(chat_id, self._codex_dirs_text())
            return
        if intent.action == ACTION_ADD_CODEX_DIR:
            raw_path = str(intent.args.get("path", "")).strip()
            ok, message, path = self.codex_dirs.add(raw_path)
            self._refresh_runtime_config()
            self.memory.write("codex_dir_add", f"ok={ok} path={path}\n{message}", source, thread=self.threads.active_name())
            self._reply(chat_id, f"{message}\n\n{path}" if path else message)
            return
        if intent.action == ACTION_REMOVE_CODEX_DIR:
            raw_path = str(intent.args.get("path", "")).strip()
            removed = self.codex_dirs.remove(raw_path)
            self._refresh_runtime_config()
            self.memory.write("codex_dir_remove", f"removed={removed} path={raw_path}", source, thread=self.threads.active_name())
            self._reply(chat_id, "Carpeta quitada de Codex." if removed else "No encontre esa carpeta en la lista.")
            return
        if intent.action == ACTION_CANCEL_ALARM:
            alarm_id = str(intent.args.get("alarm_id", "")).strip()
            if alarm_id and self.alarms.cancel(chat_id, alarm_id):
                self.memory.write("alarm_cancelled", alarm_id, source, thread="alarmas")
                self._reply(chat_id, f"Alarma {alarm_id} cancelada.", thread="alarmas")
            else:
                self._reply(chat_id, f"No encuentro una alarma activa con id {alarm_id or '(vacio)'}.", thread="alarmas")
            return
        if intent.action == ACTION_CREATE_ALARM:
            alarm_text = str(intent.args.get("text", "")).strip()
            parsed_alarm = parse_alarm_request(alarm_text)
            if parsed_alarm is not None:
                alarm = self.alarms.add(chat_id, parsed_alarm)
                self.memory.write("alarm_created", format_alarm(alarm), source, thread="alarmas")
                self._reply(chat_id, confirmation_text(alarm), thread="alarmas")
                return
            self.memory.write("alarm_parse_failed", alarm_text, source, thread="alarmas")
            self._reply(chat_id, "Entendi que quieres una alarma, pero no pude convertir la fecha. Prueba: avisame dentro de 15 minutos de poner la television.", thread="alarmas")
            return
        if intent.action == ACTION_REMEMBER:
            remember_text = str(intent.args.get("text", "")).strip()
            if not remember_text:
                self._reply(chat_id, "Entendi que quieres guardar un recuerdo, pero no veo que contenido guardar.", thread="recuerdos")
                return
            self.remembers.add(remember_text)
            self.memory.write("remember_created", remember_text, source, thread="recuerdos")
            self._reply(chat_id, "Guardado en memoria.", thread="recuerdos")
            return
        if intent.action == ACTION_QUERY_MEMORY:
            query = str(intent.args.get("query", "")).strip()
            self._reply(chat_id, self._memory_query_text(query), thread="recuerdos")
            return
        if intent.action == ACTION_DIRECT_LOCAL:
            self._reply(chat_id, self._direct_local_text(intent.args), thread=self.threads.active_name())
            return

        instruction = str(intent.args.get("instruction", "")).strip()
        if intent.action == ACTION_CODEX_DESKTOP and instruction:
            thread_record = self.threads.choose_for_codex(instruction, str(intent.args.get("thread_name", "")).strip() or None)
            self.threads.set_active(thread_record.name)
            if self.settings.bypass_confirmation:
                self._start_confirmed_codex_desktop(chat_id, instruction, source, thread_record)
            else:
                self._request_codex_desktop_confirmation(chat_id, instruction, source, thread_record)
            return

        if intent.action != ACTION_CODEX or not instruction:
            self._reply(chat_id, "Comando no reconocido. Usa Cd <instruccion> para Codex Desktop, /codex <instruccion> para Codex CLI, pideme una alarma o dime 'recuerda que ...'.")
            return

        thread_record = self.threads.choose_for_codex(instruction, str(intent.args.get("thread_name", "")).strip() or None)
        self.threads.set_active(thread_record.name)
        if self.settings.bypass_confirmation:
            self._start_confirmed_codex(chat_id, instruction, source, thread_record, None)
        else:
            self._request_codex_confirmation(chat_id, instruction, source, thread_record, None)
        return

    def _start_confirmed_codex(self, chat_id: int, instruction: str, source: str, thread_record: ThreadRecord, pending_task: PendingTask | None) -> None:
        if not self._busy.acquire(blocking=False):
            task = self.pending.add(chat_id, instruction, thread_record.name, source)
            self.memory.write("codex_queued_busy", f"id={task.id}\n{instruction}", source, thread=thread_record.name)
            self._reply(
                chat_id,
                f"Codex esta ocupado. He dejado esta tarea pendiente con id {task.id} en el hilo `{thread_record.name}`.\nCuando termine te aviso y puedes decirme: sigue con lo pendiente.",
                thread=thread_record.name,
            )
            return

        worker = threading.Thread(
            target=self._run_codex_and_reply,
            args=(chat_id, instruction, source, thread_record, pending_task),
            daemon=True,
        )
        worker.start()

    def _start_confirmed_codex_desktop(self, chat_id: int, instruction: str, source: str, thread_record: ThreadRecord) -> None:
        if not self._busy.acquire(blocking=False):
            self.memory.write("codex_desktop_busy", instruction, source, thread=thread_record.name)
            self._reply(
                chat_id,
                "Codex esta ocupado ahora mismo. Si quieres, vuelve a mandar `Cd ...` cuando quede libre o lo dejamos para la cola de pendientes en el siguiente ajuste.",
                thread=thread_record.name,
            )
            return

        worker = threading.Thread(
            target=self._run_codex_desktop_and_reply,
            args=(chat_id, instruction, source, thread_record),
            daemon=True,
        )
        worker.start()

    def _request_codex_confirmation(
        self,
        chat_id: int,
        instruction: str,
        source: str,
        thread_record: ThreadRecord,
        pending_task: PendingTask | None,
    ) -> None:
        command_line = self.codex.preview_command(instruction, thread_id=thread_record.codex_thread_id)
        self._pending_codex_confirmation = {
            "mode": "codex",
            "chat_id": chat_id,
            "instruction": instruction,
            "source": source,
            "thread_name": thread_record.name,
            "pending_task": pending_task,
            "command_line": command_line,
        }
        self.memory.write("codex_confirmation_requested", command_line, source, thread=thread_record.name)
        self._reply(chat_id, self._codex_confirmation_text(instruction, thread_record, command_line), thread=thread_record.name)

    def _request_codex_desktop_confirmation(
        self,
        chat_id: int,
        instruction: str,
        source: str,
        thread_record: ThreadRecord,
    ) -> None:
        self._pending_codex_confirmation = {
            "mode": "codex_desktop",
            "chat_id": chat_id,
            "instruction": instruction,
            "source": source,
            "thread_name": thread_record.name,
        }
        self.memory.write("codex_desktop_confirmation_requested", instruction, source, thread=thread_record.name)
        self._reply(chat_id, self._codex_desktop_confirmation_text(instruction, thread_record), thread=thread_record.name)

    def _request_next_pending_confirmation(self, chat_id: int, source: str) -> None:
        if self._busy.locked():
            self._reply(chat_id, "Codex sigue ocupado. La tarea pendiente se mantiene en cola.")
            return
        tasks = self.pending.list()
        task = tasks[0] if tasks else None
        if task is None:
            self._reply(chat_id, "No hay tareas pendientes.")
            return
        thread_record = self.threads.get(task.thread_name)
        command_line = self.codex.preview_command(task.instruction, thread_id=thread_record.codex_thread_id)
        self._pending_codex_confirmation = {
            "mode": "next_pending",
            "chat_id": task.chat_id,
            "requested_by_chat_id": chat_id,
            "task_id": task.id,
            "source": task.source,
            "thread_name": thread_record.name,
            "command_line": command_line,
        }
        self.memory.write("pending_confirmation_requested", f"id={task.id}\n{command_line}", source, thread=thread_record.name)
        self._reply(chat_id, self._codex_confirmation_text(task.instruction, thread_record, command_line, pending_id=task.id), thread=thread_record.name)

    def _handle_codex_confirmation_reply(self, chat_id: int, text: str, source: str) -> bool:
        pending = self._pending_codex_confirmation
        if not pending or int(pending.get("requested_by_chat_id") or pending.get("chat_id") or 0) != chat_id:
            return False
        decision = self._confirmation_decision(text)
        if decision == "":
            if text.strip().startswith("/"):
                return False
            self._reply(chat_id, "Tengo una ejecucion de Codex pendiente de confirmar. Responde `si` para lanzarla o `no` para cancelarla.")
            return True
        self._pending_codex_confirmation = None
        if decision == "no":
            self.memory.write("codex_confirmation_cancelled", str(pending.get("command_line", "")), source, thread=str(pending.get("thread_name", "")))
            self._reply(chat_id, "Cancelado. No he enviado nada a Codex CLI.", thread=str(pending.get("thread_name", "")))
            return True

        if pending.get("mode") == "codex_desktop":
            thread_record = self.threads.get(str(pending.get("thread_name", "")))
            self._start_confirmed_codex_desktop(
                int(pending["chat_id"]),
                str(pending["instruction"]),
                str(pending["source"]),
                thread_record,
            )
            return True

        if pending.get("mode") == "next_pending":
            task = self.pending.pop_next()
            if task is None or task.id != pending.get("task_id"):
                if task is not None:
                    self.pending.add(task.chat_id, task.instruction, task.thread_name, task.source)
                self._reply(chat_id, "La cola de pendientes cambio antes de confirmar. Pideme de nuevo `sigue con lo pendiente`.")
                return True
            thread_record = self.threads.get(task.thread_name)
            self.memory.write("pending_started", f"id={task.id}\n{task.instruction}", task.source, thread=thread_record.name)
            self._start_confirmed_codex(task.chat_id, task.instruction, task.source, thread_record, task)
            return True

        thread_record = self.threads.get(str(pending.get("thread_name", "")))
        self._start_confirmed_codex(
            int(pending["chat_id"]),
            str(pending["instruction"]),
            str(pending["source"]),
            thread_record,
            pending.get("pending_task") if isinstance(pending.get("pending_task"), PendingTask) else None,
        )
        return True

    def _codex_confirmation_text(self, instruction: str, thread_record: ThreadRecord, command_line: str, pending_id: str = "") -> str:
        conversation = thread_record.codex_thread_id or "conversacion nueva"
        pending_line = f"Pendiente: {pending_id}\n" if pending_id else ""
        return (
            "Antes de mandar nada a Codex CLI necesito confirmacion.\n\n"
            f"{pending_line}"
            f"Que voy a hacer: {instruction}\n"
            f"Hilo del orquestador: {thread_record.name}\n"
            f"Conversacion Codex: {conversation}\n"
            f"Modelo: {self.settings.codex_model}\n"
            f"Linea de comando:\n{command_line}\n\n"
            "Responde `si` para ejecutar o `no` para cancelar."
        )

    def _codex_desktop_confirmation_text(self, instruction: str, thread_record: ThreadRecord) -> str:
        return (
            "Antes de usar Codex Desktop necesito confirmacion.\n\n"
            f"Que voy a hacer: {instruction}\n"
            f"Hilo del orquestador: {thread_record.name}\n"
            "Herramienta obligatoria: Codex Desktop\n\n"
            "Responde `si` para ejecutar o `no` para cancelar."
        )

    @staticmethod
    def _confirmation_decision(text: str) -> str:
        normalized = text.strip().lower()
        normalized = re.sub(r"[^\wáéíóúüñ]+", " ", normalized, flags=re.IGNORECASE).strip()
        first = normalized.split(maxsplit=1)[0] if normalized else ""
        if normalized in AFFIRMATIVE_CONFIRMATIONS or first in AFFIRMATIVE_CONFIRMATIONS:
            return "yes"
        if normalized in NEGATIVE_CONFIRMATIONS or first in NEGATIVE_CONFIRMATIONS:
            return "no"
        return ""

    def _drain_pending_updates(self) -> None:
        if not self.settings.drain_pending_on_start:
            return
        try:
            updates = self.telegram.get_updates(None, 0)
        except Exception as exc:
            self.memory.write("telegram_drain_error", str(exc), "system")
            return
        if not updates:
            return
        self.offset = int(updates[-1]["update_id"]) + 1
        self.memory.write("telegram_drain", f"Descartados {len(updates)} updates pendientes. offset={self.offset}", "system")

    @staticmethod
    def _extract_instruction(text: str) -> str | None:
        stripped = text.strip()
        for prefix in ("cd ", "/cd ", "/codex_desktop ", "/codex "):
            if stripped.lower().startswith(prefix):
                instruction = stripped[len(prefix) :].strip()
                return instruction or None
        return None

    @staticmethod
    def _telegram_audio_file_id(message: dict[str, Any]) -> tuple[str, str, str]:
        for key, default_mime, default_suffix in (
            ("voice", "audio/ogg", ".ogg"),
            ("audio", "audio/mpeg", ".mp3"),
            ("document", "application/octet-stream", ".bin"),
        ):
            item = message.get(key)
            if not isinstance(item, dict):
                continue
            mime_type = str(item.get("mime_type", default_mime) or default_mime)
            if key == "document" and not mime_type.startswith("audio/"):
                continue
            file_id = str(item.get("file_id", "") or "")
            if not file_id:
                continue
            suffix = Path(str(item.get("file_name", "") or "")).suffix or default_suffix
            return file_id, mime_type, suffix
        return "", "", ""

    def _transcribe_telegram_audio(self, message: dict[str, Any], source: str) -> str:
        file_id, mime_type, suffix = self._telegram_audio_file_id(message)
        if not file_id:
            return ""
        try:
            audio_path = self.speech.temp_download_path(suffix)
            self.telegram.download_file(file_id, audio_path)
            text = self.speech.transcribe(
                audio_path,
                mime_type,
                self.voice_state.groq_api_key or self.settings.groq_api_key,
                self.voice_state.gemini_api_key or self.settings.google_api_key,
                preferred_backend=self.voice_state.stt_backend,
                fallback_order=self.voice_state.normalized_stt_order(),
            )
            self.memory.write("telegram_audio_transcribed", text, source, thread=self.threads.active_name())
            return text.strip()
        except Exception as exc:
            self.memory.write("telegram_audio_error", f"{exc}\n{traceback.format_exc()}", source, thread=self.threads.active_name())
            return ""

    def _handle_voice_command(self, text: str) -> str | None:
        stripped = text.strip()
        lower = stripped.lower()
        if lower in {"/voz", "voz", "estado voz", "estado de voz", "/voice"}:
            return self._voice_status_text()

        if lower in {"voz on", "voz encendida", "enciende voz", "activa voz", "activar voz", "/voz_on"}:
            self.voice_state.voz = True
            self.voice_store.save(self.voice_state)
            return self._voice_status_text("Voz activada.")

        if lower in {"voz off", "voz apagada", "apaga voz", "desactiva voz", "desactivar voz", "/voz_off"}:
            self.voice_state.voz = False
            self.voice_state.altavoz = False
            self.voice_store.save(self.voice_state)
            return self._voice_status_text("Voz desactivada. Altavoz tambien queda apagado.")

        if lower in {"altavoz on", "altavoz encendido", "enciende altavoz", "activa altavoz", "/altavoz_on"}:
            self.voice_state.altavoz = True
            self.voice_state.voz = True
            self.voice_store.save(self.voice_state)
            return self._voice_status_text("Altavoz activado. Voz tambien queda activada.")

        if lower in {"altavoz off", "altavoz apagado", "apaga altavoz", "desactiva altavoz", "/altavoz_off"}:
            self.voice_state.altavoz = False
            self.voice_store.save(self.voice_state)
            return self._voice_status_text("Altavoz desactivado. Voz se mantiene como esta.")

        backend = self._extract_backend_command(lower)
        if backend:
            self.voice_state.tts_backend = backend
            self.voice_store.save(self.voice_state)
            return self._voice_status_text(f"Proveedor TTS cambiado a {backend}.")

        stt_backend = self._extract_stt_backend_command(lower)
        if stt_backend:
            self.voice_state.stt_backend = stt_backend
            self.voice_store.save(self.voice_state)
            return self._voice_status_text(f"Proveedor STT cambiado a {stt_backend}.")

        if lower.startswith(("voz modelo ", "modelo voz ", "/voz_modelo ")):
            model = stripped.split(maxsplit=2)[-1].strip()
            if model:
                if self.voice_state.tts_backend == "groq":
                    self.voice_state.groq_model = model
                else:
                    self.voice_state.gemini_model = model
                self.voice_store.save(self.voice_state)
                return self._voice_status_text("Modelo TTS actualizado.")

        if lower.startswith(("voz timbre ", "voz gemini ", "voz nombre ", "/voz_timbre ")):
            voice = stripped.split(maxsplit=2)[-1].strip()
            if voice:
                if self.voice_state.tts_backend == "groq":
                    self.voice_state.groq_voice = voice
                else:
                    self.voice_state.gemini_voice = voice
                self.voice_store.save(self.voice_state)
                return self._voice_status_text("Voz/Timbre actualizado.")

        if lower.startswith(("voz api groq ", "api groq ", "guarda api groq ")):
            api_key = stripped.rsplit(maxsplit=1)[-1].strip()
            if len(api_key) >= 20:
                self.voice_state.groq_api_key = api_key
                self.voice_state.tts_backend = "groq"
                self.voice_state.tts_fallback_order = ["groq", "kokoro", "piper"]
                self.voice_store.save(self.voice_state)
                self._save_credential_env("GROQ_API_KEY", api_key)
                return self._voice_status_text("API key de Groq guardada para STT/TTS de voz.")
            return "He detectado un comando de API Groq, pero la clave parece demasiado corta."

        if lower.startswith(("voz api gemini ", "api gemini ", "api google ", "guarda api gemini ", "guarda api google ")):
            api_key = stripped.rsplit(maxsplit=1)[-1].strip()
            if len(api_key) >= 20:
                self.voice_state.gemini_api_key = api_key
                self.voice_state.tts_backend = "gemini"
                self.voice_store.save(self.voice_state)
                self._save_credential_env("GOOGLE_API_KEY", api_key)
                return self._voice_status_text("API key de Gemini guardada para TTS/STT de voz.")
            return "He detectado un comando de API, pero la clave parece demasiado corta."

        return None

    @staticmethod
    def _save_credential_env(name: str, value: str) -> None:
        path = Path("D:/credenciales")
        try:
            text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
            pattern = rf"(?m)^\s*{re.escape(name)}\s*=.*$"
            line = f"{name}={value}"
            if re.search(pattern, text):
                text = re.sub(pattern, line, text, count=1)
            else:
                text = text.rstrip() + "\n" + line + "\n"
            path.write_text(text, encoding="utf-8")
        except OSError:
            return

    @staticmethod
    def _extract_backend_command(lower: str) -> str:
        phrases = {
            "groq": ("usa voz groq", "usar voz groq", "tts groq", "voz proveedor groq", "modelo tts groq"),
            "gemini": ("usa voz gemini", "usar voz gemini", "tts gemini", "voz proveedor gemini", "modelo tts gemini"),
            "kokoro": ("usa voz kokoro", "usar voz kokoro", "tts kokoro", "voz proveedor kokoro", "modelo tts kokoro", "usa cocoro", "tts cocoro"),
            "piper": ("usa voz piper", "usar voz piper", "tts piper", "voz proveedor piper", "modelo tts piper"),
        }
        for backend, options in phrases.items():
            if lower in options:
                return backend
        return ""

    @staticmethod
    def _extract_stt_backend_command(lower: str) -> str:
        phrases = {
            "groq": ("usa transcripcion groq", "usar transcripcion groq", "stt groq", "transcripcion proveedor groq", "voz entrada groq"),
            "gemini": ("usa transcripcion gemini", "usar transcripcion gemini", "stt gemini", "transcripcion proveedor gemini", "voz entrada gemini"),
        }
        for backend, options in phrases.items():
            if lower in options:
                return backend
        return ""

    def _voice_status_text(self, prefix: str = "") -> str:
        lines = []
        if prefix:
            lines.append(prefix)
        lines.extend(
            [
                "Estado de voz:",
                f"voz: {'ON' if self.voice_state.voz else 'OFF'}",
                f"altavoz: {'ON' if self.voice_state.altavoz else 'OFF'}",
                f"stt: {self.voice_state.stt_backend}",
                f"stt_fallbacks: {' -> '.join(self.voice_state.normalized_stt_order())}",
                f"tts: {self.voice_state.tts_backend}",
                f"tts_fallback: {'ON' if self.voice_state.tts_allow_fallback else 'OFF'}",
                f"fallbacks: {' -> '.join(self.voice_state.normalized_order())}",
                f"groq_model: {self.voice_state.groq_model}",
                f"groq_voice: {self.voice_state.groq_voice}",
                f"groq_api_key: {'guardada' if self.voice_state.groq_api_key else 'no configurada'}",
                f"gemini_model: {self.voice_state.gemini_model}",
                f"gemini_voice: {self.voice_state.gemini_voice}",
                f"gemini_api_key: {'guardada' if self.voice_state.gemini_api_key else 'no configurada'}",
            ]
        )
        return "\n".join(lines)

    def _run_codex_and_reply(self, chat_id: int, instruction: str, source: str, thread_record: ThreadRecord, pending_task: PendingTask | None) -> None:
        try:
            self._current_task = {
                "thread": thread_record.name,
                "instruction": instruction,
                "started_at": MemoryLog.stamp(),
                "pending_id": pending_task.id if pending_task else "",
            }
            self.memory.write("codex_start", instruction, source, thread=thread_record.name)
            if not self.settings.lab_mode:
                self._reply(chat_id, f"Recibido. Trabajo en el hilo `{thread_record.name}`.", thread=thread_record.name)
            
            # List workspace files to make Codex aware of them
            from pathlib import Path
            workdir = Path(thread_record.workdir)
            
            # Copy all files from the shared inbox to the thread's workdir before run
            inbox_dir = Path(self.settings.codex_workdir) / "inbox"
            if inbox_dir.exists():
                workdir.mkdir(parents=True, exist_ok=True)
                import shutil
                for item in inbox_dir.iterdir():
                    if item.is_file():
                        shutil.copy(item, workdir / item.name)
            
            files = []
            if workdir.exists():
                files = [f.name for f in workdir.iterdir() if f.is_file()]
            
            enhanced_instruction = instruction
            if files:
                enhanced_instruction += f"\n\n[System Note: The following files are available in your working directory (workspace): {', '.join(files)}]"

            repaired_python = repair_python_syntax_if_requested(instruction, workdir)
            if repaired_python is not None:
                response = repaired_python.message
                self.memory.write(
                    "codex_fast_path_python_repair",
                    f"path={repaired_python.path}\n{response}",
                    "system",
                    thread=thread_record.name,
                )
                record_usage(
                    self.settings.memory_file.with_name("token_usage.jsonl"),
                    source="telegram_orchestrator",
                    component="local_python_repair",
                    provider="local",
                    model="python_compile",
                    operation="python_syntax_repair",
                    prompt_text=instruction,
                    completion_text=response,
                    task_id=str(pending_task.id if pending_task else ""),
                    user_id=str(chat_id),
                    thread_id=thread_record.name,
                    metadata={"path": str(repaired_python.path)},
                )
                self._reply(chat_id, response)
                return
            
            if self.settings.lab_mode:
                enhanced_instruction += (
                    "\n\nIMPORTANT FOR EVALUATION: Respond with ONLY the final clean, direct answer (e.g. just the number, the date in AAAA-MM-DD format, the name, or the list requested) without any pleasantries, conversational filler, markdown formatting, or extra explanations. If the question asks for a specific value, output ONLY that value."
                )
            
            result = self.codex.run(enhanced_instruction, thread_id=thread_record.codex_thread_id)
            if result.thread_id and result.thread_id != thread_record.codex_thread_id:
                thread_record = self.threads.update_codex_thread_id(thread_record.name, result.thread_id)
            response = result.text
            self.memory.write(
                "codex_finish",
                f"returncode={result.returncode} timed_out={result.timed_out} codex_thread_id={thread_record.codex_thread_id}\n\n{response}",
                "codex",
                thread=thread_record.name,
            )
            record_usage(
                self.settings.memory_file.with_name("token_usage.jsonl"),
                source="telegram_orchestrator",
                component="codex_cli",
                provider="codex",
                model=self.settings.codex_model,
                operation="codex_run",
                prompt_text=instruction,
                completion_text=response,
                task_id=str(pending_task.id if pending_task else ""),
                user_id=str(chat_id),
                thread_id=thread_record.name,
                metadata={"thread_id": thread_record.codex_thread_id, "returncode": result.returncode, "timed_out": result.timed_out},
            )
            self._reply(chat_id, response)
        except Exception as exc:
            detail = f"{exc}\n{traceback.format_exc()}"
            self.memory.write("codex_error", detail, "system", thread=thread_record.name)
            self._reply(chat_id, f"Fallo ejecutando Codex:\n\n{str(exc)}")
        finally:
            self._current_task = None
            self._busy.release()
            self._notify_pending_after_finish(chat_id)

    def _run_codex_desktop_and_reply(self, chat_id: int, instruction: str, source: str, thread_record: ThreadRecord) -> None:
        try:
            self._current_task = {
                "thread": thread_record.name,
                "instruction": instruction,
                "started_at": MemoryLog.stamp(),
                "tool": "codex_desktop",
            }
            self.memory.write("codex_desktop_start", instruction, source, thread=thread_record.name)
            self._reply(chat_id, f"Recibido. Voy a usar Codex Desktop en el hilo `{thread_record.name}`.", thread=thread_record.name)
            result = run_desktop_codex_operator(
                instruction,
                send=True,
                new_chat=not bool(thread_record.codex_thread_id),
                wait_seconds=self.settings.codex_timeout_seconds,
                debug_draft=False,
                pause_after_paste=False,
            )
            response = (
                f"Codex Desktop termino con estado: {result.status}\n"
                f"Directorio de ejecucion: {result.run_dir}\n"
                f"Captura final: {result.screenshot_path or 'sin captura'}"
            )
            self.memory.write(
                "codex_desktop_finish",
                f"ok={result.ok} status={result.status} error={result.error}\n\n{response}",
                "codex_desktop",
                thread=thread_record.name,
            )
            record_usage(
                self.settings.memory_file.with_name("token_usage.jsonl"),
                source="telegram_orchestrator",
                component="codex_desktop",
                provider="codex",
                model="codex_desktop",
                operation="codex_desktop_run",
                prompt_text=instruction,
                completion_text=response,
                task_id="",
                user_id=str(chat_id),
                thread_id=thread_record.name,
                metadata={"ok": result.ok, "status": result.status, "run_dir": str(result.run_dir)},
            )
            if result.ok:
                self._reply(chat_id, response, thread=thread_record.name)
                self._send_codex_desktop_screenshot(chat_id, result, thread_record)
                return
            self._send_codex_desktop_screenshot(chat_id, result, thread_record)
            self._reply(
                chat_id,
                "Codex Desktop no ha podido ejecutar la tarea ahora mismo.\n\n"
                f"Detalle: {result.error or result.status}\n\n"
                "Podemos dejarla preparada para cuando Codex Desktop vuelva a estar disponible o resolverla con Gemini como fallback. "
                "De momento no he lanzado el fallback automaticamente para no cambiar de herramienta sin tu confirmacion.",
                thread=thread_record.name,
            )
        except Exception as exc:
            detail = f"{exc}\n{traceback.format_exc()}"
            self.memory.write("codex_desktop_error", detail, "system", thread=thread_record.name)
            self._send_codex_desktop_screenshot(chat_id, None, thread_record)
            self._reply(
                chat_id,
                "Codex Desktop no esta disponible ahora mismo.\n\n"
                f"Detalle: {str(exc)}\n\n"
                "Podemos reintentarlo cuando vuelva la ventana de Codex o pasar esta tarea a Gemini como fallback; lo dejamos como decision explicita.",
                thread=thread_record.name,
            )
        finally:
            self._current_task = None
            self._busy.release()
            self._notify_pending_after_finish(chat_id)

    def _send_codex_desktop_screenshot(self, chat_id: int, result: Any, thread_record: ThreadRecord) -> None:
        screenshot_path = getattr(result, "screenshot_path", None)
        run_dir = getattr(result, "run_dir", None)
        path = Path(screenshot_path) if screenshot_path else None
        if path is None or not path.is_file():
            fallback_dir = Path(run_dir) if run_dir else self.settings.voice_runtime_dir.parent / "desktop_screenshots"
            path = fallback_dir / f"telegram_screen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            try:
                capture_desktop_screenshot(path)
            except Exception as exc:
                self.memory.write("codex_desktop_screenshot_error", str(exc), "system", thread=thread_record.name)
                self._reply(chat_id, f"No pude generar captura de pantalla para enviar al movil: {exc}", thread=thread_record.name)
                return
        try:
            self.telegram.send_photo(chat_id, path, caption=f"Captura Codex Desktop | hilo: {thread_record.name}")
            self.memory.write("codex_desktop_screenshot_sent", str(path), "telegram", thread=thread_record.name)
        except Exception as exc:
            self.memory.write("codex_desktop_screenshot_send_error", f"{path}\n{exc}", "system", thread=thread_record.name)
            self._reply(chat_id, f"No pude enviar la captura al movil: {exc}\n\nRuta local: {path}", thread=thread_record.name)

    def _reply(self, chat_id: int, text: str, thread: str | None = None) -> None:
        self.memory.write("telegram_out", text, "orchestrator", thread=thread or self.threads.active_name())
        self.telegram.send_message(chat_id, text)
        voice_text = self._voice_text_for_reply(text)
        if voice_text != (text or "").strip():
            summary_message = "Resumen para voz:\n" + voice_text
            self.memory.write("telegram_voice_summary", summary_message, "orchestrator", thread=thread or self.threads.active_name())
            self.telegram.send_message(chat_id, summary_message)
        self._reply_with_voice(chat_id, voice_text, thread)

    def _reply_with_voice(self, chat_id: int, text: str, thread: str | None = None) -> None:
        if not self.voice_state.voz:
            return
        clean_text = (text or "").strip()
        if not clean_text:
            return
        try:
            result = self.speech.synthesize(clean_text, self.voice_state)
            self.memory.write(
                "telegram_voice_out",
                f"provider={result.provider} detail={result.detail} path={result.path}",
                "orchestrator",
                thread=thread or self.threads.active_name(),
            )
            self.telegram.send_audio(chat_id, result.path, caption=f"Voz: {result.provider}")
            if self.voice_state.altavoz:
                self.speech.play(result.path)
        except Exception as exc:
            self.memory.write("telegram_voice_error", f"{exc}\n{traceback.format_exc()}", "orchestrator", thread=thread or self.threads.active_name())
            self.telegram.send_message(chat_id, f"No pude generar audio de voz: {exc}")

    def _voice_text_for_reply(self, text: str) -> str:
        clean_text = (text or "").strip()
        if not clean_text or not self.voice_state.voz:
            return clean_text
        if not self._is_long_voice_text(clean_text):
            return clean_text
        return self._gemini_summarize_for_voice(clean_text)

    def _gemini_summarize_for_voice(self, text: str) -> str:
        if not self.settings.google_api_key:
            return self._summarize_for_voice(text)

        prompt = (
            "Eres el sintetizador de voz de un asistente de IA. Tu tarea es generar un resumen "
            "muy narrativo, explicativo, conversacional y fluido en español del siguiente texto "
            "para ser leído en voz alta. Evita marcas de formato markdown, viñetas, caracteres "
            "especiales, código o términos técnicos excesivamente densos. Hazlo sonar natural, "
            "amigable y claro. Mantén una longitud apropiada para ser leída en unos 30-40 segundos "
            "(unas 80 a 120 palabras).\n\n"
            f"Texto original:\n{text}"
        )
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3},
        }
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            + urllib.parse.quote(self.settings.google_model, safe="")
            + ":generateContent?key="
            + urllib.parse.quote(self.settings.google_api_key, safe="")
        )
        request = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                result = json.loads(response.read().decode("utf-8", errors="replace"))
            parts = (((result.get("candidates") or [{}])[0].get("content") or {}).get("parts") or [])
            answer = "".join(str(part.get("text", "")) for part in parts if isinstance(part, dict)).strip()
            if answer:
                try:
                    record_usage(
                        Path(self.settings.memory_file).with_name("token_usage.jsonl"),
                        source="telegram_orchestrator",
                        component="voice_summarizer",
                        provider="gemini",
                        model=self.settings.google_model,
                        operation="voice_summarize",
                        prompt_text=prompt,
                        completion_text=answer,
                    )
                except Exception:
                    pass
                return answer
        except Exception as exc:
            self.memory.write("voice_summary_gemini_error", str(exc), "orchestrator", thread=self.threads.active_name())
        
        return self._summarize_for_voice(text)

    @staticmethod
    def _is_long_voice_text(text: str) -> bool:
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n+", text) if part.strip()]
        letter_count = sum(1 for char in text if char.isalpha())
        return len(paragraphs) > 2 or letter_count > VOICE_LONG_TEXT_CHARS

    @staticmethod
    def _summarize_for_voice(text: str) -> str:
        clean = re.sub(r"`{1,3}", "", text)
        clean = re.sub(r"https?://\S+", "", clean)
        clean = re.sub(r"\s+", " ", clean).strip()
        if len(clean) <= VOICE_SUMMARY_MAX_CHARS:
            return clean

        sentences = re.split(r"(?<=[.!?])\s+", clean)
        selected: list[str] = []
        total = 0
        for sentence in sentences:
            sentence = sentence.strip(" -")
            if not sentence:
                continue
            next_total = total + len(sentence) + (1 if selected else 0)
            if selected and next_total > VOICE_SUMMARY_MAX_CHARS:
                break
            selected.append(sentence)
            total = next_total
            if len(selected) >= 3:
                break
        summary = " ".join(selected).strip()
        if not summary:
            summary = clean[:VOICE_SUMMARY_MAX_CHARS].rsplit(" ", 1)[0].strip()
        if len(summary) > VOICE_SUMMARY_MAX_CHARS:
            summary = summary[:VOICE_SUMMARY_MAX_CHARS].rsplit(" ", 1)[0].strip()
        return summary + ("..." if summary and not summary.endswith((".", "!", "?")) else "")

    def _reload(self, chat_id: int) -> None:
        self._refresh_runtime_config()
        self.memory.write("config_reload", self._status_text(), "system")
        self._reply(chat_id, "Configuracion recargada.\n\n" + self._status_text())

    def _refresh_runtime_config(self) -> None:
        self.settings = load_settings()
        self.memory = MemoryLog(self.settings.memory_file)
        self.telegram = TelegramApi(self.settings.telegram_bot_token, self.settings.message_chunk_size)
        self.codex = CodexRunner(self.settings)
        self.codex_dirs = CodexDirStore(self.settings.codex_dirs_file)
        self.alarms = AlarmStore(self.settings.alarms_file)
        self.remembers = RememberStore(self.settings.memories_file)
        self.threads = ThreadStore(self.settings.threads_file, self.settings.codex_workdir, self.settings.codex_extra_dirs)
        self.pending = PendingTaskStore(self.settings.pending_tasks_file)
        self.interpreter = IntentInterpreter(self.settings)
        self.voice_store = VoiceStateStore(self.settings.voice_settings_file, self.settings.google_api_key, self.settings.groq_api_key)
        self.voice_state = self.voice_store.load()
        self.speech = SpeechIO(self.settings.voice_runtime_dir)

    def _alarm_loop(self) -> None:
        while not self._stop.is_set():
            try:
                now = datetime.now()
                for alarm in self.alarms.due(now):
                    text = f"Alarma: {alarm.text}"
                    self.memory.write("alarm_fired", format_alarm(alarm), "alarm_loop", thread="alarmas")
                    self._reply(alarm.chat_id, text, thread="alarmas")
                    next_alarm = self.alarms.mark_fired(alarm, now)
                    if next_alarm is not None:
                        self.memory.write("alarm_rescheduled", format_alarm(next_alarm), "alarm_loop", thread="alarmas")
            except Exception as exc:
                self.memory.write("alarm_error", f"{exc}\n{traceback.format_exc()}", "alarm_loop", thread="alarmas")
            self._stop.wait(max(1, self.settings.alarm_check_seconds))

    def _alarms_text(self, chat_id: int) -> str:
        alarms = self.alarms.list_enabled(chat_id)
        if not alarms:
            return "No hay alarmas activas."
        lines = ["Alarmas activas:"]
        lines.extend(format_alarm(alarm) for alarm in alarms)
        return "\n".join(lines)

    def _memories_text(self) -> str:
        lines = self.remembers.tail()
        if not lines:
            return "No hay recuerdos guardados."
        return "Ultimos recuerdos:\n" + "\n".join(lines)

    def _memory_query_text(self, query: str) -> str:
        clean_query = " ".join((query or "").split())
        remembered = self.remembers.search(clean_query, limit=8)
        event_matches = self._search_event_memory(clean_query, limit=6)
        if not remembered and not event_matches:
            return f"No he encontrado memoria relevante sobre: {clean_query or 'ese tema'}."
        gemini_answer = self._answer_memory_with_gemini(clean_query, remembered, event_matches)
        if gemini_answer:
            return gemini_answer
        lines = [f"He encontrado esto sobre {clean_query or 'memoria'}:"]
        if remembered:
            lines.append("\nRecuerdos guardados:")
            lines.extend(remembered)
        if event_matches:
            lines.append("\nEventos recientes:")
            lines.extend(event_matches)
        return "\n".join(lines)

    def _search_event_memory(self, query: str, limit: int = 6) -> list[str]:
        words = [word.casefold() for word in (query or "").split() if len(word) >= 3]
        if not words:
            return []
        try:
            lines = self.settings.memory_file.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return []
        matches: list[str] = []
        current_header = ""
        for line in reversed(lines):
            clean = line.strip()
            if not clean:
                continue
            if clean.startswith("[") and "]" in clean:
                current_header = clean
                continue
            folded = clean.casefold()
            if any(word in folded for word in words):
                prefix = f"{current_header} " if current_header else ""
                matches.append((prefix + clean)[:260])
                if len(matches) >= limit:
                    break
        return matches

    def _answer_memory_with_gemini(self, query: str, remembered: list[str], event_matches: list[str]) -> str:
        if not self.settings.google_api_key:
            return ""
        context_lines: list[str] = []
        if remembered:
            context_lines.append("Recuerdos guardados:")
            context_lines.extend(remembered[:8])
        if event_matches:
            context_lines.append("Eventos relevantes:")
            context_lines.extend(event_matches[:6])
        context = "\n".join(context_lines).strip()
        if not context:
            return ""
        prompt = (
            "Responde en espanol de forma breve usando solo la memoria proporcionada. "
            "Si la memoria no basta, dilo claramente.\n\n"
            f"Pregunta: {query or 'resume la memoria relevante'}\n\n"
            f"Memoria:\n{context}"
        )
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1},
        }
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            + urllib.parse.quote(self.settings.google_model, safe="")
            + ":generateContent?key="
            + urllib.parse.quote(self.settings.google_api_key, safe="")
        )
        request = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=min(self.settings.google_intent_timeout_seconds, 20)) as response:
                result = json.loads(response.read().decode("utf-8", errors="replace"))
        except Exception as exc:
            self.memory.write("memory_gemini_error", str(exc), "orchestrator", thread="recuerdos")
            return ""
        parts = (((result.get("candidates") or [{}])[0].get("content") or {}).get("parts") or [])
        answer = "".join(str(part.get("text", "")) for part in parts if isinstance(part, dict)).strip()
        if not answer:
            return ""
        try:
            record_usage(
                Path(self.settings.memory_file).with_name("token_usage.jsonl"),
                source="telegram_orchestrator",
                component="memory",
                provider="gemini",
                model=self.settings.google_model,
                operation="memory_query",
                prompt_text=prompt,
                completion_text=answer,
                metadata={"query": query},
            )
        except Exception:
            pass
        return answer

    def _direct_local_text(self, args: dict[str, Any]) -> str:
        kind = str(args.get("kind", "")).strip().lower()
        now = datetime.now()
        if kind == "time":
            return "Son las " + now.strftime("%H:%M") + "."
        if kind == "date":
            return "Hoy es " + now.strftime("%Y-%m-%d") + "."
        if kind == "list_files":
            try:
                items = sorted(self.settings.codex_workdir.iterdir(), key=lambda item: (item.is_file(), item.name.lower()))
            except OSError as exc:
                return f"No pude listar la carpeta de trabajo: {exc}"
            lines = [f"Archivos en {self.settings.codex_workdir}:"]
            for item in items[:40]:
                marker = "[d]" if item.is_dir() else "[f]"
                lines.append(f"{marker} {item.name}")
            if len(items) > 40:
                lines.append(f"... y {len(items) - 40} mas.")
            return "\n".join(lines)
        return "Puedo responder eso directamente, pero no reconoci la accion local concreta."

    def _codex_dirs_text(self) -> str:
        dirs = self.codex_dirs.list()
        if not dirs:
            return "No hay carpetas extra para Codex. Solo trabaja en el workdir principal."
        lines = ["Carpetas extra de Codex:"]
        lines.extend(str(path) for path in dirs)
        return "\n".join(lines)

    def _activity_text(self) -> str:
        lines = ["Estado de actividad:"]
        lines.append(f"Codex ocupado: {'si' if self._busy.locked() else 'no'}")
        lines.append(f"Hilo activo: {self.threads.active_name()}")
        if self._current_task:
            lines.append(f"Tarea actual: {self._current_task_summary()}")
        else:
            lines.append("Tarea actual: ninguna")
        pending = self.pending.list()
        lines.append(f"Pendientes: {len(pending)}")
        if pending:
            first = pending[0]
            lines.append(f"Siguiente: {first.id} | {first.thread_name} | {first.instruction[:120]}")
        return "\n".join(lines)

    def _pending_text(self) -> str:
        tasks = self.pending.list()
        if not tasks:
            return "No hay tareas pendientes para Codex."
        lines = ["Tareas pendientes:"]
        for task in tasks:
            lines.append(f"{task.id} | {task.thread_name} | {task.created_at} | {task.instruction[:160]}")
        return "\n".join(lines)

    def _start_next_pending(self, chat_id: int) -> None:
        if self._busy.locked():
            self._reply(chat_id, "Codex sigue ocupado. La tarea pendiente se mantiene en cola.")
            return
        task = self.pending.pop_next()
        if task is None:
            self._reply(chat_id, "No hay tareas pendientes.")
            return
        thread_record = self.threads.get(task.thread_name)
        if not self._busy.acquire(blocking=False):
            self.pending.add(task.chat_id, task.instruction, task.thread_name, task.source)
            self._reply(chat_id, "Codex acaba de quedar ocupado. Reencolo la tarea.")
            return
        self.memory.write("pending_started", f"id={task.id}\n{task.instruction}", task.source, thread=thread_record.name)
        worker = threading.Thread(
            target=self._run_codex_and_reply,
            args=(task.chat_id, task.instruction, task.source, thread_record, task),
            daemon=True,
        )
        worker.start()

    def _cancel_current_task(self, chat_id: int, source: str) -> None:
        if not self._busy.locked() or not self.codex.is_running():
            self._reply(chat_id, "No hay ninguna tarea de Codex en ejecucion.")
            return
        task_summary = self._current_task_summary()
        ok = self.codex.cancel()
        self.memory.write("codex_cancel_requested", f"ok={ok}\n{task_summary}", source, thread=self.threads.active_name())
        if ok:
            self._reply(chat_id, "He pedido detener la tarea actual de Codex. Puede tardar unos segundos en cerrarse limpiamente.")
        else:
            self._reply(chat_id, "He intentado detener Codex, pero el proceso ya no estaba activo.")

    def _notify_pending_after_finish(self, chat_id: int) -> None:
        tasks = self.pending.list()
        if not tasks:
            return
        first = tasks[0]
        self._reply(
            chat_id,
            f"Quedan {len(tasks)} tarea(s) pendiente(s). La siguiente es {first.id} en `{first.thread_name}`.\nDime: sigue con lo pendiente.",
        )

    def _current_task_summary(self) -> str:
        if not self._current_task:
            return "ninguna"
        pending = f" pending={self._current_task['pending_id']}" if self._current_task.get("pending_id") else ""
        return f"{self._current_task['thread']} desde {self._current_task['started_at']}{pending}: {self._current_task['instruction'][:140]}"

    def _threads_text(self) -> str:
        active = self.threads.active_name()
        lines = ["Hilos:"]
        for record in self.threads.list():
            marker = "*" if record.name == active else "-"
            codex = " codex=si" if record.codex_thread_id else ""
            lines.append(f"{marker} {self._thread_line(record)}{codex}")
        return "\n".join(lines)

    def _current_thread_text(self) -> str:
        return "Hilo activo:\n" + self._thread_line(self.threads.active())

    @staticmethod
    def _thread_line(record: ThreadRecord) -> str:
        return f"{record.name} | {record.kind} | {record.title or record.name}"

    def _status_text(self) -> str:
        busy = "si" if self._busy.locked() else "no"
        return "\n".join(
            [
                "Estado del orquestador Codex",
                f"busy: {busy}",
                f"current_task: {self._current_task_summary()}",
                f"pending_tasks: {len(self.pending.list())}",
                f"workdir: {self.settings.codex_workdir}",
                f"extra_dirs: {len(self.settings.codex_extra_dirs)}",
                f"active_thread: {self.threads.active_name()}",
                f"threads: {self.settings.threads_file}",
                f"pending_file: {self.settings.pending_tasks_file}",
                f"codex: {' '.join(self.settings.codex_command)}",
                f"codex_model: {self.settings.codex_model}",
                f"sandbox: {self.settings.codex_sandbox}",
                f"approval: {self.settings.codex_approval}",
                f"timeout: {self.settings.codex_timeout_seconds}s",
                f"memory: {self.settings.memory_file}",
                f"memories: {self.settings.memories_file}",
                f"alarms: {self.settings.alarms_file}",
                f"voz: {'ON' if self.voice_state.voz else 'OFF'}",
                f"altavoz: {'ON' if self.voice_state.altavoz else 'OFF'}",
                f"stt_backend: {self.voice_state.stt_backend}",
                f"stt_order: {' -> '.join(self.voice_state.normalized_stt_order())}",
                f"tts_backend: {self.voice_state.tts_backend}",
                f"tts_fallback: {'ON' if self.voice_state.tts_allow_fallback else 'OFF'}",
                f"tts_order: {' -> '.join(self.voice_state.normalized_order())}",
                f"groq_tts: {self.voice_state.groq_model} / {self.voice_state.groq_voice}",
                f"voice_settings: {self.settings.voice_settings_file}",
                f"google_intent: {self.settings.google_intent_enabled and bool(self.settings.google_api_key)} ({self.settings.google_model}, {self.settings.google_api_key_source})",
                f"hot_reload: {self.settings.hot_reload}",
                f"drain_pending_on_start: {self.settings.drain_pending_on_start}",
            ]
        )

    @staticmethod
    def _help_text() -> str:
        return "\n".join(
            [
                "Comandos:",
                "alarma <texto>      Crea una alarma con parser estricto",
                "memoria <texto>     Guarda memoria con timestamp",
                "recuerdo <texto>    Busca y responde usando la memoria",
                "escritorio <texto>  Fuerza Codex Desktop",
                "linea <texto>       Fuerza Codex CLI",
                "hilo actual | nuevo hilo <nombre> | usar hilo <nombre>",
                "estado | pendientes | siguiente",
                "Cd <instruccion>  Pide confirmacion y ejecuta Codex Desktop",
                "/codex <instruccion>  Pide confirmacion y ejecuta Codex CLI",
                "/status          Estado",
                "/alarmas         Lista alarmas activas",
                "/cancelar_alarma <id>",
                "/recuerdos       Lista recuerdos guardados",
                "/hilos           Lista hilos",
                "/hilo            Hilo activo",
                "/pendientes      Lista tareas Codex pendientes",
                "/siguiente       Ejecuta la siguiente pendiente",
                "/limpiar_pendientes",
                "/nuevo_hilo <nombre>",
                "/usar_hilo <nombre>",
                "/directorios     Lista carpetas extra de Codex",
                "/add_dir <ruta>  Anade carpeta extra a Codex",
                "/remove_dir <ruta>",
                "/reload          Recarga .env",
                "/restart         Reinicio en caliente con supervisor",
                "/voz             Estado de voz",
                "voz on/off       Envia tambien audio por Telegram",
                "altavoz on/off   Altavoz on activa voz, manda audio y lo reproduce en el PC",
                "usa voz groq|kokoro|piper|gemini",
                "usa transcripcion groq|gemini",
                "voz modelo <modelo TTS>",
                "voz timbre <voz>",
                "voz api groq <clave>",
                "voz api gemini <clave>",
                "Ejemplo: recuerda que el wifi de casa se llama MiRed",
                "Ejemplo: anade carpeta G:\\Otros ordenadores\\Main\\D",
                "Ejemplo: avisame dentro de 15 minutos de poner la television",
                "Ejemplo: recuerdame manana a las 9 que revise el correo",
                "Ejemplo: todos los lunes a las 9 revisar agenda",
            ]
        )

    def _fingerprint_code(self) -> str:
        digest = hashlib.sha256()
        for path in sorted(ROOT.glob("*.py")):
            stat = path.stat()
            digest.update(str(path.name).encode("utf-8"))
            digest.update(str(stat.st_mtime_ns).encode("ascii"))
            digest.update(str(stat.st_size).encode("ascii"))
        return digest.hexdigest()

    def _code_changed(self) -> bool:
        if not self.settings.hot_reload:
            return False
        now = time.monotonic()
        if now < self._next_code_check:
            return False
        self._next_code_check = now + max(1, self.settings.code_watch_seconds)
        return self._fingerprint_code() != self._code_fingerprint


def main() -> int:
    try:
        return Orchestrator().run()
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else 1


if __name__ == "__main__":
    sys.exit(main())
