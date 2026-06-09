from __future__ import annotations

import json
from pathlib import Path

from agent_v2_2.config import Config, QuotaConfig, TelegramConfig
from agent_v2_2.evolution import BenchmarkArena, ExperienceStore
from agent_v2_2.models import Attachment, OrchestratorResult
from agent_v2_2.evolution.controller import EvolutionController
from agent_v2_2.routing.builder import ContractBuilder
from agent_v2_2.routing.contract import (
    CognitiveLevel,
    Guarantee,
    InstrumentalCapability,
    Operation,
    PrepareActionType,
)
from agent_v2_2.runtime import TelegramAgentRuntime
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
    runtime = TelegramAgentRuntime(transport=transport)
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
    assert any("Execution engine simulado" in text for text in message_texts)


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
