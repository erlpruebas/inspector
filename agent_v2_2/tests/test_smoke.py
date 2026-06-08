from __future__ import annotations

from pathlib import Path

from agent_v2_2.capabilities.catalog import create_default_catalog
from agent_v2_2.capabilities.introspection import IntrospectionManager
from agent_v2_2.capabilities.preferences import PreferenceStore
from agent_v2_2.capabilities.voice import VoiceCapabilities
from agent_v2_2.cli import check_status, set_speaker, set_voice, set_voice_name, set_voice_provider
from agent_v2_2.config import Config, QuotaConfig, TelegramConfig, load_config, parse_int_list, parse_path_list
from agent_v2_2.evolution.controller import EvolutionController
from agent_v2_2.engines.codex_desktop import CodexDesktopOperator
from agent_v2_2.models import CapabilityRequest, OrchestratorResult, TaskRequest
from agent_v2_2.routing.registry import ToolRegistry, ToolDefinition
from agent_v2_2.scheduling.codex_quota import CodexQuotaMonitor
from agent_v2_2.transport.lifecycle import LifecycleManager
from agent_v2_2.transport.metrics import MetricsRecorder
from agent_v2_2.transport.queue import ExecutionMailbox


def test_catalog_exposes_17_capabilities() -> None:
    catalog = create_default_catalog()
    assert len(catalog.capabilities) == 17
    assert catalog.capabilities[0].id == "cap_extract_short"
    assert catalog.capabilities[-1].id == "cap_verify"


def test_config_parsers_handle_empty_and_lists(monkeypatch) -> None:
    assert parse_int_list("") == []
    assert parse_int_list("1, 2, nope, 3") == [1, 2, 3]
    assert parse_path_list("") == []
    assert parse_path_list("a;b") == [Path("a;b")]

    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", "C:/tmp/agent")
    cfg = load_config()
    assert isinstance(cfg, Config)
    assert str(cfg.workspace_root).replace("\\", "/").endswith("C:/tmp/agent")
    assert isinstance(cfg.telegram, TelegramConfig)
    assert isinstance(cfg.quota, QuotaConfig)


def test_registry_and_models_are_instantiable() -> None:
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            id="local_direct",
            name="Local Direct",
            description="Smoke test tool",
            tier="fast",
            handler=lambda request: OrchestratorResult(ok=True, tool_id="local_direct", tier="fast", output=request.text),
        )
    )
    tool = registry.get_tool("local_direct")
    assert tool is not None
    assert registry.get_tools_by_tier("fast")[0].id == "local_direct"

    request = CapabilityRequest(
        capability="cap_verify",
        tool_name="local_direct",
        format="text",
        operation="verify",
        text="verifica esto",
    )
    assert request.operation == "verify"
    assert isinstance(TaskRequest.model_validate(request.model_dump()), TaskRequest)


def test_codex_quota_monitor_default_footer_is_safe(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monitor = CodexQuotaMonitor()
    assert monitor.get_remaining_quota().startswith("Cuota Codex:")
    assert "Codex" in monitor.get_footer()
    monitor.record_usage("codex", 250_000)
    assert not monitor.should_reject(1000)


def test_desktop_codex_operator_falls_back_when_cli_missing(tmp_path: Path) -> None:
    operator = CodexDesktopOperator(cli_path=tmp_path / "missing-codex-cli.exe")
    result = operator.execute_task("haz una prueba", tmp_path)
    assert "Simulación" in result


def test_introspection_manager_reports_capabilities() -> None:
    manager = IntrospectionManager()
    answer = manager.answer_question("¿Qué capacidades tienes?")
    assert "capacidades disponibles" in answer.body.lower()


def test_preference_store_persists_flags(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))
    store = PreferenceStore()
    state = store.toggle_voice(True)
    assert state.voice_enabled is True
    state = store.toggle_speaker(True)
    assert state.speaker_enabled is True
    state = store.set_voice_provider("edge")
    assert state.voice_provider == "edge"
    state = store.set_voice_name("Elvira")
    assert state.voice_name == "Elvira"

    reloaded = PreferenceStore().load()
    assert reloaded.voice_enabled is True
    assert reloaded.speaker_enabled is True
    assert reloaded.voice_provider == "edge"
    assert reloaded.voice_name == "Elvira"


def test_voice_warmup_returns_a_status_map() -> None:
    warmup = VoiceCapabilities().warmup()
    assert "edge" in warmup
    assert "groq_stt" in warmup


def test_transport_metrics_mailbox_and_lifecycle(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))

    recorder = MetricsRecorder()
    metrics = recorder.start("req-1")
    recorder.record_stage("req-1", "routing", 0.2)
    recorder.record_stage("req-1", "execution", 1.4)
    recorder.finish("req-1")
    assert round(metrics.timings.total_seconds, 1) == 1.6

    mailbox = ExecutionMailbox()
    execution_id = mailbox.append_inbox(None, "hola", chat_id=123)
    mailbox.append_outbox(execution_id, "respuesta", chat_id=123)
    assert len(mailbox.list_inbox(execution_id)) == 1
    assert len(mailbox.list_outbox(execution_id)) == 1

    lifecycle = LifecycleManager()
    lifecycle.request_reload("test")
    state = lifecycle.load()
    assert state.reload_requested is True
    lifecycle.request_restart("again")
    state = lifecycle.load()
    assert state.restart_requested is True


def test_evolution_controller_can_audit_and_activate(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))
    controller = EvolutionController(workspace_root=tmp_path)
    report = controller.audit_tasks()
    assert report.total_tasks >= 3
    maturity = controller.evaluate_maturity()
    assert maturity.total_items >= 1
    status = controller.activate()
    assert status.active is True
    assert status.audit.total_tasks >= 3
