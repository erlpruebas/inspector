from __future__ import annotations

from pathlib import Path

from agent_v2_2.capabilities.catalog import create_default_catalog
from agent_v2_2.capabilities.introspection import IntrospectionManager
from agent_v2_2.capabilities.preferences import PreferenceStore
from agent_v2_2.capabilities.voice import VoiceCapabilities
from agent_v2_2.cli import check_status, set_speaker, set_voice, set_voice_name, set_voice_provider
from agent_v2_2.config import Config, QuotaConfig, TelegramConfig, load_config, parse_int_list, parse_path_list
from agent_v2_2.evolution.controller import EvolutionController
from agent_v2_2.evolution.coverage import TaskCoverageAnalyzer
from agent_v2_2.evolution.experience import BenchmarkExperienceImporter, ExperienceStore
from agent_v2_2.engines.codex_desktop import CodexDesktopOperator
from agent_v2_2.models import CapabilityRequest, OrchestratorResult, TaskRequest
from agent_v2_2.routing.contract import (
    CognitiveLevel,
    ExecutionRequirements,
    FileFormat,
    FileOperation,
    FileRequirement,
    Guarantee,
    InstrumentalCapability,
    Operation,
    PrepareAction,
    PrepareActionType,
    RequestContract,
)
from agent_v2_2.routing.registry import ToolRegistry, ToolDefinition
from agent_v2_2.scheduling.codex_quota import (
    CodexQuotaMonitor,
    CodexQuotaSnapshot,
    parse_rate_limits_response,
)
from agent_v2_2.scheduling.autonomy import QuotaAwareScheduler
from agent_v2_2.scheduling.queue import TaskQueue
from agent_v2_2.transport.lifecycle import LifecycleManager
from agent_v2_2.transport.metrics import MetricsRecorder
from agent_v2_2.transport.queue import ExecutionMailbox


def test_catalog_exposes_17_capabilities() -> None:
    catalog = create_default_catalog()
    assert len(catalog.capabilities) == 17
    assert catalog.capabilities[0].id == "cap_extract_short"
    assert catalog.capabilities[-1].id == "cap_verify"
    assert len(catalog.tools) == 13
    assert len({tool.tool_id for tool in catalog.tools}) == 13
    assert catalog.get_tool("premium_codex_55") is not None
    gemini = catalog.get_tool("gemini_pro_long_context")
    assert gemini is not None
    assert any(
        method.operation == "read" and method.format == "xlsx"
        for method in gemini.access_methods
    )


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


def test_canonical_request_contract_covers_prepare_execute_and_access() -> None:
    contract = RequestContract(
        normalized_request="Find a florist near my dentist.",
        prepare=[
            PrepareAction(
                action=PrepareActionType.MEMORY_LOOKUP,
                query="dentist address",
                output_key="dentist_address",
            ),
            PrepareAction(
                action=PrepareActionType.WEB_LOOKUP,
                query="florists near {dentist_address}",
                output_key="nearby_florists",
            ),
        ],
        execute=ExecutionRequirements(
            operation=Operation.ANSWER,
            cognitive_level=CognitiveLevel.LIGHT,
            instrumental_capabilities=[
                InstrumentalCapability.PREPARED_TEXT,
                InstrumentalCapability.CURRENT_WEB_LOOKUP,
            ],
            guarantees=[
                Guarantee.FRESH_INFORMATION,
                Guarantee.SOURCE_CITATIONS,
            ],
        ),
    )
    assert contract.schema_version == "1.0"
    assert "current_web_lookup" in contract.required_accesses()


def test_canonical_contract_tracks_file_operations() -> None:
    contract = RequestContract(
        normalized_request="Update the spreadsheet and preserve its format.",
        execute=ExecutionRequirements(
            operation=Operation.MODIFY_ARTIFACT,
            cognitive_level=CognitiveLevel.GENERAL,
            instrumental_capabilities=[
                InstrumentalCapability.READ_SPREADSHEET,
                InstrumentalCapability.WRITE_FILE,
                InstrumentalCapability.PRESERVE_DOCUMENT_FORMAT,
            ],
            file_requirements=[
                FileRequirement(
                    format=FileFormat.XLSX,
                    operations=[
                        FileOperation.READ,
                        FileOperation.MODIFY,
                        FileOperation.PRESERVE,
                        FileOperation.VERIFY,
                    ],
                    preserve_format=True,
                )
            ],
            guarantees=[
                Guarantee.ARTIFACT_EXISTS,
                Guarantee.ARTIFACT_VERIFIED,
            ],
        ),
    )
    assert "modify:xlsx" in contract.required_accesses()
    assert "verify:xlsx" in contract.required_accesses()


def test_codex_quota_monitor_uses_real_window_snapshots(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))
    snapshot = CodexQuotaSnapshot(
        five_hour_remaining=80,
        weekly_remaining=50,
        five_hour_resets_at=2_000_000_000,
        weekly_resets_at=2_000_100_000,
        captured_at=2_000_000_000,
    )
    monkeypatch.setattr("agent_v2_2.scheduling.codex_quota.time.time", lambda: 2_000_000_010)
    monitor = CodexQuotaMonitor(reader=lambda: snapshot)
    assert monitor.refresh() == snapshot
    assert monitor.can_schedule_codex()
    assert not monitor.should_reject(1000)
    assert "80% five-hour" in monitor.get_remaining_quota()
    assert monitor.get_footer() is not None

    reloaded = CodexQuotaMonitor(reader=lambda: snapshot)
    assert reloaded.snapshot() == snapshot


def test_codex_quota_monitor_pauses_at_five_hour_reserve(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setattr("agent_v2_2.scheduling.codex_quota.time.time", lambda: 2_000_000_010)
    snapshot = CodexQuotaSnapshot(
        five_hour_remaining=25,
        weekly_remaining=40,
        five_hour_resets_at=2_000_000_500,
        weekly_resets_at=2_000_100_000,
        captured_at=2_000_000_000,
    )
    monitor = CodexQuotaMonitor(reader=lambda: snapshot)
    monitor.refresh()
    assert not monitor.can_schedule_codex()
    assert "Five-hour" in (monitor.pause_reason() or "")


def test_parse_real_codex_rate_limit_response() -> None:
    snapshot = parse_rate_limits_response(
        {
            "result": {
                "rateLimits": {
                    "primary": {"usedPercent": 8, "resetsAt": 2_000_000_000},
                    "secondary": {"usedPercent": 93, "resetsAt": 2_000_100_000},
                }
            }
        }
    )
    assert snapshot.five_hour_remaining == 92
    assert snapshot.weekly_remaining == 7


def test_quota_scheduler_pauses_codex_and_runs_other_work(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setattr("agent_v2_2.scheduling.codex_quota.time.time", lambda: 2_000_000_010)
    blocked = CodexQuotaSnapshot(
        five_hour_remaining=25,
        weekly_remaining=20,
        five_hour_resets_at=2_000_000_500,
        weekly_resets_at=2_000_100_000,
        captured_at=2_000_000_000,
    )
    monitor = CodexQuotaMonitor(
        snapshot_path=tmp_path / "quota.json",
        reader=lambda: blocked,
    )
    queue = TaskQueue(store_path=tmp_path / "queue.json")
    codex_id = queue.enqueue(TaskRequest(text="code", tool_name="codex_gpt_5_5"))
    local_id = queue.enqueue(TaskRequest(text="docs", tool_name="local_direct"))
    scheduler = QuotaAwareScheduler(
        task_queue=queue,
        quota_monitor=monitor,
        checkpoint_path=tmp_path / "checkpoint.json",
    )

    selected = scheduler.next_runnable()
    assert selected is not None
    assert selected.task_id == local_id
    codex_task = next(task for task in queue.list_tasks() if task.task_id == codex_id)
    assert codex_task.status == "paused_quota"
    assert codex_task.pause_reason


def test_quota_scheduler_resumes_codex_after_reset(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setattr("agent_v2_2.scheduling.codex_quota.time.time", lambda: 2_000_000_010)
    allowed = CodexQuotaSnapshot(
        five_hour_remaining=90,
        weekly_remaining=20,
        five_hour_resets_at=2_000_000_500,
        weekly_resets_at=2_000_100_000,
        captured_at=2_000_000_000,
    )
    monitor = CodexQuotaMonitor(
        snapshot_path=tmp_path / "quota.json",
        reader=lambda: allowed,
    )
    queue = TaskQueue(store_path=tmp_path / "queue.json")
    task_id = queue.enqueue(TaskRequest(text="code", tool_name="codex_gpt_5_5"))
    queue.mark_paused(task_id, reason="quota", status="paused_quota")
    scheduler = QuotaAwareScheduler(
        task_queue=queue,
        quota_monitor=monitor,
        checkpoint_path=tmp_path / "checkpoint.json",
    )

    selected = scheduler.next_runnable()
    assert selected is not None
    assert selected.task_id == task_id
    assert selected.status == "pending"


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


def test_benchmark_importer_and_readiness(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))

    tasks_root = tmp_path / "benchmarks" / "tasks"
    results_root = tmp_path / "benchmarks" / "results" / "run-1"
    results_root.mkdir(parents=True, exist_ok=True)
    tasks_root.mkdir(parents=True, exist_ok=True)

    tasks_file = tasks_root / "synthetic.json"
    tasks_file.write_text(
        """
        [
          {
            "id": "task-1",
            "title": "Synthetic task",
            "block": "memory",
            "skills": ["cap_extract_short"],
            "required_files": ["memory.md"],
            "requires_network": false
          }
        ]
        """.strip(),
        encoding="utf-8",
    )

    output_file = results_root / "out.md"
    output_file.write_text("answer", encoding="utf-8")
    (results_root / "summary.json").write_text(
        """
        [
          {
            "engine": "tool-a",
            "task_id": "task-1",
            "returncode": 0,
            "timed_out": false,
            "elapsed_seconds": 1.23,
            "output_files": ["D:/tmp/out.md"],
            "model": "mock"
          }
        ]
        """.strip().replace("D:/tmp/out.md", str(output_file).replace("\\", "/")),
        encoding="utf-8",
    )
    (results_root / "tool_a_competitive.json").write_text(
        """
        [
          {
            "task_id": "task-1",
            "judge_model": "gemini-2.5-pro",
            "quality_winner": "tool-a",
            "fastest_sufficient": "tool-a",
            "candidates": [
              {"engine": "tool-a", "score": 9.0, "passed": true, "comment": "ok"}
            ]
          }
        ]
        """.strip(),
        encoding="utf-8",
    )

    store = ExperienceStore(tmp_path / "evolution" / "experiences.jsonl")
    importer = BenchmarkExperienceImporter(results_root=tmp_path / "benchmarks" / "results", tasks_root=tasks_root)
    imported = importer.import_all(store)
    assert imported == 1
    experiences = store.load()
    assert len(experiences) == 1
    assert experiences[0].task_id == "task-1"
    assert experiences[0].judge_scores

    controller = EvolutionController(workspace_root=tmp_path)
    controller.benchmark_importer = importer
    controller.experience_store = store
    readiness = controller.readiness()
    assert "experiencias" in readiness.to_markdown().lower()


def test_task_coverage_analyzer_reports_dimensions() -> None:
    coverage = TaskCoverageAnalyzer().analyze(Path("benchmarks/tasks"))
    assert coverage.total_tasks >= 25
    assert "text" in coverage.file_buckets or "csv" in coverage.file_buckets
    assert coverage.to_markdown().startswith("# Task coverage report")
