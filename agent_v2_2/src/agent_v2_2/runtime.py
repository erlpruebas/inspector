from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Callable, Optional

from .application import AgentApplication
from .capabilities.introspection import IntrospectionManager
from .capabilities.memory import MemoryStore
from .capabilities.preferences import PreferenceStore
from .capabilities.status import StatusManager
from .capabilities.voice import VoiceCapabilities
from .config import load_config
from .engines.codex_desktop import CodexDesktopOperator
from .engines.execution import ExecutionEngine
from .engines.workspace import WorkspaceManager
from .models import Attachment, OrchestratorResult, RouteDecision, TaskRequest
from .routing.builder import ContractBuilder
from .routing.contract import RequestContract
from .routing.executor import execute_local_command
from .routing.selector import CapabilitySelector
from .scheduling.codex_quota import CodexQuotaMonitor
from .transport import TelegramTransport
from .transport.queue import ExecutionMailbox
from .evolution.experience import ExperienceStore
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
    ) -> None:
        config = load_config()
        self.config = config
        self.workspace_root = config.workspace_root.resolve()
        self.transport = transport or TelegramTransport(config)
        self.selector = selector or CapabilitySelector()
        self.contract_builder = contract_builder or ContractBuilder()
        self.workspace_manager = workspace_manager or WorkspaceManager(self.workspace_root)
        self.execution_engine = execution_engine or ExecutionEngine(self.workspace_manager)
        self.codex_desktop = codex_desktop or CodexDesktopOperator()
        self.voice = voice or VoiceCapabilities()
        self.memory_store = memory_store or MemoryStore()
        self.experience_store = experience_store or ExperienceStore()
        self.quota_monitor = quota_monitor or CodexQuotaMonitor()
        self.status_manager = status_manager or StatusManager()
        self.introspection = introspection or IntrospectionManager()
        self.mailbox = mailbox or ExecutionMailbox()
        self.lifecycle = lifecycle or LifecycleManager()
        self.metrics = metrics or MetricsRecorder()
        self.preferences = PreferenceStore()
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
        self.transport.start_polling()

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
            prepared_text,
            attachments=attachments,
            metadata={
                "telegram_chat_id": chat_id,
                "telegram_media_type": media_type or "",
                "telegram_source": source_metadata.get("source", "text"),
            },
        )
        result = self.application.handle(
            request,
            contract,
            progress_callback=self._build_progress_callback(chat_id),
        )
        self._deliver_result(chat_id, request, result)

    def execute_request(self, request: TaskRequest, decision: RouteDecision) -> OrchestratorResult:
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
        return TaskRequest(
            user_id=str(chat_id),
            thread_id=str(chat_id),
            text=text,
            attachments=attachments,
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
        if command in {"estado", "/estado", "status", "/status", "estado del sistema"}:
            self.transport.send_message(chat_id, self.status_manager.generate_status_report())
            self._send_quota_footer(chat_id)
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

    def _handle_development(self, text: str, chat_id: int) -> bool:
        command = self._normalize_command(text)
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
        self._send_quota_footer(chat_id)

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
            from .development_mode import DevelopmentModeController

            return DevelopmentModeController()
        except Exception:
            logger.exception("Development mode controller unavailable")
            return _NullDevelopmentModeController()


class _NullDevelopmentModeController:
    def is_active(self, chat_id: int | str) -> bool:
        del chat_id
        return False

    def process(self, chat_id: int | str, text: str, *, send_message, complete_implementation) -> bool:
        del chat_id, text, send_message, complete_implementation
        return False
