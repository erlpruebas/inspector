from __future__ import annotations

from datetime import datetime
from pathlib import Path

from orchestrator_v2_1 import OrchestratorResult
from orchestrator_v2_1.codex_rate_limits import parse_rate_limits_response
from orchestrator_v2_1.llm_router import decision_from_payload
from orchestrator_v2_1.memory_store import MemoryStore
from orchestrator_v2_1.models import RouteDecision, TaskRequest
from orchestrator_v2_1.orchestrator import OrchestratorV21
from orchestrator_v2_1.router import choose_tool
from orchestrator_v2_1.voice_settings import VoiceSettings


def test_task_request_accepts_request_id() -> None:
    request = TaskRequest(text="hola", request_id="abc")
    assert request.request_id == "abc"


def test_codex_rate_limit_footer_reports_remaining_percent() -> None:
    five_hour_reset = int(datetime(2026, 3, 25, 17, 15).timestamp())
    weekly_reset = int(datetime(2026, 3, 25, 23, 0).timestamp())
    snapshot = parse_rate_limits_response(
        {
            "result": {
                "rateLimits": {
                    "primary": {"usedPercent": 30, "resetsAt": five_hour_reset},
                    "secondary": {"usedPercent": 40, "resetsAt": weekly_reset},
                }
            }
        }
    )
    assert snapshot.footer() == "70% 17.15 60% 25/3"


def test_desktop_route_is_tier_5(monkeypatch) -> None:
    import orchestrator_v2_1.router as router_module

    monkeypatch.setattr(
        router_module,
        "route_with_model",
        lambda request, **kwargs: RouteDecision(
            tool_id="desktop_codex_operator",
            tier=5,
            reason="Visual authenticated task.",
            privacy_mode="clear",
        ),
    )
    decision = choose_tool(TaskRequest(text="cd abre el navegador autenticado"))
    assert decision.tool_id == "desktop_codex_operator"
    assert decision.tier == 5


def test_general_route_does_not_create_desktop_route(monkeypatch) -> None:
    import orchestrator_v2_1.router as router_module

    monkeypatch.setattr(
        router_module,
        "route_with_model",
        lambda request, **kwargs: RouteDecision(
            tool_id="worker_openrouter_deepseek32",
            tier=2,
            reason="General text task.",
            privacy_mode="clear",
        ),
    )
    decision = choose_tool(TaskRequest(text="resume la estrategia del proyecto"))
    assert decision.tool_id != "desktop_codex_operator"


def test_local_forced_execution() -> None:
    result = OrchestratorV21().handle(TaskRequest(text="ping", request_id="test-local"), tool_id="local_direct")
    assert result.ok
    assert result.tool_id == "local_direct"
    assert not result.attachments


def test_router_payload_can_select_grounded_weather_tool() -> None:
    decision = decision_from_payload(
        {
            "tool_id": "gemini_grounded_search",
            "reason": "Current weather requires grounded search.",
            "alternatives": ["worker_openrouter_gpt54mini"],
        },
        "clear",
        False,
    )
    assert decision.tool_id == "gemini_grounded_search"
    assert decision.tier == 3


def test_provider_failure_uses_route_fallback(tmp_path: Path, monkeypatch) -> None:
    import orchestrator_v2_1.orchestrator as orch_module
    import orchestrator_v2_1.router as router_module

    attempts: list[str] = []

    def fake_execute(request, decision):
        attempts.append(decision.tool_id)
        if len(attempts) == 1:
            return OrchestratorResult(
                ok=False,
                tool_id=decision.tool_id,
                tier=decision.tier,
                engine=decision.tool_id,
                output="",
                workdir=Path(".").resolve(),
                elapsed_seconds=0,
                privacy_mode="clear",
                error="API error 401: Invalid API Key",
            )
        return OrchestratorResult(
            ok=True,
            tool_id=decision.tool_id,
            tier=decision.tier,
            engine=decision.tool_id,
            output="respuesta alternativa",
            workdir=Path(".").resolve(),
            elapsed_seconds=0,
            privacy_mode="clear",
        )

    monkeypatch.setattr(orch_module, "execute_request", fake_execute)
    monkeypatch.setattr(
        router_module,
        "route_with_model",
        lambda request, **kwargs: RouteDecision(
            tool_id="router_groq_qwen32",
            tier=2,
            reason="Primary route.",
            privacy_mode="clear",
            alternatives=("worker_openrouter_deepseek32",),
        ),
    )
    orch = OrchestratorV21(memory_store=MemoryStore(tmp_path / "memory"))
    result = orch.handle(TaskRequest(text="hola", request_id="fallback"))

    assert result.ok
    assert len(attempts) == 2
    assert "Fallback automático" in result.output


def test_memory_roundtrip_changes_route(tmp_path: Path, monkeypatch) -> None:
    import orchestrator_v2_1.router as router_module

    store = MemoryStore(tmp_path / "memory")
    orch = OrchestratorV21(memory_store=store)
    user_id = "telegram-user"
    thread_id = "thread-1"

    save_result = orch.handle(
        TaskRequest(
            text="recuerda que mi casa está en Calle Luna 12",
            request_id="save-memory",
            user_id=user_id,
            thread_id=thread_id,
        ),
        tool_id="local_direct",
    )
    assert save_result.ok

    prepared = orch.prepare_request(
        TaskRequest(
            text="cómo llego desde mi casa a la dirección del cliente",
            request_id="route-memory",
            user_id=user_id,
            thread_id=thread_id,
        )
    )
    assert prepared.memory_context.facts
    assert any(fact.kind == "home_address" for fact in prepared.memory_context.facts)

    def route_from_memory(request, **kwargs):
        assert any(fact.kind == "home_address" for fact in request.memory_context.facts)
        return RouteDecision(
            tool_id="desktop_codex_operator",
            tier=5,
            reason="Map task with remembered address.",
            privacy_mode="clear",
        )

    monkeypatch.setattr(router_module, "route_with_model", route_from_memory)
    decision = choose_tool(prepared)
    assert decision.tool_id == "desktop_codex_operator"


def test_memory_is_written_as_markdown(tmp_path: Path) -> None:
    store = MemoryStore(tmp_path / "memory")
    orch = OrchestratorV21(memory_store=store)
    user_id = "telegram-user"
    thread_id = "thread-2"

    orch.handle(
        TaskRequest(
            text="recuerda que mi casa esta en Calle Luna 12",
            request_id="md-memory",
            user_id=user_id,
            thread_id=thread_id,
        ),
        tool_id="local_direct",
    )

    raw_files = sorted((tmp_path / "memory" / "telegram-user" / "thread-2" / "raw").glob("*.md"))
    assert raw_files
    content = raw_files[0].read_text(encoding="utf-8")
    assert content.startswith("## ")
    assert "- type: message" not in content
    assert "> recuerda que mi casa esta en Calle Luna 12" in content

    index_path = store.compact_thread(user_id, thread_id)
    index_content = index_path.read_text(encoding="utf-8")
    assert "# Memory index" in index_content
    assert "## casa" in index_content.lower()


def test_memory_query_is_resolved_by_model_with_context(tmp_path: Path, monkeypatch) -> None:
    import orchestrator_v2_1.orchestrator as orch_module
    import orchestrator_v2_1.router as router_module

    store = MemoryStore(tmp_path / "memory")
    orch = OrchestratorV21(memory_store=store)
    user_id = "telegram-user"
    thread_id = "thread-3"

    orch.handle(
        TaskRequest(
            text="recuerda que mi casa esta en Calle Luna 12",
            request_id="save-memory-query",
            user_id=user_id,
            thread_id=thread_id,
        )
    )
    seen: dict[str, TaskRequest] = {}

    monkeypatch.setattr(
        router_module,
        "route_with_model",
        lambda request, **kwargs: RouteDecision(
            tool_id="worker_openrouter_deepseek32",
            tier=2,
            reason="Natural-language memory answer.",
            privacy_mode="clear",
        ),
    )

    def fake_execute(request, decision):
        seen["request"] = request
        return OrchestratorResult(
            ok=True,
            tool_id=decision.tool_id,
            tier=decision.tier,
            engine=decision.tool_id,
            output="Recuerdo que tu casa está en Calle Luna 12.",
            workdir=Path(".").resolve(),
            elapsed_seconds=0,
            privacy_mode="clear",
        )

    monkeypatch.setattr(orch_module, "execute_request", fake_execute)
    result = orch.handle(
        TaskRequest(
            text="que recuerdas de mi casa",
            request_id="query-memory",
            user_id=user_id,
            thread_id=thread_id,
        )
    )
    assert result.ok
    assert result.tool_id == "worker_openrouter_deepseek32"
    assert seen["request"].memory_context.facts
    assert "Calle Luna 12" in result.output


def test_sensitive_action_requires_human_confirmation(monkeypatch) -> None:
    import orchestrator_v2_1.router as router_module

    monkeypatch.setattr(
        router_module,
        "route_with_model",
        lambda request, **kwargs: RouteDecision(
            tool_id="runtime_opencode_deepseek32",
            tier=4,
            reason="Filesystem action.",
            privacy_mode="clear",
        ),
    )
    result = OrchestratorV21().handle(TaskRequest(text="borra la carpeta temporal", request_id="hitl"))
    assert not result.ok
    assert result.requires_human_confirmation
    assert result.error == "human_confirmation_required"


def test_telegram_gateway_uses_v2_1(monkeypatch) -> None:
    from orchestrator_v2_1 import telegram_gateway as tg

    captured: list[str] = []

    def fake_send_message(chat_id, text):
        captured.append(f"{chat_id}:{text}")

    def fake_send_photo(chat_id, image_path, caption=""):
        captured.append(f"photo:{chat_id}:{image_path}:{caption}")

    def fake_handle(request, tool_id="", progress_callback=None):
        assert request.text == "hola"
        if progress_callback:
            progress_callback(
                "routed",
                {
                    "decision": RouteDecision(
                        tool_id="local_direct",
                        tier=1,
                        reason="test",
                        privacy_mode="clear",
                    ),
                    "seconds": 0.2,
                },
            )
        return OrchestratorResult(
            ok=True,
            tool_id="local_direct",
            tier=1,
            engine="local:direct",
            output="ok",
            workdir=Path(".").resolve(),
            elapsed_seconds=0,
            privacy_mode="clear",
        )

    monkeypatch.setattr(tg, "send_message", fake_send_message)
    monkeypatch.setattr(tg, "send_photo", fake_send_photo)
    monkeypatch.setattr(tg.ORCHESTRATOR, "handle", fake_handle)
    monkeypatch.setattr(tg, "VOICE_SETTINGS", VoiceSettings(generate_audio=False, play_audio=False))
    monkeypatch.setattr(tg.CODEX_RATE_LIMITS, "footer", lambda: "70% 17.15 60% 25/3")

    tg.process_message("hola", 123)

    assert captured[0] == "123:Recibido\n0.1s"
    assert any("Enrutado a Tier 1" in item for item in captured)
    assert any("Modelo: local:direct" in item for item in captured)
    assert any(item.endswith("ok\n\n0.1s") for item in captured)
    assert captured[-1] == "123:70% 17.15 60% 25/3"


def test_telegram_memory_flow_uses_saved_home_address(tmp_path: Path, monkeypatch) -> None:
    from orchestrator_v2_1 import telegram_gateway as tg
    from orchestrator_v2_1.memory_store import MemoryStore
    from orchestrator_v2_1.models import OrchestratorResult
    import orchestrator_v2_1.orchestrator as orch_module
    import orchestrator_v2_1.router as router_module

    store = MemoryStore(tmp_path / "memory")
    orch = OrchestratorV21(memory_store=store)
    monkeypatch.setattr(tg, "ORCHESTRATOR", orch)

    sent: list[str] = []

    def fake_send_message(chat_id, text):
        sent.append(text)

    monkeypatch.setattr(tg, "send_message", fake_send_message)
    monkeypatch.setattr(tg, "send_photo", lambda *args, **kwargs: None)
    monkeypatch.setattr(tg, "VOICE_SETTINGS", VoiceSettings(generate_audio=False, play_audio=False))

    orch.handle(
        TaskRequest(
            text="recuerda que mi casa esta en Calle Luna 12",
            request_id="telegram-memory-save",
            user_id="456",
            thread_id="456",
        ),
        tool_id="local_direct",
    )

    seen: dict[str, object] = {}

    def fake_execute_request(request, decision):
        seen["tool_id"] = decision.tool_id
        seen["memory_context"] = request.memory_context
        return OrchestratorResult(
            ok=True,
            tool_id=decision.tool_id,
            tier=decision.tier,
            engine=decision.tool_id,
            output="ok",
            workdir=Path(".").resolve(),
            elapsed_seconds=0,
            privacy_mode=decision.privacy_mode,
        )

    monkeypatch.setattr(
        router_module,
        "route_with_model",
        lambda request, **kwargs: RouteDecision(
            tool_id="desktop_codex_operator",
            tier=5,
            reason="Map task with remembered address.",
            privacy_mode="clear",
        ),
    )
    monkeypatch.setattr(orch_module, "execute_request", fake_execute_request)
    tg.process_message("como llego desde mi casa a la direccion del cliente", 456)

    assert seen["tool_id"] == "desktop_codex_operator"
    assert seen["memory_context"].facts
    assert any("Enrutado a Tier 5" in line for line in sent)


def test_telegram_voice_message_is_transcribed_and_replied(tmp_path: Path, monkeypatch) -> None:
    from orchestrator_v2_1 import telegram_gateway as tg
    from orchestrator_v2_1.models import OrchestratorResult
    import orchestrator_v2_1.orchestrator as orch_module

    monkeypatch.setattr(tg, "ALLOWED_CHAT_IDS", {"789"})

    sent_messages: list[str] = []
    sent_audio: list[Path] = []
    seen_requests: list[TaskRequest] = []

    def fake_send_message(chat_id, text):
        sent_messages.append(text)

    def fake_send_audio(chat_id, audio_path, caption=""):
        sent_audio.append(audio_path)

    def fake_download(token, file_id, target_dir, suffix=".ogg"):
        path = target_dir / f"{file_id}{suffix}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fake-audio")
        return path

    def fake_transcribe(audio_path, language="es", prompt=""):
        return "recuerda que mi casa esta en Calle Luna 12"

    def fake_handle(request, tool_id="", progress_callback=None):
        seen_requests.append(request)
        return OrchestratorResult(
            ok=True,
            tool_id="local_direct",
            tier=1,
            engine="local:direct",
            output="respuesta final",
            workdir=Path(".").resolve(),
            elapsed_seconds=0,
            privacy_mode="clear",
        )

    def fake_build_voice_summary_text(answer_text, user_request="", language="es"):
        return "Resumen hablado en dos párrafos."

    def fake_synthesize_voice_summary(summary_text, output_path, **kwargs):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"wave-bytes")
        return output_path

    monkeypatch.setattr(tg, "send_message", fake_send_message)
    monkeypatch.setattr(tg, "send_audio", fake_send_audio)
    monkeypatch.setattr(tg, "download_telegram_file", fake_download)
    monkeypatch.setattr(tg, "transcribe_audio_file", fake_transcribe)
    monkeypatch.setattr(tg, "build_voice_summary_text", fake_build_voice_summary_text)
    monkeypatch.setattr(tg, "synthesize_voice_summary", fake_synthesize_voice_summary)
    monkeypatch.setattr(tg, "play_audio_file", lambda path: None)
    monkeypatch.setattr(tg.ORCHESTRATOR, "handle", fake_handle)
    monkeypatch.setattr(tg, "VOICE_SETTINGS", VoiceSettings(generate_audio=True, play_audio=True))
    monkeypatch.setattr(tg.CODEX_RATE_LIMITS, "footer", lambda: "70% 17.15 60% 25/3")
    monkeypatch.setattr(orch_module, "execute_request", lambda request, decision: fake_handle(request))

    tg.process_update(
        {
            "update_id": 1,
            "message": {
                "chat": {"id": 789},
                "voice": {"file_id": "voice-file-1"},
            },
        }
    )

    assert seen_requests
    assert seen_requests[0].text == "recuerda que mi casa esta en Calle Luna 12"
    assert seen_requests[0].metadata["source"] == "voice"
    assert any("Transcrito" in message for message in sent_messages)
    assert any("respuesta final" in message for message in sent_messages)
    assert sent_audio


def test_orchestrator_reports_routing_and_execution_timings(tmp_path: Path, monkeypatch) -> None:
    import orchestrator_v2_1.orchestrator as orch_module
    import orchestrator_v2_1.router as router_module

    events: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        router_module,
        "route_with_model",
        lambda request, **kwargs: RouteDecision(
            tool_id="local_direct",
            tier=1,
            reason="test",
            privacy_mode="clear",
        ),
    )
    monkeypatch.setattr(
        orch_module,
        "execute_request",
        lambda request, decision: OrchestratorResult(
            ok=True,
            tool_id=decision.tool_id,
            tier=decision.tier,
            engine="local:direct",
            output="ok",
            workdir=tmp_path,
            elapsed_seconds=0,
            privacy_mode="clear",
        ),
    )

    result = OrchestratorV21(memory_store=MemoryStore(tmp_path / "memory")).handle(
        TaskRequest(text="hola", request_id="timings"),
        progress_callback=lambda event, payload: events.append((event, payload)),
    )

    assert [event for event, _ in events] == ["routed", "executed"]
    assert result.timings.total_seconds >= result.timings.routing_seconds
    assert result.timings.total_seconds >= result.timings.execution_seconds


def test_text_reply_generates_and_plays_audio(tmp_path: Path, monkeypatch) -> None:
    from orchestrator_v2_1 import telegram_gateway as tg

    audio_path = tmp_path / "summary.wav"
    played: list[Path] = []
    sent_audio: list[tuple[Path, str]] = []
    sent_messages: list[str] = []

    monkeypatch.setattr(tg, "VOICE_SETTINGS", VoiceSettings(generate_audio=True, play_audio=True))
    monkeypatch.setattr(tg, "build_voice_summary_text", lambda answer, user_request="": "Resumen directo.")
    monkeypatch.setattr(
        tg,
        "synthesize_voice_summary",
        lambda summary, output_path, **kwargs: audio_path,
    )
    monkeypatch.setattr(tg, "play_audio_file", lambda path: played.append(path))
    monkeypatch.setattr(tg, "send_audio", lambda chat_id, path, caption="": sent_audio.append((path, caption)))
    monkeypatch.setattr(tg, "send_message", lambda chat_id, text: sent_messages.append(text))
    monkeypatch.setattr(tg.CODEX_RATE_LIMITS, "footer", lambda: "70% 17.15 60% 25/3")

    tg.deliver_result(
        123,
        TaskRequest(text="dime el tiempo", request_id="text-audio"),
        OrchestratorResult(
            ok=True,
            tool_id="local_direct",
            tier=1,
            engine="local:direct",
            output="Hace 22 grados.",
            workdir=tmp_path,
            elapsed_seconds=1.2,
            privacy_mode="clear",
        ),
    )

    assert sent_audio
    assert "Edge · es-ES-ElviraNeural" in sent_audio[0][1]
    assert played == [audio_path]
    assert any("Reproduciendo Edge · es-ES-ElviraNeural" in message for message in sent_messages)
    assert sent_messages[-1] == "70% 17.15 60% 25/3"


def test_telegram_hides_technical_traceback(monkeypatch) -> None:
    from orchestrator_v2_1 import telegram_gateway as tg

    sent: list[str] = []
    monkeypatch.setattr(tg, "send_message", lambda chat_id, text: sent.append(text))

    result = OrchestratorResult(
        ok=False,
        tool_id="router_groq_qwen32",
        tier=2,
        engine="groq:test",
        output="",
        workdir=Path(".").resolve(),
        elapsed_seconds=0,
        privacy_mode="clear",
        error="Traceback...\nRuntimeError: API error 401: Invalid API Key",
    )
    tg.deliver_result(123, TaskRequest(text="estado"), result)

    assert sent
    assert "clave válida" in sent[0]
    assert "Traceback" not in sent[0]


def test_legacy_desktop_import_is_isolated() -> None:
    offenders = []
    root = Path("orchestrator_v2_1")
    for path in root.glob("*.py"):
        if path.name == "desktop_adapter.py":
            continue
        text = path.read_text(encoding="utf-8")
        if "orchestrator_v2.desktop_codex_operator" in text or "capture_desktop_screenshot" in text:
            offenders.append(path.name)
    assert offenders == []


def test_development_mode_activation_and_deactivation(tmp_path: Path, monkeypatch) -> None:
    from orchestrator_v2_1 import development_mode as development_module

    monkeypatch.setattr("orchestrator_v2_1.conversation_state.DEFAULT_STATE_ROOT", tmp_path / "state")
    controller = development_module.DevelopmentModeController(tmp_path)
    sent: list[str] = []

    assert controller.process(
        123,
        "activar modo desarrollo",
        send_message=lambda chat_id, text: sent.append(text),
        complete_implementation=lambda *args: None,
    )
    assert controller.is_active(123)
    assert "activado" in sent[-1].casefold()

    assert controller.process(
        123,
        "desactivar modo desarrollo",
        send_message=lambda chat_id, text: sent.append(text),
        complete_implementation=lambda *args: None,
    )
    assert not controller.is_active(123)
    assert "desactivado" in sent[-1].casefold()


def test_development_mode_proposal_can_be_revised_and_approved(tmp_path: Path, monkeypatch) -> None:
    from orchestrator_v2_1 import development_mode as development_module

    monkeypatch.setattr("orchestrator_v2_1.conversation_state.DEFAULT_STATE_ROOT", tmp_path / "state")
    controller = development_module.DevelopmentModeController(tmp_path)
    sent: list[str] = []
    proposal = {
        "title": "Añadir una prueba",
        "understanding": "Se añadirá una prueba.",
        "changes": ["Crear la prueba."],
        "files": ["tests/test_example.py"],
        "tests": ["pytest"],
        "risks": [],
        "open_questions": [],
    }
    monkeypatch.setattr(controller, "_run_proposal_codex", lambda *args: proposal)

    controller.activate(456)
    controller._proposal_worker(456, "añade una prueba", "", None, 1, development_module.RunningTask(), lambda _, text: sent.append(text))
    state = controller._development_state(456)
    assert state["phase"] == "awaiting_approval"
    assert "Propuesta de desarrollo v1" in sent[-1]

    started: list[bool] = []
    monkeypatch.setattr(controller, "_start_implementation", lambda *args, **kwargs: started.append(True))
    assert controller.process(
        456,
        "sí",
        send_message=lambda chat_id, text: sent.append(text),
        complete_implementation=lambda *args: None,
    )
    assert started == [True]


def test_development_mode_feedback_requests_a_revised_proposal(tmp_path: Path, monkeypatch) -> None:
    from orchestrator_v2_1 import development_mode as development_module

    monkeypatch.setattr("orchestrator_v2_1.conversation_state.DEFAULT_STATE_ROOT", tmp_path / "state")
    controller = development_module.DevelopmentModeController(tmp_path)
    controller.activate(457)
    controller._set_development_state(
        457,
        {
            "active": True,
            "phase": "awaiting_approval",
            "pending_request": "cambia el saludo",
            "proposal": {"title": "Primera propuesta"},
            "proposal_version": 1,
        },
    )
    revisions: list[tuple[str, bool]] = []
    monkeypatch.setattr(
        controller,
        "_start_proposal",
        lambda chat_id, text, **kwargs: revisions.append((text, kwargs["revision"])),
    )

    controller.process(
        457,
        "Hazlo sin tocar la voz",
        send_message=lambda *args: None,
        complete_implementation=lambda *args: None,
    )

    assert revisions == [("Hazlo sin tocar la voz", True)]


def test_development_mode_recovers_interrupted_execution(tmp_path: Path, monkeypatch) -> None:
    from orchestrator_v2_1 import development_mode as development_module

    monkeypatch.setattr("orchestrator_v2_1.conversation_state.DEFAULT_STATE_ROOT", tmp_path / "state")
    controller = development_module.DevelopmentModeController(tmp_path)
    controller.activate(458)
    controller._set_development_state(
        458,
        {
            "active": True,
            "phase": "implementing",
            "pending_request": "cambia el saludo",
            "proposal": {"title": "Cambio aprobado"},
            "proposal_version": 1,
        },
    )
    discarded: list[str] = []

    controller.process(
        458,
        "no",
        send_message=lambda chat_id, text: discarded.append(text),
        complete_implementation=lambda *args: None,
    )

    assert controller._development_state(458)["phase"] == "idle"
    assert "descartada" in discarded[-1].casefold()


def test_telegram_development_command_bypasses_normal_orchestrator(monkeypatch) -> None:
    from orchestrator_v2_1 import telegram_gateway as tg

    sent: list[str] = []
    handled: list[str] = []
    monkeypatch.setattr(tg, "send_message", lambda chat_id, text: sent.append(text))
    monkeypatch.setattr(tg.DEVELOPMENT_MODE, "is_active", lambda chat_id: False)
    monkeypatch.setattr(
        tg.DEVELOPMENT_MODE,
        "process",
        lambda chat_id, text, **kwargs: handled.append(text) or True,
    )
    monkeypatch.setattr(
        tg.ORCHESTRATOR,
        "handle",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("normal orchestrator should not run")),
    )

    tg.process_message("activar modo desarrollo", 789)

    assert handled == ["activar modo desarrollo"]


def test_development_response_sends_audio_and_rate_limit_footer(tmp_path: Path, monkeypatch) -> None:
    from orchestrator_v2_1 import telegram_gateway as tg

    audio_path = tmp_path / "development-summary.wav"
    events: list[str] = []
    monkeypatch.setattr(tg, "VOICE_SETTINGS", VoiceSettings(generate_audio=True, play_audio=True))
    monkeypatch.setattr(tg, "send_message", lambda chat_id, text: events.append(f"text:{text}"))
    monkeypatch.setattr(tg, "send_audio", lambda chat_id, path, caption="": events.append(f"audio:{path.name}"))
    monkeypatch.setattr(
        tg,
        "synthesize_voice_summary",
        lambda summary, output_path, **kwargs: audio_path,
    )
    monkeypatch.setattr(tg, "play_audio_file", lambda path: events.append(f"play:{path.name}"))
    monkeypatch.setattr(tg.CODEX_RATE_LIMITS, "footer", lambda: "70% 17.15 60% 25/3")

    tg.deliver_development_response(
        123,
        "Propuesta preparada.",
        user_request="Añade una prueba.",
    )

    assert events[0] == "text:Propuesta preparada."
    assert "audio:development-summary.wav" in events
    assert "play:development-summary.wav" in events
    assert events[-1] == "text:70% 17.15 60% 25/3"


def test_development_controller_messages_use_multimedia_delivery(monkeypatch) -> None:
    from orchestrator_v2_1 import telegram_gateway as tg

    delivered: list[tuple[int, str, str]] = []
    monkeypatch.setattr(tg.DEVELOPMENT_MODE, "is_active", lambda chat_id: False)

    def fake_process(chat_id, text, *, send_message, complete_implementation):
        send_message(chat_id, "Modo desarrollo activado.")
        return True

    monkeypatch.setattr(tg.DEVELOPMENT_MODE, "process", fake_process)
    monkeypatch.setattr(
        tg,
        "deliver_development_response",
        lambda chat_id, output, user_request="", **kwargs: delivered.append(
            (chat_id, output, user_request)
        ),
    )

    assert tg.process_development_message("activar modo desarrollo", 456)
    assert delivered == [(456, "Modo desarrollo activado.", "activar modo desarrollo")]


def test_development_rebases_commit_when_main_head_advanced(tmp_path: Path, monkeypatch) -> None:
    from orchestrator_v2_1 import development_mode as development_module

    project_root = tmp_path / "project"
    worktree = tmp_path / "worktree"
    project_root.mkdir()
    worktree.mkdir()
    controller = development_module.DevelopmentModeController(project_root)
    calls: list[tuple[Path, tuple[str, ...]]] = []

    def fake_run_git(cwd, *args):
        calls.append((cwd, args))
        if cwd == controller.project_root and args == ("rev-parse", "HEAD"):
            return "new-head\n"
        if cwd == worktree and args == ("rev-parse", "HEAD^"):
            return "old-head\n"
        if cwd == worktree and args == ("rebase", "new-head"):
            return ""
        if cwd == worktree and args == ("rev-parse", "HEAD"):
            return "rebased-commit\n"
        raise AssertionError((cwd, args))

    monkeypatch.setattr(development_module, "run_git", fake_run_git)

    assert controller._rebase_onto_current_head(worktree) == "rebased-commit"
    assert (worktree, ("rebase", "new-head")) in calls


def test_readable_development_error_keeps_conflict_context() -> None:
    from orchestrator_v2_1.development_mode import readable_error

    error = RuntimeError(
        "error: Your local changes would be overwritten by cherry-pick:\n"
        "README.md\n"
        "fatal: cherry-pick failed"
    )

    detail = readable_error(error)

    assert "would be overwritten" in detail
    assert "cherry-pick failed" in detail
