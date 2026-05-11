from __future__ import annotations

import hashlib
import re
import sys
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

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
    Intent,
    IntentInterpreter,
)
from memories import RememberStore
from memory import MemoryLog
from pending_tasks import PendingTask, PendingTaskStore
from speech_io import SpeechIO
from thread_store import ThreadRecord, ThreadStore
from telegram_api import TelegramApi
from voice_state import VoiceStateStore


RESTART_EXIT_CODE = 75


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
        text = (message.get("text") or "").strip()
        source = f"telegram user_id={user_id} chat_id={chat_id}"

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
            self._start_next_pending(chat_id)
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

        instruction = str(intent.args.get("instruction", "")).strip()
        if intent.action != ACTION_CODEX or not instruction:
            self._reply(chat_id, "Comando no reconocido. Usa C <instruccion>, pideme una alarma o dime 'recuerda que ...'.")
            return

        thread_record = self.threads.choose_for_codex(instruction, str(intent.args.get("thread_name", "")).strip() or None)
        self.threads.set_active(thread_record.name)

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
            args=(chat_id, instruction, source, thread_record, None),
            daemon=True,
        )
        worker.start()

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
        for prefix in ("c ", "-c ", "/c ", "/codex "):
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

    def _voice_status_text(self, prefix: str = "") -> str:
        lines = []
        if prefix:
            lines.append(prefix)
        lines.extend(
            [
                "Estado de voz:",
                f"voz: {'ON' if self.voice_state.voz else 'OFF'}",
                f"altavoz: {'ON' if self.voice_state.altavoz else 'OFF'}",
                f"tts: {self.voice_state.tts_backend}",
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
            self._reply(chat_id, f"Recibido. Trabajo en el hilo `{thread_record.name}`.", thread=thread_record.name)
            result = self.codex.run(instruction, thread_id=thread_record.codex_thread_id)
            if result.thread_id and result.thread_id != thread_record.codex_thread_id:
                thread_record = self.threads.update_codex_thread_id(thread_record.name, result.thread_id)
            response = result.text
            self.memory.write(
                "codex_finish",
                f"returncode={result.returncode} timed_out={result.timed_out} codex_thread_id={thread_record.codex_thread_id}\n\n{response}",
                "codex",
                thread=thread_record.name,
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

    def _reply(self, chat_id: int, text: str, thread: str | None = None) -> None:
        self.memory.write("telegram_out", text, "orchestrator", thread=thread or self.threads.active_name())
        self.telegram.send_message(chat_id, text)
        self._reply_with_voice(chat_id, text, thread)

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
                f"sandbox: {self.settings.codex_sandbox}",
                f"approval: {self.settings.codex_approval}",
                f"timeout: {self.settings.codex_timeout_seconds}s",
                f"memory: {self.settings.memory_file}",
                f"memories: {self.settings.memories_file}",
                f"alarms: {self.settings.alarms_file}",
                f"voz: {'ON' if self.voice_state.voz else 'OFF'}",
                f"altavoz: {'ON' if self.voice_state.altavoz else 'OFF'}",
                f"tts_backend: {self.voice_state.tts_backend}",
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
                "C <instruccion>   Ejecuta Codex CLI",
                "-c <instruccion>  Alias compatible",
                "/c <instruccion>  Alias compatible",
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
