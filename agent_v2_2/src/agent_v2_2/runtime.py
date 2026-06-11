from __future__ import annotations

import logging
import json
import threading
import time
from pathlib import Path
from typing import Callable, Optional

from .application import AgentApplication
from .capabilities.introspection import IntrospectionManager
from .capabilities.directories import AllowedDirectoryStore
from .capabilities.memory import MemoryStore, ThreadRegistry
from .capabilities.preferences import PreferenceStore
from .capabilities.status import StatusManager
from .capabilities.voice import VoiceCapabilities
from .config import load_config
from .engines.codex_desktop import CodexDesktopOperator
from .engines.execution import ExecutionEngine
from .engines.workspace import WorkspaceManager
from .models import Attachment, OrchestratorResult, RouteDecision, TaskRequest
from .privacy.core import (
    ConfirmationStore,
    build_confirmation_message,
    is_confirmation_no,
    is_confirmation_yes,
    should_require_human_confirmation,
    redact_sensitive_text,
)
from .routing.builder import ContractBuilder
from .routing.contract import RequestContract
from .routing.executor import execute_local_command
from .routing.evolutionary import EvolutionarySelector
from .routing.cancellation import CancellationManager
from .routing.selector import CapabilitySelector
from .scheduling.codex_quota import CodexQuotaMonitor
from .scheduling.alarms import AlarmScheduler, parse_alarm_request
from .scheduling.autonomy import QuotaAwareScheduler
from .scheduling.queue import TaskQueue
from .transport import TelegramTransport
from .transport.queue import ExecutionMailbox
from .evolution.experience import ExperienceStore
from .evolution.hitl import HITLController, HITLTrial
from .transport.metrics import MetricsRecorder
from .transport.lifecycle import LifecycleManager


logger = logging.getLogger("agent_v2_2.runtime")


class TelegramAgentRuntime:
    """Glue layer between Telegram updates and the vertical Agent 2.2 flow."""

    def __init__(
        self,
        *,
        transport: Optional[TelegramTransport] = None,
        application: Optional[AgentApplication] = None,
        selector: Optional[CapabilitySelector] = None,
        contract_builder: Optional[ContractBuilder] = None,
        workspace_manager: Optional[WorkspaceManager] = None,
        execution_engine: Optional[ExecutionEngine] = None,
        codex_desktop: Optional[CodexDesktopOperator] = None,
        voice: Optional[VoiceCapabilities] = None,
        memory_store: Optional[MemoryStore] = None,
        experience_store: Optional[ExperienceStore] = None,
        quota_monitor: Optional[CodexQuotaMonitor] = None,
        status_manager: Optional[StatusManager] = None,
        introspection: Optional[IntrospectionManager] = None,
        mailbox: Optional[ExecutionMailbox] = None,
        lifecycle: Optional[LifecycleManager] = None,
        metrics: Optional[MetricsRecorder] = None,
        development_mode: Optional[object] = None,
        hitl_controller: Optional[HITLController] = None,
        confirmation_store: Optional[ConfirmationStore] = None,
        alarm_scheduler: Optional[AlarmScheduler] = None,
        task_queue: Optional[TaskQueue] = None,
        thread_registry: Optional[ThreadRegistry] = None,
        directory_store: Optional[AllowedDirectoryStore] = None,
        cancellation_manager: Optional[CancellationManager] = None,
    ) -> None:
        config = load_config()
        self.config = config
        self.workspace_root = config.workspace_root.resolve()
        self.transport = transport or TelegramTransport(config)
        self.experience_store = experience_store or ExperienceStore()
        self.selector = selector or self._default_selector()
        self.contract_builder = contract_builder or ContractBuilder()
        self.workspace_manager = workspace_manager or WorkspaceManager(self.workspace_root)
        self.execution_engine = execution_engine or ExecutionEngine(self.workspace_manager)
        self.codex_desktop = codex_desktop or CodexDesktopOperator()
        self.voice = voice or VoiceCapabilities()
        self.memory_store = memory_store or MemoryStore()
        self.threads = thread_registry or ThreadRegistry()
        self.quota_monitor = quota_monitor or CodexQuotaMonitor()
        self.status_manager = status_manager or StatusManager()
        self.introspection = introspection or IntrospectionManager()
        self.mailbox = mailbox or ExecutionMailbox()
        self.lifecycle = lifecycle or LifecycleManager()
        self.directories = directory_store or AllowedDirectoryStore()
        self.cancellations = cancellation_manager or CancellationManager()
        self.metrics = metrics or MetricsRecorder()
        self.preferences = PreferenceStore()
        self.hitl = hitl_controller or HITLController(
            experience_store=self.experience_store
        )
        self._pending_hitl_trials: dict[int, HITLTrial] = {}
        self.confirmations = confirmation_store or ConfirmationStore()
        self.alarms = alarm_scheduler or AlarmScheduler(
            lambda target_chat, message: self.transport.send_message(
                target_chat,
                f"Recordatorio: {message}",
            )
        )
        self.task_queue = task_queue or TaskQueue()
        self.autonomous_scheduler = QuotaAwareScheduler(
            task_queue=self.task_queue,
            quota_monitor=self.quota_monitor,
        )
        self._queue_stop = threading.Event()
        self._queue_thread: Optional[threading.Thread] = None
        self.development_mode = development_mode or self._default_development_mode()
        self.transport.set_message_handler(self.handle_message)
        self.transport.set_progress_handler(self._handle_transport_progress)
        self.application = application or AgentApplication(
            selector=self.selector,
            executor=self.execute_request,
            memory_store=self.memory_store,
            experience_store=self.experience_store,
            voice=self.voice,
        )

    def run(self) -> None:
        self.alarms.start()
        self._start_queue_worker()
        try:
            self.transport.start_polling()
        finally:
            self._stop_queue_worker()
            self.alarms.stop()

    def handle_message(
        self,
        text: str,
        chat_id: int,
        *,
        media_file_id: str | None = None,
        media_type: str | None = None,
        message: dict | None = None,
    ) -> None:
        raw_text = (text or "").strip()
        if self._handle_cancellation_command(raw_text, chat_id):
            return
        if self._handle_confirmation_reply(raw_text, chat_id):
            return
        if self._handle_alarm_command(raw_text, chat_id):
            return
        if self._handle_queue_command(raw_text, chat_id):
            return
        if self._handle_thread_command(raw_text, chat_id):
            return
        if self._handle_hitl_command(raw_text, chat_id):
            return
        if self._handle_local_information(raw_text, chat_id):
            return
        if self._handle_development(raw_text, chat_id):
            return

        attachments, prepared_text, source_metadata = self._prepare_incoming_payload(
            chat_id,
            media_file_id=media_file_id,
            media_type=media_type,
            message=message or {},
            text=raw_text,
        )
        if prepared_text is None:
            return

        if source_metadata.get("source") == "voice":
            self.transport.send_message(chat_id, f"Transcrito\n{self._format_seconds(source_metadata.get('transcription_seconds', 0.0))}")
        else:
            self.transport.send_message(chat_id, "Recibido\n0.1s")

        if self._handle_local_information(prepared_text, chat_id):
            return
        if self._handle_development(prepared_text, chat_id):
            return

        request = self._build_request(
            chat_id=chat_id,
            text=prepared_text,
            attachments=attachments,
            metadata=source_metadata,
        )
        contract = self.contract_builder.build(
            request.text,
            attachments=request.attachments,
            metadata={
                "telegram_chat_id": chat_id,
                "telegram_media_type": media_type or "",
                "telegram_source": source_metadata.get("source", "text"),
            },
        )
        confirmation_required, confirmation_reason = (
            should_require_human_confirmation(prepared_text)
        )
        if confirmation_required and not request.metadata.get(
            "human_confirmation_approved"
        ):
            preview = self.selector.select_contract(contract)
            self.confirmations.set(
                chat_id,
                {
                    "request": request.model_dump(mode="json"),
                    "contract": contract.model_dump(mode="json"),
                    "reason": confirmation_reason,
                    "tool_id": preview.tool_id,
                },
            )
            self.transport.send_message(
                chat_id,
                build_confirmation_message(
                    preview.tool_id,
                    confirmation_reason or "accion sensible",
                ),
            )
            return
        result = self._execute_application_request(chat_id, request, contract)
        trial = self._pending_hitl_trials.pop(chat_id, None)
        if trial is not None:
            elapsed = (
                result.timings.total_seconds
                if result.timings
                else result.elapsed_seconds
            )
            self.hitl.link_result(
                trial.trial_id,
                experience_id=request.request_id,
                tool_id=result.tool_id,
                elapsed_seconds=elapsed,
            )
        self._deliver_result(chat_id, request, result)
        if trial is not None:
            self.transport.send_message(
                chat_id,
                "Valoracion: responde `si`, `mas o menos` o `no`. "
                "Puedes anadir una correccion despues de la respuesta.",
            )

    def execute_request(self, request: TaskRequest, decision: RouteDecision) -> OrchestratorResult:
        if (
            "codex" in decision.tool_id
            and not request.metadata.get("from_persistent_queue")
            and not self.quota_monitor.can_schedule_codex(refresh=True)
        ):
            queued = request.model_copy(
                update={
                    "tool_name": decision.tool_id,
                    "metadata": {
                        **request.metadata,
                        "queued_decision": decision.model_dump(mode="json"),
                    },
                }
            )
            task_id = self.task_queue.enqueue(queued)
            self.task_queue.mark_paused(
                task_id,
                reason=self.quota_monitor.pause_reason()
                or "Codex quota unavailable.",
                status="paused_quota",
            )
            return OrchestratorResult(
                ok=True,
                tool_id=decision.tool_id,
                tier=decision.tier,
                output=(
                    f"Tarea `{task_id[:8]}` guardada. Se retomara cuando "
                    "la cuota Codex vuelva a estar disponible."
                ),
                privacy_mode=decision.privacy_mode,
                metadata={
                    "evidence_kind": "queued",
                    "queue_task_id": task_id,
                },
            )
        if decision.tool_id == "local_direct":
            return self._execute_local_request(request, decision)
        if "desktop_codex" in decision.tool_id:
            return self._execute_desktop_codex(request, decision)
        if "codex" in decision.tool_id:
            return self._execute_workspace_request(request, decision)
        if decision.tool_id.startswith("gemini") or decision.tool_id.startswith("worker_") or decision.tool_id.startswith("router_"):
            return self._execute_workspace_request(request, decision)
        return OrchestratorResult(
            ok=True,
            tool_id=decision.tool_id,
            tier=decision.tier,
            output=f"Ruta preparada para {decision.tool_id}: {request.text}",
            privacy_mode=decision.privacy_mode,
        )

    def execute_voice(self, audio_path: Path, request: TaskRequest, contract: RequestContract) -> OrchestratorResult:
        return self.application.handle_voice(
            audio_path,
            request,
            contract,
            progress_callback=self._build_progress_callback(request.user_id or 0),
        )

    def _execute_local_request(self, request: TaskRequest, decision: RouteDecision) -> OrchestratorResult:
        command = request.text.strip()
        if command.casefold().startswith("ejecuta "):
            return execute_local_command(request, decision, self.workspace_root)
        if command.startswith("!"):
            return execute_local_command(
                request.model_copy(update={"text": f"ejecuta {command[1:].strip()}"}),
                decision,
                self.workspace_root,
            )
        return OrchestratorResult(
            ok=True,
            tool_id=decision.tool_id,
            tier=decision.tier,
            output=f"Respuesta local preparada: {command}",
            privacy_mode=decision.privacy_mode,
        )

    def _execute_workspace_request(self, request: TaskRequest, decision: RouteDecision) -> OrchestratorResult:
        result = self.execution_engine.execute_code(request, decision)
        if result.workdir is None:
            result.workdir = self.workspace_manager.create_isolated_workspace()
        if not result.output.strip():
            result.output = f"Trabajo preparado para {decision.tool_id}."
        return result

    def _execute_desktop_codex(self, request: TaskRequest, decision: RouteDecision) -> OrchestratorResult:
        workdir = self.workspace_manager.create_isolated_workspace()
        output = self.codex_desktop.execute_task(request.text, workdir)
        return OrchestratorResult(
            ok=True,
            tool_id=decision.tool_id,
            tier=decision.tier,
            output=output,
            workdir=workdir,
            privacy_mode=decision.privacy_mode,
        )

    def _build_request(
        self,
        *,
        chat_id: int,
        text: str,
        attachments: list[Attachment],
        metadata: dict,
    ) -> TaskRequest:
        request_metadata = {
            "source": metadata.get("source", "text"),
            "telegram_chat_id": chat_id,
            "telegram_media_type": metadata.get("media_type", ""),
            "telegram_message_id": metadata.get("message_id"),
            "telegram_file_id": metadata.get("telegram_file_id"),
            "transcription_seconds": metadata.get("transcription_seconds", 0.0),
        }
        request_metadata.update(metadata)
        preferences = self.preferences.load()
        prepared_text = (
            redact_sensitive_text(text)
            if preferences.anonymization_enabled
            else text
        )
        request_metadata["privacy_mode"] = (
            "redacted" if preferences.anonymization_enabled else "clear"
        )
        resolved_paths = self.directories.resolve_references(text)
        known_paths = {Path(item.path).resolve() for item in attachments}
        prepared_attachments = list(attachments)
        for path in resolved_paths:
            if path.resolve() in known_paths:
                continue
            prepared_attachments.append(
                Attachment(
                    kind="document",
                    path=path,
                    label=path.name,
                    source="allowed_directory",
                )
            )
            known_paths.add(path.resolve())
        return TaskRequest(
            user_id=str(chat_id),
            thread_id=self.threads.current(str(chat_id)),
            text=prepared_text,
            attachments=prepared_attachments,
            metadata=request_metadata,
            capability=str(metadata.get("primary_capability", "")),
            operation=str(metadata.get("operation", "")),
            format=str(metadata.get("format", "")),
            tool_name=str(metadata.get("tool_name", "")),
        )

    def _prepare_incoming_payload(
        self,
        chat_id: int,
        *,
        media_file_id: str | None,
        media_type: str | None,
        message: dict,
        text: str,
    ) -> tuple[list[Attachment], Optional[str], dict]:
        source = "text"
        metadata: dict = {"source": "text"}
        attachments: list[Attachment] = []

        if media_file_id and media_type:
            source = media_type
            downloaded = self._download_media(chat_id, media_file_id, media_type, message)
            attachment = Attachment(
                kind=media_type,
                path=downloaded,
                label=str(message.get("caption") or message.get("file_name") or media_type),
                source="telegram",
            )
            attachments.append(attachment)
            metadata.update(
                {
                    "source": media_type,
                    "media_type": media_type,
                    "telegram_file_id": media_file_id,
                    "telegram_file_path": str(downloaded),
                    "message_id": message.get("message_id"),
                }
            )
            if media_type in {"voice", "audio"}:
                transcription_started = time.monotonic()
                transcript = self.voice.transcribe_audio_file(downloaded)
                metadata["transcription_seconds"] = time.monotonic() - transcription_started
                if not transcript.strip():
                    self.transport.send_message(chat_id, "No he podido transcribir la nota de voz.")
                    return attachments, None, metadata
                text = transcript.strip()
                source = "voice" if media_type == "voice" else "audio"
                metadata["source"] = source
                attachments = [
                    item
                    for item in attachments
                    if item.kind not in {"voice", "audio"}
                ]
            elif media_type in {"photo", "document"} and not text:
                text = str(message.get("caption") or message.get("file_name") or media_type).strip()

        if not text.strip():
            return attachments, None, metadata

        metadata.setdefault("source", source)
        return attachments, text.strip(), metadata

    def _download_media(self, chat_id: int, file_id: str, media_type: str, message: dict) -> Path:
        suffix = self._suffix_for_media(media_type, message)
        target_dir = self.workspace_root / "telegram" / str(chat_id) / "inbox"
        target_dir.mkdir(parents=True, exist_ok=True)
        return self.transport.download_file(file_id, target_dir / suffix.name)

    def _suffix_for_media(self, media_type: str, message: dict) -> Path:
        file_name = str(message.get("file_name") or message.get("caption") or media_type).strip()
        suffix = Path(file_name).suffix
        if suffix:
            return Path(file_name)
        defaults = {
            "voice": Path("voice.ogg"),
            "audio": Path("audio.mp3"),
            "photo": Path("image.jpg"),
            "document": Path("document.bin"),
        }
        return defaults.get(media_type, Path(f"{media_type}.bin"))

    def _handle_local_information(self, text: str, chat_id: int) -> bool:
        command = self._normalize_command(text)
        preference_commands = {
            "voz on": ("voice", True),
            "voz off": ("voice", False),
            "altavoz on": ("speaker", True),
            "altavoz off": ("speaker", False),
            "anonimizacion on": ("anonymization", True),
            "anonimizacion off": ("anonymization", False),
        }
        preference = preference_commands.get(command)
        if preference is not None:
            name, enabled = preference
            if name == "voice":
                state = self.preferences.toggle_voice(enabled)
                value = state.voice_enabled
            elif name == "speaker":
                state = self.preferences.toggle_speaker(enabled)
                value = state.speaker_enabled
            else:
                state = self.preferences.set_anonymization(enabled)
                value = state.anonymization_enabled
            self.transport.send_message(
                chat_id,
                f"{name}={'on' if value else 'off'}",
            )
            return True
        if command in {"estado", "/estado", "status", "/status", "estado del sistema"}:
            self.transport.send_message(chat_id, self.status_manager.generate_status_report())
            self._send_quota_footer(chat_id)
            return True
        if command in {
            "diagnostico",
            "diagnostico proveedores",
            "diagnostico de proveedores",
            "/diagnostico",
        }:
            self.transport.send_message(
                chat_id,
                self.status_manager.generate_provider_diagnostics(),
            )
            return True
        if command in {"/reload", "reload", "recargar", "recargar configuracion"}:
            self.lifecycle.request_reload("Solicitado desde Telegram.")
            self.transport.send_message(
                chat_id,
                "Recarga solicitada. El supervisor reconstruira el runtime.",
            )
            stop = getattr(self.transport, "stop_polling", None)
            if callable(stop):
                stop()
            return True
        if command in {"/restart", "restart", "reiniciar", "reiniciar agente"}:
            self.lifecycle.request_restart("Solicitado desde Telegram.")
            self.transport.send_message(
                chat_id,
                "Reinicio solicitado. El supervisor levantara una instancia limpia.",
            )
            stop = getattr(self.transport, "stop_polling", None)
            if callable(stop):
                stop()
            return True
        if command in {"/directorios", "directorios", "listar directorios"}:
            directories = self.directories.list()
            lines = ["**Directorios permitidos**"]
            lines.extend(f"- `{path}`" for path in directories)
            if not directories:
                lines.append("- ninguno adicional")
            self.transport.send_message(chat_id, "\n".join(lines))
            return True
        if command.startswith(("anadir directorio ", "agregar directorio ")):
            raw_path = text.split(" ", 2)[-1].strip().strip('"')
            try:
                added = self.directories.add(Path(raw_path))
                self.transport.send_message(
                    chat_id,
                    f"Directorio permitido: `{added}`.",
                )
            except ValueError as exc:
                self.transport.send_message(chat_id, str(exc))
            return True
        if command.startswith(("quitar directorio ", "eliminar directorio ")):
            raw_path = text.split(" ", 2)[-1].strip().strip('"')
            removed = self.directories.remove(Path(raw_path))
            self.transport.send_message(
                chat_id,
                (
                    "Directorio eliminado."
                    if removed
                    else "Ese directorio no era una adicion persistente."
                ),
            )
            return True
        capability_markers = (
            "capacidad",
            "capacidades",
            "que puedes hacer",
            "que cosas puedes hacer",
            "que hace el tier",
            "que puede hacer el tier",
        )
        if not any(marker in command for marker in capability_markers):
            return False
        if "tier" in command or "nivel" in command:
            import re

            match = re.search(r"\b(?:tier|nivel)\s*([1-5])\b", command)
            answer = self._tier_capabilities_text(int(match.group(1))) if match else self.introspection.list_capabilities()
        else:
            answer = self.introspection.list_capabilities()
        self.transport.send_message(chat_id, answer.body)
        self._send_quota_footer(chat_id)
        return True

    def _handle_alarm_command(self, text: str, chat_id: int) -> bool:
        command = self._normalize_command(text)
        if command in {
            "listar alarmas",
            "mis alarmas",
            "listar recordatorios",
            "mis recordatorios",
        }:
            alarms = self.alarms.list_alarms(chat_id)
            if not alarms:
                self.transport.send_message(chat_id, "No hay recordatorios pendientes.")
                return True
            lines = ["**Recordatorios pendientes**"]
            for alarm in alarms:
                when = time.strftime(
                    "%d/%m/%Y %H:%M",
                    time.localtime(alarm.trigger_at),
                )
                recurrence = (
                    f", {alarm.recurrence}" if alarm.recurrence != "none" else ""
                )
                lines.append(
                    f"- `{alarm.alarm_id[:8]}` {when}{recurrence}: {alarm.message}"
                )
            self.transport.send_message(chat_id, "\n".join(lines))
            return True
        import re

        cancel = re.match(
            r"^(?:cancelar|eliminar)\s+(?:alarma|recordatorio)\s+([a-z0-9-]+)$",
            command,
        )
        if cancel:
            removed = self.alarms.cancel_alarm(cancel.group(1), chat_id=chat_id)
            self.transport.send_message(
                chat_id,
                "Recordatorio cancelado." if removed else "No encontre ese recordatorio.",
            )
            return True
        request = parse_alarm_request(text)
        if request is None:
            return False
        alarm = self.alarms.add(chat_id, request)
        when = time.strftime(
            "%d/%m/%Y %H:%M",
            time.localtime(alarm.trigger_at),
        )
        self.transport.send_message(
            chat_id,
            f"Recordatorio `{alarm.alarm_id[:8]}` guardado para {when}.",
        )
        return True

    def _handle_queue_command(self, text: str, chat_id: int) -> bool:
        command = self._normalize_command(text)
        own_tasks = [
            task
            for task in self.task_queue.list_tasks()
            if str(task.request.user_id or "") == str(chat_id)
        ]
        if command in {
            "tareas pendientes",
            "listar tareas",
            "listar tareas pendientes",
        }:
            if not own_tasks:
                self.transport.send_message(chat_id, "No hay tareas pendientes.")
                return True
            lines = ["**Tareas pendientes**"]
            for task in own_tasks:
                detail = f" ({task.pause_reason})" if task.pause_reason else ""
                lines.append(
                    f"- `{task.task_id[:8]}` {task.status}{detail}: "
                    f"{task.request.text[:120]}"
                )
            self.transport.send_message(chat_id, "\n".join(lines))
            return True
        if command in {"limpiar tareas", "limpiar tareas pendientes"}:
            removed = self.task_queue.clear_for_user(str(chat_id))
            self.transport.send_message(chat_id, f"Tareas eliminadas: {removed}.")
            return True

        import re

        action = re.match(
            r"^(continuar|reanudar|detener|cancelar)\s+tarea\s+([a-z0-9-]+)$",
            command,
        )
        if action is None:
            return False
        verb, prefix = action.groups()
        task = next(
            (item for item in own_tasks if item.task_id.startswith(prefix)),
            None,
        )
        if task is None:
            self.transport.send_message(chat_id, "No encontre esa tarea.")
            return True
        if verb in {"continuar", "reanudar"}:
            self.task_queue.resume(task.task_id)
            self.transport.send_message(chat_id, "Tarea preparada para continuar.")
        else:
            self.task_queue.mark_paused(
                task.task_id,
                reason="Detenida por el usuario.",
                status="stopped",
            )
            self.transport.send_message(chat_id, "Tarea detenida.")
        return True

    def _handle_thread_command(self, text: str, chat_id: int) -> bool:
        command = self._normalize_command(text)
        user_id = str(chat_id)
        if command in {"hilo actual", "cual es el hilo actual"}:
            self.transport.send_message(
                chat_id,
                f"Hilo actual: `{self.threads.current(user_id)}`.",
            )
            return True
        if command in {"listar hilos", "mis hilos"}:
            lines = ["**Hilos**"]
            for thread_id, display, active in self.threads.list(user_id):
                marker = " (actual)" if active else ""
                lines.append(f"- `{thread_id}`: {display}{marker}")
            self.transport.send_message(chat_id, "\n".join(lines))
            return True

        import re

        create = re.match(r"^(?:crear|nuevo)\s+hilo\s+(.+)$", command)
        if create:
            thread_id = self.threads.create(user_id, create.group(1))
            self.transport.send_message(
                chat_id,
                f"Hilo `{thread_id}` creado y activado.",
            )
            return True
        switch = re.match(
            r"^(?:cambiar a|usar|activar)\s+hilo\s+(.+)$",
            command,
        )
        if switch:
            thread_id = self.threads.switch(user_id, switch.group(1))
            self.transport.send_message(
                chat_id,
                (
                    f"Hilo `{thread_id}` activado."
                    if thread_id
                    else "No encontre ese hilo."
                ),
            )
            return True
        return False

    def _start_queue_worker(self) -> None:
        if self._queue_thread is not None and self._queue_thread.is_alive():
            return
        self._queue_stop.clear()
        self._queue_thread = threading.Thread(
            target=self._queue_worker,
            daemon=True,
            name="agent22-persistent-queue",
        )
        self._queue_thread.start()

    def _stop_queue_worker(self) -> None:
        self._queue_stop.set()
        if self._queue_thread is not None:
            self._queue_thread.join(timeout=3)

    def _queue_worker(self) -> None:
        while not self._queue_stop.wait(30):
            try:
                task = self.autonomous_scheduler.next_runnable(refresh_quota=True)
                if task is not None:
                    self._run_queued_task(task)
            except Exception:
                logger.exception("Persistent queue iteration failed")

    def _run_queued_task(self, pending_task) -> None:
        request = pending_task.request
        chat_id = int(request.user_id or request.metadata.get("telegram_chat_id") or 0)
        if not chat_id:
            self.task_queue.mark_paused(
                pending_task.task_id,
                reason="Missing Telegram chat id.",
                status="failed",
            )
            return
        contract_payload = request.metadata.get("request_contract")
        if not isinstance(contract_payload, dict):
            contract = self.contract_builder.build(
                request.text,
                attachments=request.attachments,
                metadata=request.metadata,
            )
        else:
            contract = RequestContract.model_validate(contract_payload)
        self.task_queue.mark_running(pending_task.task_id)
        resumed = request.model_copy(
            update={
                "metadata": {
                    **request.metadata,
                    "from_persistent_queue": True,
                }
            }
        )
        try:
            result = self._execute_application_request(chat_id, resumed, contract)
            self._deliver_result(chat_id, resumed, result)
            if result.ok:
                self.task_queue.mark_completed(pending_task.task_id)
            else:
                self.task_queue.mark_paused(
                    pending_task.task_id,
                    reason=result.error or "Execution failed.",
                    status="failed",
                )
        except Exception as exc:
            self.task_queue.mark_paused(
                pending_task.task_id,
                reason=str(exc),
                status="failed",
            )
            self.transport.send_message(
                chat_id,
                f"La tarea `{pending_task.task_id[:8]}` fallo y queda conservada.",
            )

    def _handle_development(self, text: str, chat_id: int) -> bool:
        from .capabilities.dev_mode import normalize_command

        command = normalize_command(text)
        if command not in {"activar modo desarrollo", "desactivar modo desarrollo"} and not self._development_is_active(chat_id):
            return False

        def send_message(target_chat_id: int | str, output: str) -> None:
            self.transport.send_message(int(target_chat_id), output)
            self._send_quota_footer(int(target_chat_id))

        def complete_implementation(target_chat_id: int | str, request_text: str, output: str, ok: bool) -> None:
            del request_text
            if output:
                self.transport.send_message(int(target_chat_id), output)
            if ok:
                self._send_quota_footer(int(target_chat_id))

        return bool(
            self.development_mode.process(
                chat_id,
                text,
                send_message=send_message,
                complete_implementation=complete_implementation,
            )
        )

    def _handle_hitl_command(self, text: str, chat_id: int) -> bool:
        command = self._normalize_command(text)
        if command in {"iniciar bateria", "iniciar bateria de pruebas"}:
            task = self.hitl.start(chat_id)
            self._launch_hitl_task(chat_id, task, "Bateria iniciada")
            return True
        if command in {"prueba siguiente", "siguiente prueba"}:
            task = self.hitl.next(chat_id)
            self._launch_hitl_task(chat_id, task, "Prueba siguiente")
            return True
        if command in {"repetir prueba", "repite la prueba"}:
            task = self.hitl.repeat(chat_id)
            self._launch_hitl_task(chat_id, task, "Repeticion")
            return True
        if command.startswith("correccion:"):
            correction = text.split(":", 1)[1].strip()
            saved = self.hitl.record_annotation(
                chat_id,
                correction=correction,
            )
            if saved:
                self.transport.send_message(chat_id, "Correccion HITL guardada.")
            return saved
        if command.startswith("friccion:"):
            friction = text.split(":", 1)[1].strip()
            saved = self.hitl.record_annotation(
                chat_id,
                friction=friction,
            )
            if saved:
                self.transport.send_message(chat_id, "Friccion HITL guardada.")
            return saved
        feedback = {
            "si": "yes",
            "sí": "yes",
            "mas o menos": "partial",
            "más o menos": "partial",
            "no": "no",
        }.get(command)
        if feedback is None:
            return False
        if not self.hitl.record_feedback(chat_id, feedback):
            return False
        self.transport.send_message(
            chat_id,
            "Valoracion guardada. Puedes añadir `correccion: ...` o "
            "`friccion: baja|media|alta`, y despues usar "
            "`prueba siguiente` o `repetir prueba`.",
        )
        return True

    def _launch_hitl_task(self, chat_id: int, task, label: str) -> None:
        trial = self.hitl.begin_trial(chat_id, task)
        self._pending_hitl_trials[chat_id] = trial
        self.transport.send_message(
            chat_id,
            f"{label}: {task.task_id}\n\n{task.prompt}",
        )
        self.handle_message(task.prompt, chat_id)

    def _development_is_active(self, chat_id: int) -> bool:
        try:
            return bool(getattr(self.development_mode, "is_active")(chat_id))
        except Exception:
            return False

    def _build_progress_callback(self, chat_id: int) -> Callable[[str, dict], None]:
        def callback(stage: str, payload: dict) -> None:
            if stage == "routed":
                decision = payload.get("decision") or {}
                tool_id = str(decision.get("tool_id", ""))
                tier = str(decision.get("tier", ""))
                seconds = self._format_seconds(float(payload.get("seconds", 0.0)))
                self.transport.send_message(
                    chat_id,
                    f"Enrutado a Tier {tier}\nModelo: {tool_id}\n{seconds}",
                )
            elif stage == "executing":
                tool_id = str(payload.get("tool_id", ""))
                self.transport.send_message(chat_id, f"Ejecutando con {tool_id}...")
            elif stage == "fallback":
                self.transport.send_message(
                    chat_id,
                    (
                        f"{payload.get('from_tool', '')} no esta disponible. "
                        f"Continuo con {payload.get('tool_id', '')}..."
                    ),
                )

        return callback

    def _deliver_result(self, chat_id: int, request: TaskRequest, result: OrchestratorResult) -> None:
        if not result.ok:
            self.transport.send_message(chat_id, self._friendly_error(result))
            self._send_quota_footer(chat_id)
            return

        if result.output:
            elapsed = result.timings.execution_seconds if result.timings else result.elapsed_seconds
            self.transport.send_message(chat_id, f"{result.output}\n\n{self._format_seconds(elapsed)}")
        else:
            elapsed = result.timings.execution_seconds if result.timings else result.elapsed_seconds
            self.transport.send_message(chat_id, self._format_seconds(elapsed))

        self.mailbox.append_inbox(request.request_id, request.text, chat_id=chat_id)
        self.mailbox.append_outbox(request.request_id, result.output or result.error or "", chat_id=chat_id)
        self._deliver_voice_if_enabled(chat_id, request, result)
        self._send_quota_footer(chat_id)

    def _deliver_voice_if_enabled(
        self,
        chat_id: int,
        request: TaskRequest,
        result: OrchestratorResult,
    ) -> None:
        preferences = self.preferences.load()
        if not preferences.voice_enabled or not result.output.strip():
            return
        started = time.monotonic()
        try:
            summary = self.voice.summarize_for_voice(result.output, request.text)
            audio_root = self.workspace_root / "voice" / str(chat_id)
            audio_path = self.voice.synthesize_voice(
                summary,
                audio_root / f"{request.request_id}.mp3",
                provider=preferences.voice_provider,
                voice_name=preferences.voice_name,
            )
            self.transport.send_audio(chat_id, audio_path, caption="Resumen de audio")
            if preferences.speaker_enabled:
                self.voice.play_audio_file(audio_path)
            if result.timings:
                result.timings.voice_seconds = time.monotonic() - started
        except Exception as exc:
            logger.warning("Voice delivery failed: %s", exc)
            self.transport.send_message(
                chat_id,
                "La respuesta de texto esta completa, pero no pude generar el audio.",
            )

    def _handle_confirmation_reply(self, text: str, chat_id: int) -> bool:
        pending = self.confirmations.get(chat_id)
        if pending is None:
            return False
        if is_confirmation_no(text):
            self.confirmations.clear(chat_id)
            self.transport.send_message(chat_id, "Accion cancelada.")
            return True
        if not is_confirmation_yes(text):
            self.transport.send_message(
                chat_id,
                "Hay una accion pendiente. Responde `si` o `no`.",
            )
            return True

        self.confirmations.clear(chat_id)
        request = TaskRequest.model_validate(pending["request"])
        request.metadata["human_confirmation_approved"] = True
        contract = RequestContract.model_validate(pending["contract"])
        result = self._execute_application_request(chat_id, request, contract)
        self._deliver_result(chat_id, request, result)
        return True

    def _execute_application_request(
        self,
        chat_id: int,
        request: TaskRequest,
        contract: RequestContract,
    ) -> OrchestratorResult:
        cancel = getattr(self.execution_engine, "cancel", None)
        if callable(cancel):
            self.cancellations.register(str(chat_id), request.request_id, cancel)
        try:
            return self.application.handle(
                request,
                contract,
                progress_callback=self._build_progress_callback(chat_id),
            )
        finally:
            self.cancellations.clear_owner(str(chat_id), request.request_id)

    def _handle_cancellation_command(self, text: str, chat_id: int) -> bool:
        command = self._normalize_command(text)
        if command not in {
            "cancelar operacion",
            "cancelar ejecucion",
            "detener operacion",
            "/cancelar",
        }:
            return False
        cancelled = self.cancellations.cancel_owner(str(chat_id))
        self.transport.send_message(
            chat_id,
            (
                "Cancelacion enviada a la operacion activa."
                if cancelled
                else "No hay una operacion cancelable activa."
            ),
        )
        return True

    def _send_quota_footer(self, chat_id: int) -> None:
        footer = self.quota_monitor.get_footer()
        if footer:
            self.transport.send_message(chat_id, footer)

    def _handle_transport_progress(self, chat_id: int, stage: str) -> None:
        del chat_id, stage

    def _friendly_error(self, result: OrchestratorResult) -> str:
        error = (result.error or result.output).casefold()
        if "invalid api key" in error or "401" in error or "unauthorized" in error:
            return "El proveedor seleccionado no tiene una clave valida. He registrado el fallo; prueba de nuevo en unos segundos."
        if "429" in error or "rate limit" in error:
            return "El proveedor esta temporalmente saturado. Prueba de nuevo dentro de un momento."
        if "timeout" in error or "timed out" in error:
            return "La peticion tardo demasiado y se cancelo. Prueba otra vez con una instruccion mas corta."
        return "No he podido completar la peticion. El detalle tecnico quedo guardado en el registro."

    def _normalize_command(self, text: str) -> str:
        import unicodedata

        normalized = unicodedata.normalize("NFKD", (text or "").casefold())
        without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
        return " ".join(without_accents.strip().split()).strip(" .,!¡?¿")

    def _format_seconds(self, seconds: float) -> str:
        if seconds < 1:
            value = max(0.1, round(seconds, 1))
            return f"{value:g}s"
        return f"{round(seconds):d}s"

    def _tier_capabilities_text(self, tier: int):
        from .capabilities.introspection import IntrospectionAnswer

        descriptions = {
            1: "logica local y control: estado, capacidades, memoria relevante, confirmaciones y comandos del sistema",
            2: "modelos API rapidos para conversacion, redaccion, resumen y razonamiento corto",
            3: "investigacion web con fuentes, informacion actual, analisis mas profundo y archivos de contexto medio",
            4: "trabajo agencial: codigo, terminal, cambios de repositorio, Codex CLI y contextos documentales grandes",
            5: "Codex Desktop para navegador, interfaces visuales, sesiones autenticadas, mapas, clics y capturas",
        }
        body = descriptions.get(tier, "No tengo una descripcion concreta para ese tier.")
        return IntrospectionAnswer(title=f"tier-{tier}", body=f"Tier {tier}: {body}.")

    def _default_development_mode(self):
        try:
            from .capabilities.dev_mode import DevelopmentModeController

            return DevelopmentModeController(
                project_root=Path(__file__).resolve().parents[3],
                quota_monitor=self.quota_monitor,
            )
        except Exception:
            logger.exception("Development mode controller unavailable")
            return _NullDevelopmentModeController()

    def _default_selector(self) -> CapabilitySelector:
        state_path = self.workspace_root / "evolution_state.json"
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            state = {}
        if bool(state.get("active")):
            return EvolutionarySelector(experience_store=self.experience_store)
        return CapabilitySelector()


class _NullDevelopmentModeController:
    def is_active(self, chat_id: int | str) -> bool:
        del chat_id
        return False

    def process(self, chat_id: int | str, text: str, *, send_message, complete_implementation) -> bool:
        del chat_id, text, send_message, complete_implementation
        return False
