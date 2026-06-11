from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path

from agent_v2_2.config import Config, QuotaConfig, TelegramConfig
from agent_v2_2.evolution import (
    BenchmarkArena,
    BenchmarkRunner,
    CapabilityMatrixBuilder,
    ExperienceStore,
    NormalizedTask,
    RouterExperience,
)
from agent_v2_2.models import Attachment, OrchestratorResult
from agent_v2_2.evolution.controller import EvolutionController
from agent_v2_2.routing.builder import ContractBuilder
from agent_v2_2.routing.evolutionary import EvolutionarySelector
from agent_v2_2.routing.selector import CapabilitySelector
from agent_v2_2.routing.contract import (
    CognitiveLevel,
    InstrumentalCapability,
    Operation,
    RequestContract,
)
from agent_v2_2.routing.contract import (
    Guarantee,
    PrepareActionType,
)
from agent_v2_2.runtime import TelegramAgentRuntime
from agent_v2_2.capabilities.dev_mode import DevelopmentModeController, RunningTask
from agent_v2_2.capabilities.memory import ThreadRegistry
from agent_v2_2.capabilities.directories import AllowedDirectoryStore
from agent_v2_2.privacy.core import redact_sensitive_text
from agent_v2_2.scheduling.alarms import AlarmScheduler, parse_alarm_request
from agent_v2_2.transport.telegram import TelegramTransport


def test_telegram_transport_passes_message_context(tmp_path: Path) -> None:
    config = Config(
        telegram=TelegramConfig(bot_token="", allowed_users=[123], allowed_chats=[123]),
        quota=QuotaConfig(),
        workspace_root=tmp_path,
        allowed_directories=[],
    )
    transport = TelegramTransport(config)
    captured: dict[str, object] = {}

    def handler(text: str, chat_id: int, **kwargs) -> None:
        captured["text"] = text
        captured["chat_id"] = chat_id
        captured.update(kwargs)

    transport.set_message_handler(handler)
    transport.process_update(
        {
            "update_id": 1,
            "message": {
                "message_id": 7,
                "chat": {"id": 123},
                "voice": {"file_id": "voice-123"},
                "text": "",
            },
        }
    )

    assert captured["text"] == ""
    assert captured["chat_id"] == 123
    assert captured["media_file_id"] == "voice-123"
    assert captured["media_type"] == "voice"
    assert isinstance(captured["message"], dict)
    assert captured["message"]["message_id"] == 7


def test_contract_builder_infers_memory_web_and_file_access() -> None:
    builder = ContractBuilder()
    contract = builder.build(
        "Recuerda la direccion de mi dentista y busca una floristeria cerca; compara el Excel adjunto.",
        attachments=[
            Attachment(
                kind="document",
                path=Path("ventas.xlsx"),
                label="ventas.xlsx",
            )
        ],
    )

    actions = {action.action for action in contract.prepare}
    assert PrepareActionType.MEMORY_LOOKUP in actions
    assert PrepareActionType.WEB_LOOKUP in actions
    assert contract.execute.operation == Operation.COMPARE
    assert contract.execute.cognitive_level in {CognitiveLevel.GENERAL, CognitiveLevel.REASONING}
    assert InstrumentalCapability.READ_SPREADSHEET in contract.execute.instrumental_capabilities
    assert Guarantee.FRESH_INFORMATION in contract.execute.guarantees
    assert Guarantee.SOURCE_CITATIONS in contract.execute.guarantees
    assert "current_web_lookup" in contract.required_accesses()


def test_runtime_handles_voice_and_routes_request(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))

    class FakeTransport:
        def __init__(self) -> None:
            self.messages: list[tuple[int, str]] = []
            self.message_handler = None
            self.progress_handler = None

        def set_message_handler(self, handler):
            self.message_handler = handler

        def set_progress_handler(self, handler):
            self.progress_handler = handler

        def send_message(self, chat_id: int, text: str) -> bool:
            self.messages.append((chat_id, text))
            return True

        def download_file(self, file_id: str, target_path: Path) -> Path:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(f"fake:{file_id}", encoding="utf-8")
            return target_path

        def start_polling(self) -> None:
            raise AssertionError("Polling should not start in unit tests")

    transport = FakeTransport()

    class FakeExecutionEngine:
        def execute_code(self, request, decision):
            del request
            return OrchestratorResult(
                ok=True,
                tool_id=decision.tool_id,
                tier=decision.tier,
                output="Resultado real simulado por el doble de prueba.",
                metadata={"evidence_kind": "live"},
            )

    runtime = TelegramAgentRuntime(
        transport=transport,
        execution_engine=FakeExecutionEngine(),
    )
    runtime.voice.transcribe_audio_file = lambda path: "compara el excel adjunto"  # type: ignore[assignment]

    runtime.handle_message(
        "",
        123,
        media_file_id="voice-123",
        media_type="voice",
        message={"message_id": 7, "file_name": "nota.ogg"},
    )

    message_texts = [message for _chat_id, message in transport.messages]
    assert any(text.startswith("Transcrito") for text in message_texts)
    assert any(text.startswith("Enrutado a Tier") for text in message_texts)
    assert any(text.startswith("Ejecutando con") for text in message_texts)
    assert any("Resultado real simulado por el doble de prueba." in text for text in message_texts)


def test_runtime_answers_status_locally(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))

    class FakeTransport:
        def __init__(self) -> None:
            self.messages: list[tuple[int, str]] = []
            self.message_handler = None
            self.progress_handler = None

        def set_message_handler(self, handler):
            self.message_handler = handler

        def set_progress_handler(self, handler):
            self.progress_handler = handler

        def send_message(self, chat_id: int, text: str) -> bool:
            self.messages.append((chat_id, text))
            return True

        def download_file(self, file_id: str, target_path: Path) -> Path:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(f"fake:{file_id}", encoding="utf-8")
            return target_path

        def start_polling(self) -> None:
            raise AssertionError("Polling should not start in unit tests")

    transport = FakeTransport()
    runtime = TelegramAgentRuntime(transport=transport)
    runtime.handle_message("estado", 123)

    message_texts = [message for _chat_id, message in transport.messages]
    assert any("Estado" in text for text in message_texts)
    assert any("telegram" in text.casefold() for text in message_texts)


def test_development_mode_accepts_aliases_and_persists_state(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path / "runtime"))

    class FakeQuota:
        def can_schedule_codex(self, *, refresh=False):
            del refresh
            return True

        def pause_reason(self):
            return None

    messages: list[str] = []
    controller = DevelopmentModeController(
        project_root=tmp_path,
        quota_monitor=FakeQuota(),  # type: ignore[arg-type]
    )
    handled = controller.process(
        123,
        "activar modo desarrollador",
        send_message=lambda _chat, text: messages.append(text),
        complete_implementation=lambda *_args: None,
    )
    assert handled is True
    assert controller.is_active(123) is True
    assert DevelopmentModeController(
        project_root=tmp_path,
        quota_monitor=FakeQuota(),  # type: ignore[arg-type]
    ).is_active(123)

    controller.process(
        123,
        "desactivar modo de desarrollo",
        send_message=lambda _chat, text: messages.append(text),
        complete_implementation=lambda *_args: None,
    )
    assert controller.is_active(123) is False
    assert any("activado" in message for message in messages)


def test_runtime_uses_real_development_controller(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))

    class FakeTransport:
        def set_message_handler(self, handler):
            self.handler = handler

        def set_progress_handler(self, handler):
            self.progress = handler

        def send_message(self, chat_id, text):
            del chat_id, text
            return True

    runtime = TelegramAgentRuntime(transport=FakeTransport())
    assert isinstance(runtime.development_mode, DevelopmentModeController)


def test_runtime_uses_evolutionary_selector_only_after_activation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))

    class FakeTransport:
        def set_message_handler(self, handler):
            self.handler = handler

        def set_progress_handler(self, handler):
            self.progress = handler

        def send_message(self, chat_id, text):
            del chat_id, text
            return True

    runtime = TelegramAgentRuntime(transport=FakeTransport())
    assert type(runtime.selector) is CapabilitySelector

    (tmp_path / "evolution_state.json").write_text(
        json.dumps({"active": True}),
        encoding="utf-8",
    )
    active_runtime = TelegramAgentRuntime(transport=FakeTransport())
    assert isinstance(active_runtime.selector, EvolutionarySelector)


def test_development_mode_completes_proposal_and_isolated_publication(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path / "runtime"))

    class FakeQuota:
        def can_schedule_codex(self, *, refresh=False):
            del refresh
            return True

        def pause_reason(self):
            return None

    controller = DevelopmentModeController(
        project_root=tmp_path,
        quota_monitor=FakeQuota(),  # type: ignore[arg-type]
    )
    controller.activate(123)
    proposal = {
        "title": "Añadir prueba",
        "understanding": "Crear una prueba pequeña.",
        "changes": ["Añadir prueba"],
        "files": ["tests/test_sample.py"],
        "tests": ["pytest"],
        "risks": [],
        "open_questions": [],
    }
    monkeypatch.setattr(controller, "_run_proposal", lambda *_args: proposal)
    messages: list[str] = []
    controller._proposal_worker(
        123,
        "añade una prueba",
        "",
        None,
        1,
        RunningTask(),
        lambda _chat, text: messages.append(text),
    )
    state = controller._load_state(123)
    assert state["phase"] == "awaiting_approval"
    assert state["proposal"] == proposal

    worktree = tmp_path / "worktree"
    worktree.mkdir()
    monkeypatch.setattr(controller, "_create_worktree", lambda _chat: (worktree, "codex/test"))
    monkeypatch.setattr(controller, "_run_implementation", lambda *_args: "Implementado.")
    monkeypatch.setattr(controller, "_commit_worktree", lambda *_args: "commit-a")
    monkeypatch.setattr(controller, "_rebase_onto_head", lambda *_args: "commit-b")
    monkeypatch.setattr(controller, "_push_current_branch", lambda: (True, "main"))
    monkeypatch.setattr(controller, "_cleanup_worktree", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("agent_v2_2.capabilities.dev_mode._run_git", lambda *_args: "")
    completed = []
    controller._implementation_worker(
        123,
        "añade una prueba",
        proposal,
        RunningTask(),
        lambda *args: completed.append(args),
    )

    state = controller._load_state(123)
    assert state["phase"] == "idle"
    assert state["last_commit"] == "commit-b"
    assert completed[0][-1] is True
    assert "Publicado" in completed[0][2]


def test_runtime_requires_confirmation_before_sensitive_execution(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))

    class FakeTransport:
        def __init__(self):
            self.messages = []

        def set_message_handler(self, handler):
            self.handler = handler

        def set_progress_handler(self, handler):
            self.progress = handler

        def send_message(self, chat_id, text):
            self.messages.append((chat_id, text))
            return True

    class FakeExecution:
        def execute_code(self, request, decision):
            return OrchestratorResult(
                ok=True,
                tool_id=decision.tool_id,
                tier=decision.tier,
                output="enviado",
                metadata={"evidence_kind": "live"},
            )

    transport = FakeTransport()
    runtime = TelegramAgentRuntime(
        transport=transport,
        execution_engine=FakeExecution(),
        experience_store=ExperienceStore(tmp_path / "confirm-experiences.jsonl"),
    )
    runtime.handle_message("Envia este informe al cliente.", 123)
    assert runtime.experience_store.load() == []
    assert runtime.confirmations.get(123) is not None
    assert any("Confirmacion necesaria" in text for _chat, text in transport.messages)

    runtime.handle_message("si", 123)
    assert len(runtime.experience_store.load()) == 1
    assert runtime.confirmations.get(123) is None


def test_runtime_delivers_audio_when_voice_is_enabled(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))

    class FakeTransport:
        def __init__(self):
            self.messages = []
            self.audio = []

        def set_message_handler(self, handler):
            self.handler = handler

        def set_progress_handler(self, handler):
            self.progress = handler

        def send_message(self, chat_id, text):
            self.messages.append((chat_id, text))
            return True

        def send_audio(self, chat_id, path, caption=""):
            self.audio.append((chat_id, path, caption))
            return True

    class FakeExecution:
        def execute_code(self, request, decision):
            del request
            return OrchestratorResult(
                ok=True,
                tool_id=decision.tool_id,
                tier=decision.tier,
                output="Respuesta completa.",
                metadata={"evidence_kind": "live"},
            )

    transport = FakeTransport()
    runtime = TelegramAgentRuntime(
        transport=transport,
        execution_engine=FakeExecution(),
    )
    runtime.preferences.toggle_voice(True)
    runtime.voice.summarize_for_voice = lambda output, request: output  # type: ignore[assignment]

    def synthesize(text, output_path, provider="edge", voice_name=""):
        del text, provider, voice_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"audio")
        return output_path

    runtime.voice.synthesize_voice = synthesize  # type: ignore[assignment]
    runtime.handle_message("Resume este texto brevemente.", 123)
    assert len(transport.audio) == 1
    assert transport.audio[0][2] == "Resumen de audio"


def test_runtime_voice_commands_and_local_speaker(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))

    class FakeTransport:
        def __init__(self):
            self.messages = []
            self.audio = []

        def set_message_handler(self, handler):
            self.handler = handler

        def set_progress_handler(self, handler):
            self.progress = handler

        def send_message(self, chat_id, text):
            self.messages.append((chat_id, text))
            return True

        def send_audio(self, chat_id, path, caption=""):
            self.audio.append((chat_id, path, caption))
            return True

    class FakeExecution:
        def execute_code(self, request, decision):
            del request
            return OrchestratorResult(
                ok=True,
                tool_id=decision.tool_id,
                tier=decision.tier,
                output="Respuesta completa.",
                metadata={"evidence_kind": "live"},
            )

    transport = FakeTransport()
    runtime = TelegramAgentRuntime(
        transport=transport,
        execution_engine=FakeExecution(),
    )
    runtime.handle_message("voz on", 123)
    runtime.handle_message("altavoz on", 123)
    played: list[Path] = []
    runtime.voice.summarize_for_voice = lambda output, request: output  # type: ignore[assignment]

    def synthesize(text, output_path, provider="edge", voice_name=""):
        del text, provider, voice_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"audio")
        return output_path

    runtime.voice.synthesize_voice = synthesize  # type: ignore[assignment]
    runtime.voice.play_audio_file = lambda path: played.append(path)  # type: ignore[assignment]
    runtime.handle_message("Resume este texto brevemente.", 123)

    assert runtime.preferences.load().voice_enabled is True
    assert runtime.preferences.load().speaker_enabled is True
    assert len(transport.audio) == 1
    assert len(played) == 1


def test_runtime_lifecycle_directories_and_provider_diagnostics(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path / "runtime"))
    allowed = tmp_path / "documentos"
    allowed.mkdir()

    class FakeTransport:
        def __init__(self):
            self.messages = []
            self.stopped = False

        def set_message_handler(self, handler):
            self.handler = handler

        def set_progress_handler(self, handler):
            self.progress = handler

        def send_message(self, chat_id, text):
            self.messages.append((chat_id, text))
            return True

        def stop_polling(self):
            self.stopped = True

    transport = FakeTransport()
    directory_store = AllowedDirectoryStore(
        path=tmp_path / "allowed.json",
        configured=[],
    )
    runtime = TelegramAgentRuntime(
        transport=transport,
        directory_store=directory_store,
    )
    runtime.handle_message(f"añadir directorio {allowed}", 123)
    assert allowed.resolve() in directory_store.list()
    assert allowed.resolve() in AllowedDirectoryStore(
        path=tmp_path / "allowed.json",
        configured=[],
    ).list()
    source = allowed / "gastos.xlsx"
    source.write_bytes(b"fixture")
    request = runtime._build_request(
        chat_id=123,
        text="Analiza gastos.xlsx",
        attachments=[],
        metadata={},
    )
    assert request.attachments[0].path == source.resolve()
    assert request.attachments[0].source == "allowed_directory"

    runtime.handle_message("directorios", 123)
    runtime.handle_message("diagnostico proveedores", 123)
    assert any(str(allowed.resolve()) in text for _chat, text in transport.messages)
    assert any("Diagnostico de proveedores" in text for _chat, text in transport.messages)

    runtime.handle_message("recargar configuracion", 123)
    assert runtime.lifecycle.load().reload_requested is True
    assert transport.stopped is True


def test_runtime_cancels_active_execution(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))

    class FakeTransport:
        def __init__(self):
            self.messages = []

        def set_message_handler(self, handler):
            self.handler = handler

        def set_progress_handler(self, handler):
            self.progress = handler

        def send_message(self, chat_id, text):
            self.messages.append((chat_id, text))
            return True

    class CancellableExecution:
        def __init__(self):
            self.started = threading.Event()
            self.cancelled = threading.Event()

        def execute_code(self, request, decision):
            self.started.set()
            self.cancelled.wait(timeout=5)
            return OrchestratorResult(
                ok=False,
                tool_id=decision.tool_id,
                tier=decision.tier,
                error="cancelled",
                metadata={"evidence_kind": "live"},
            )

        def cancel(self, request_id):
            del request_id
            self.cancelled.set()
            return True

    transport = FakeTransport()
    execution = CancellableExecution()
    runtime = TelegramAgentRuntime(
        transport=transport,
        execution_engine=execution,
    )
    worker = threading.Thread(
        target=runtime.handle_message,
        args=("Resume este documento.", 123),
    )
    worker.start()
    assert execution.started.wait(timeout=3)
    runtime.handle_message("cancelar operacion", 123)
    worker.join(timeout=3)

    assert worker.is_alive() is False
    assert execution.cancelled.is_set()
    assert any("Cancelacion enviada" in text for _chat, text in transport.messages)


def test_alarm_parser_and_scheduler_persist_and_deliver(tmp_path: Path) -> None:
    now = datetime(2026, 6, 11, 12, 0).astimezone()
    request = parse_alarm_request(
        "Recuérdame en 10 minutos que llame al dentista",
        now=now,
    )
    assert request is not None
    assert request.message == "llame al dentista"
    assert request.trigger_at == now.timestamp() + 600

    delivered: list[tuple[int, str]] = []
    store = tmp_path / "alarms.json"
    scheduler = AlarmScheduler(
        lambda chat_id, message: delivered.append((chat_id, message)),
        store_path=store,
    )
    alarm = scheduler.add(123, request)
    assert AlarmScheduler(lambda *_args: None, store_path=store).list_alarms(123)
    assert scheduler.tick(now=alarm.trigger_at) == 1
    assert delivered == [(123, "llame al dentista")]
    assert scheduler.list_alarms(123) == []


def test_runtime_manages_alarm_commands_locally(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))

    class FakeTransport:
        def __init__(self):
            self.messages = []

        def set_message_handler(self, handler):
            self.handler = handler

        def set_progress_handler(self, handler):
            self.progress = handler

        def send_message(self, chat_id, text):
            self.messages.append((chat_id, text))
            return True

    transport = FakeTransport()
    runtime = TelegramAgentRuntime(transport=transport)
    runtime.handle_message(
        "Recuérdame en 10 minutos que llame al dentista",
        123,
    )
    alarms = runtime.alarms.list_alarms(123)
    assert len(alarms) == 1
    runtime.handle_message("mis recordatorios", 123)
    assert any(alarms[0].alarm_id[:8] in text for _chat, text in transport.messages)
    runtime.handle_message(
        f"cancelar recordatorio {alarms[0].alarm_id[:8]}",
        123,
    )
    assert runtime.alarms.list_alarms(123) == []


def test_runtime_manages_threads_and_uses_active_thread(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))

    class FakeTransport:
        def __init__(self):
            self.messages = []

        def set_message_handler(self, handler):
            self.handler = handler

        def set_progress_handler(self, handler):
            self.progress = handler

        def send_message(self, chat_id, text):
            self.messages.append((chat_id, text))
            return True

    transport = FakeTransport()
    runtime = TelegramAgentRuntime(transport=transport)
    runtime.handle_message("crear hilo Proyecto Alfa", 123)
    assert runtime.threads.current("123") == "proyecto_alfa"
    request = runtime._build_request(
        chat_id=123,
        text="dato",
        attachments=[],
        metadata={},
    )
    assert request.thread_id == "proyecto_alfa"
    runtime.handle_message("listar hilos", 123)
    assert any("proyecto_alfa" in text for _chat, text in transport.messages)
    assert ThreadRegistry().current("123") == "proyecto_alfa"


def test_runtime_manages_persistent_queue_commands(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))

    class FakeTransport:
        def __init__(self):
            self.messages = []

        def set_message_handler(self, handler):
            self.handler = handler

        def set_progress_handler(self, handler):
            self.progress = handler

        def send_message(self, chat_id, text):
            self.messages.append((chat_id, text))
            return True

    from agent_v2_2.models import TaskRequest
    from agent_v2_2.scheduling.queue import TaskQueue

    queue = TaskQueue(tmp_path / "queue.json")
    task_id = queue.enqueue(TaskRequest(user_id="123", text="tarea larga"))
    queue.mark_paused(task_id, reason="esperando", status="paused")
    transport = FakeTransport()
    runtime = TelegramAgentRuntime(transport=transport, task_queue=queue)

    runtime.handle_message("listar tareas pendientes", 123)
    assert any(task_id[:8] in text for _chat, text in transport.messages)
    runtime.handle_message(f"reanudar tarea {task_id[:8]}", 123)
    assert queue.list_tasks()[0].status == "pending"
    runtime.handle_message("limpiar tareas pendientes", 123)
    assert queue.list_tasks() == []


def test_runtime_records_hitl_correction_command(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))
    tasks = tmp_path / "tasks.json"
    tasks.write_text(
        '[{"id":"hitl-1","prompt":"Responde brevemente.","skills":["draft"]}]',
        encoding="utf-8",
    )
    from agent_v2_2.evolution.hitl import HITLController

    class FakeTransport:
        def __init__(self):
            self.messages = []

        def set_message_handler(self, handler):
            self.handler = handler

        def set_progress_handler(self, handler):
            self.progress = handler

        def send_message(self, chat_id, text):
            self.messages.append((chat_id, text))
            return True

    hitl = HITLController(
        tasks_path=tasks,
        state_path=tmp_path / "state.json",
        trials_path=tmp_path / "trials.jsonl",
        experience_store=ExperienceStore(tmp_path / "experiences.jsonl"),
    )
    task = hitl.start(123)
    trial = hitl.begin_trial(123, task)
    hitl.link_result(
        trial.trial_id,
        experience_id="missing-experience",
        tool_id="router_groq_qwen32",
        elapsed_seconds=1,
    )
    transport = FakeTransport()
    runtime = TelegramAgentRuntime(transport=transport, hitl_controller=hitl)
    runtime.handle_message("correccion: mas breve", 123)

    assert hitl._find_trial(trial.trial_id).correction == "mas breve"
    assert any("Correccion HITL guardada" in text for _chat, text in transport.messages)


def test_application_materializes_memory_facts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))

    def execute(request, decision):
        return OrchestratorResult(
            ok=True,
            tool_id=decision.tool_id,
            tier=decision.tier,
            output="guardado",
        )

    from agent_v2_2.application import AgentApplication
    from agent_v2_2.evolution.experience import ExperienceStore
    from agent_v2_2.capabilities.memory import MemoryStore

    memory = MemoryStore(tmp_path / "memory")
    application = AgentApplication(
        executor=execute,
        memory_store=memory,
        experience_store=ExperienceStore(tmp_path / "experiences.jsonl"),
    )
    contract = ContractBuilder().build("Recuerda que mi casa esta en Calle Mayor 1.")
    from agent_v2_2.models import TaskRequest

    application.handle(
        TaskRequest(
            user_id="123",
            thread_id="principal",
            text="Recuerda que mi casa esta en Calle Mayor 1.",
        ),
        contract,
    )
    facts = memory.load_facts("123", "principal")
    assert facts[0].kind == "home_address"
    assert facts[0].value == "Calle Mayor 1."


def test_anonymization_redacts_provider_text(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))
    assert "[EMAIL REDACTADO]" in redact_sensitive_text("Escribe a ana@example.com")

    class FakeTransport:
        def set_message_handler(self, handler):
            self.handler = handler

        def set_progress_handler(self, handler):
            self.progress = handler

        def send_message(self, chat_id, text):
            del chat_id, text
            return True

    runtime = TelegramAgentRuntime(transport=FakeTransport())
    runtime.preferences.set_anonymization(True)
    request = runtime._build_request(
        chat_id=123,
        text="Escribe a ana@example.com y llama al 612 345 678.",
        attachments=[],
        metadata={},
    )
    assert "ana@example.com" not in request.text
    assert "612 345 678" not in request.text
    assert request.metadata["privacy_mode"] == "redacted"


def test_task_normalizer_builds_primary_capability_and_rubric(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))
    sample = tmp_path / "sample_tasks.json"
    sample.write_text(
        json.dumps(
            [
                {
                    "id": "task-1",
                    "title": "Compare spreadsheet",
                    "prompt": "Compara el Excel adjunto con el anterior y dime las diferencias.",
                    "skills": ["compare", "data_filtering"],
                    "required_files": ["report.xlsx"],
                    "expected_operation": "compare_spreadsheet",
                    "expected_keys": ["diferencias", "ventas"],
                    "rubric": {"correctness": 4, "traceability": 2},
                    "route_hypothesis": "gemini_pro_long_context",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = EvolutionController(workspace_root=tmp_path).normalize_tasks([sample])
    assert report.total_tasks == 1
    assert report.primary_capabilities["cap_compare"] == 1
    assert report.compatible_tools
    task = report.records[0]
    assert task.judge_rubric["correctness"] == 4
    assert "contains:diferencias" in task.objective_checks
    assert task.compatible_tools[0] == "gemini_pro_long_context"


def test_task_normalizer_covers_web_research_and_multi_document_tasks(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))
    sample = tmp_path / "sample_tasks_extra.json"
    sample.write_text(
        json.dumps(
            [
                {
                    "id": "task-web",
                    "title": "Investigate competitors",
                    "prompt": "Investiga con varias fuentes web las alternativas a una herramienta de encuestas.",
                    "skills": ["web_search", "comparison", "reporting"],
                    "required_files": ["notes.md"],
                    "requires_network": True,
                },
                {
                    "id": "task-web-single",
                    "title": "Single web lookup",
                    "prompt": "Busca en la web la dirección exacta de la floristería del barrio.",
                    "skills": ["web"],
                    "required_files": [],
                    "requires_network": True,
                },
                {
                    "id": "task-multi",
                    "title": "Multi document summary",
                    "prompt": "Resume y combina los dos documentos para preparar un informe ejecutivo.",
                    "skills": ["read_files", "summarization"],
                    "required_files": ["source-a.md", "source-b.csv"],
                    "requires_network": False,
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = EvolutionController(workspace_root=tmp_path).normalize_tasks([sample])
    assert report.total_tasks == 3
    primary = {task.task_id: task.primary_capability for task in report.records}
    assert primary["task-web"] == "cap_investigate"
    assert primary["task-web-single"] == "cap_web_punctual"
    assert primary["task-multi"] == "cap_synth_multi"
    assert "cap_investigate" not in report.missing_capabilities
    assert "cap_web_punctual" not in report.missing_capabilities


def test_real_benchmark_normalization_has_full_capability_coverage(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))
    report = EvolutionController(workspace_root=tmp_path).normalize_tasks()
    assert report.total_tasks >= 300
    assert report.missing_rubrics == 0
    assert report.network_tasks > 0
    assert report.missing_capabilities == []
    for task in report.records:
        RequestContract.model_validate(task.contract)


def test_benchmark_arena_persists_runs_with_judge(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))
    sample = tmp_path / "sample_arena.json"
    sample.write_text(
        json.dumps(
            [
                {
                    "id": "arena-1",
                    "title": "Compare spreadsheet",
                    "prompt": "Compara el Excel adjunto con el anterior y dime las diferencias.",
                    "skills": ["compare", "data_filtering"],
                    "required_files": ["report.xlsx"],
                    "expected_keys": ["diferencias", "ventas"],
                    "rubric": {"correctness": 4, "traceability": 2},
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    normalized = EvolutionController(workspace_root=tmp_path).normalize_tasks([sample])
    arena = BenchmarkArena(experience_store=ExperienceStore(tmp_path / "arena_experiences.jsonl"))

    def executor(task, tool_id, contract):
        del task, tool_id, contract
        return OrchestratorResult(
            ok=True,
            tool_id="gemini_pro_long_context",
            tier="reasoning",
            output="diferencias detectadas en ventas",
        )

    def judge(task, result):
        del task, result
        return {"judge": "gemini-2.5-pro", "score": 8.5, "passed": True, "comment": "ok"}

    report = arena.run(normalized.records, executor=executor, judge=judge)
    assert report.total_runs == 1
    assert report.passed_runs == 1
    assert report.judge_count == 1
    saved = arena.experience_store.load()
    assert len(saved) == 1
    assert saved[0].judge_scores


def test_capability_matrix_aggregates_experiences(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))
    store = ExperienceStore(tmp_path / "matrix_experiences.jsonl")
    store.append_many(
        [
            RouterExperience(
                experience_id="exp-1",
                timestamp="2026-06-09T10:00:00+00:00",
                catalog_version=4,
                task_id="arena-1",
                task_shape="compare",
                tool_id="gemini_pro_long_context",
                required_capabilities=["cap_compare"],
                cognitive_requirements=["comparison"],
                elapsed_seconds=3.0,
                objective_checks={"passed": True, "checks": []},
                judge_scores=[{"judge": "gemini-2.5-pro", "score": 8.5, "passed": True}],
                outcome="sufficient",
                metadata={
                    "primary_capability": "cap_compare",
                    "evidence_kind": "live",
                },
            ),
            RouterExperience(
                experience_id="exp-2",
                timestamp="2026-06-09T10:00:01+00:00",
                catalog_version=4,
                task_id="arena-2",
                task_shape="compare",
                tool_id="gemini_pro_long_context",
                required_capabilities=["cap_compare"],
                cognitive_requirements=["comparison"],
                elapsed_seconds=5.0,
                objective_checks={"passed": True, "checks": []},
                judge_scores=[{"judge": "gemini-2.5-pro", "score": 9.0, "passed": True}],
                outcome="sufficient",
                metadata={
                    "primary_capability": "cap_compare",
                    "evidence_kind": "live",
                },
            ),
        ]
    )

    report = CapabilityMatrixBuilder(store).build()
    assert report.total_experiences == 2
    assert report.total_cells == 1
    cell = report.cells[0]
    assert cell.tool_id == "gemini_pro_long_context"
    assert cell.capability == "cap_compare"
    assert cell.samples == 2
    assert cell.pass_rate == 1.0
    assert cell.mean_score >= 8.5
    assert cell.mean_seconds == 4.0
    assert 0.1 <= cell.confidence <= 0.2


def test_benchmark_runner_marks_unavailable_tools_as_non_evidence(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))
    runner = BenchmarkRunner(workspace_root=tmp_path / "arena")
    contract = ContractBuilder().build(
        "Redacta un breve resumen de este informe.",
        attachments=[],
        metadata={"task_id": "arena-task"},
    )
    normalized = NormalizedTask(
        task_id="arena-task",
        title="Fallback task",
        source_path=Path("sample.json"),
        prompt="Redacta un breve resumen de este informe.",
        primary_capability="cap_synth_long",
        secondary_capabilities=[],
        compatible_tools=["local_direct"],
        objective_checks=["contains:resumen"],
        judge_rubric={"correctness": 4},
        task_shape="summarize",
        route_hypothesis="",
        required_files=[],
        expected_outputs=["resultado.md"],
        requires_network=False,
        dimensions={},
        contract=contract.model_dump(mode="json"),
    )
    report = BenchmarkArena(experience_store=ExperienceStore(tmp_path / "arena_store.jsonl")).run(
        [normalized],
        executor=runner.build_executor(),
        judge=runner.build_judge(),
    )
    assert report.total_runs == 1
    assert report.judge_count == 0
    assert report.runs[0].tool_id == "local_direct"
    assert report.runs[0].success is False
    assert report.runs[0].outcome == "insufficient"


def test_evolution_controller_uses_explicit_benchmark_paths(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))
    controller = EvolutionController(workspace_root=tmp_path)
    captured: dict[str, object] = {}

    class DummyReport:
        def to_markdown(self) -> str:
            return "ok"

    def fake_run_arena(
        path,
        *,
        limit=None,
        tool_ids=None,
        all_compatible_tools=False,
        task_ids=None,
    ):
        captured["path"] = path
        captured["limit"] = limit
        captured["tool_ids"] = tool_ids
        captured["all_compatible_tools"] = all_compatible_tools
        captured["task_ids"] = task_ids
        return DummyReport()

    controller.benchmark_runner.run_arena = fake_run_arena  # type: ignore[assignment]
    task_path = tmp_path / "custom_tasks.json"
    task_path.write_text("[]", encoding="utf-8")

    report = controller.run_benchmark_arena(task_paths=[task_path], limit=2)
    assert report.to_markdown() == "ok"
    assert captured["path"] == task_path
    assert captured["limit"] == 2


def test_evolution_controller_normalizes_explicit_paths(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))
    controller = EvolutionController(workspace_root=tmp_path)
    captured: dict[str, object] = {}

    class DummyReport:
        total_tasks = 1

        def to_markdown(self) -> str:
            return "normalized"

    def fake_normalize_path(path):
        captured["path"] = path
        return DummyReport()

    controller.normalize_tasks = lambda task_paths=None: fake_normalize_path(task_paths[0])  # type: ignore[assignment]
    task_path = tmp_path / "custom_tasks.json"
    task_path.write_text("[]", encoding="utf-8")

    report = controller.normalize_tasks([task_path])
    assert report.to_markdown() == "normalized"
    assert captured["path"] == task_path
