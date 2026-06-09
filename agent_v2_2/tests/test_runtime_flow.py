from __future__ import annotations

from pathlib import Path

from agent_v2_2.config import Config, QuotaConfig, TelegramConfig
from agent_v2_2.models import Attachment
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

