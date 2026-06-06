from __future__ import annotations

import logging
import os
import time
from dataclasses import replace
from pathlib import Path

import requests
from benchmarks.env_utils import load_env_files

from .conversation_state import (
    clear_pending_confirmation,
    deserialize_task_request,
    get_pending_confirmation,
    is_confirmation_no,
    is_confirmation_yes,
    set_pending_confirmation,
)
from .models import OrchestratorResult, RouteDecision, TaskRequest
from .orchestrator import OrchestratorV21
from .tool_registry import get_tool
from .voice_settings import load_voice_settings
from .voice_tools import (
    build_voice_summary_text,
    download_telegram_file,
    play_audio_file,
    synthesize_voice_summary,
    transcribe_audio_file,
)


load_env_files()

TOKEN = os.getenv("LAB_BOT_1_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_CHAT_IDS = {
    item.strip()
    for raw in (os.getenv("LAB_TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_ALLOWED_USER_IDS") or "").split(",")
    for item in [raw]
    if item.strip()
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
ORCHESTRATOR = OrchestratorV21()
VOICE_SETTINGS = load_voice_settings()
VOICE_RUNTIME_DIR = Path("orchestrator_v2_1/runtime/voice").resolve()
VOICE_INBOX_DIR = VOICE_RUNTIME_DIR / "inbox"
VOICE_OUTBOX_DIR = VOICE_RUNTIME_DIR / "outbox"


def get_updates(offset: int | None = None) -> list[dict]:
    if not TOKEN:
        return []
    params: dict[str, object] = {"timeout": 30, "allowed_updates": ["message", "edited_message"]}
    if offset is not None:
        params["offset"] = offset
    try:
        response = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", params=params, timeout=40)
        response.raise_for_status()
        return response.json().get("result", [])
    except Exception as exc:
        logging.error("Telegram getUpdates failed: %s", exc)
        return []


def send_message(chat_id: int | str, text: str) -> None:
    if not TOKEN:
        return
    for chunk in message_chunks(text):
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": chunk},
                timeout=15,
            )
            response.raise_for_status()
        except Exception as exc:
            logging.error("Telegram sendMessage failed: %s", exc)


def send_photo(chat_id: int | str, image_path: Path, caption: str = "") -> None:
    if not TOKEN:
        return
    try:
        with image_path.open("rb") as handle:
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
                data={"chat_id": chat_id, "caption": caption[:1024]},
                files={"photo": handle},
                timeout=60,
            )
    except Exception as exc:
        logging.error("Telegram sendPhoto failed: %s", exc)


def send_audio(chat_id: int | str, audio_path: Path, caption: str = "") -> None:
    if not TOKEN:
        return
    try:
        with audio_path.open("rb") as handle:
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendAudio",
                data={"chat_id": chat_id, "caption": caption[:1024]},
                files={"audio": handle},
                timeout=60,
            )
    except Exception as exc:
        logging.error("Telegram sendAudio failed: %s", exc)


def send_attachment(chat_id: int | str, result: OrchestratorResult, attachment_index: int, attachment_path: Path, label: str) -> None:
    if not attachment_path.exists():
        return
    if result.attachments[attachment_index].kind == "image":
        send_photo(chat_id, attachment_path, caption=label)
        return
    if result.attachments[attachment_index].kind in {"markdown", "json", "text"}:
        try:
            content = attachment_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            content = str(attachment_path)
        send_message(chat_id, f"{label}\n\n{content[:3500]}")
        return
    send_message(chat_id, f"{label}\n{attachment_path}")


def build_request(text: str, chat_id: int | str, *, source: str = "text", metadata: dict | None = None) -> TaskRequest:
    request_metadata = {
        "desktop_send": True,
        "desktop_new_chat": True,
        "desktop_wait_seconds": 300,
        "source": source,
    }
    if metadata:
        request_metadata.update(metadata)
    return TaskRequest(
        text=text,
        request_id=f"tg-{chat_id}-{int(time.time() * 1000)}",
        user_id=str(chat_id),
        thread_id=str(chat_id),
        privacy_mode="clear",
        metadata=request_metadata,
    )

def format_seconds(seconds: float) -> str:
    if seconds < 1:
        value = max(0.1, round(seconds, 1))
        return f"{value:g}s"
    return f"{round(seconds):d}s"


def progress_sender(chat_id: int | str):
    def send_progress(event: str, payload: dict) -> None:
        if event == "routed":
            decision = payload["decision"]
            engine = get_tool(decision.tool_id).engine
            send_message(
                chat_id,
                f"Enrutado a Tier {decision.tier}\nModelo: {engine}\n{format_seconds(payload['seconds'])}",
            )

    return send_progress


def summarize_and_send_audio(chat_id: int | str, request: TaskRequest, result: OrchestratorResult) -> None:
    if not VOICE_SETTINGS.generate_audio:
        return
    try:
        started = time.monotonic()
        if len(result.output) <= VOICE_SETTINGS.summarize_above_chars:
            summary_text = result.output.strip()
        else:
            summary_text = build_voice_summary_text(result.output, user_request=request.text)
        outputs: list[tuple[str, Path, float]] = []
        audio_path = synthesize_voice_summary(
            summary_text,
            VOICE_OUTBOX_DIR / f"{request.request_id}-{VOICE_SETTINGS.provider}.wav",
            provider=VOICE_SETTINGS.provider,
            voice_name=VOICE_SETTINGS.voice_name,
        )
        outputs.append(
            (
                f"{VOICE_SETTINGS.provider.title()} · {VOICE_SETTINGS.voice_name}",
                audio_path,
                time.monotonic() - started,
            )
        )
        if VOICE_SETTINGS.comparison_enabled:
            comparison_started = time.monotonic()
            comparison_path = synthesize_voice_summary(
                summary_text,
                VOICE_OUTBOX_DIR / f"{request.request_id}-{VOICE_SETTINGS.comparison_provider}.wav",
                provider=VOICE_SETTINGS.comparison_provider,
                voice_name=VOICE_SETTINGS.comparison_voice_name,
            )
            outputs.append(
                (
                    f"{VOICE_SETTINGS.comparison_provider.title()} · {VOICE_SETTINGS.comparison_voice_name}",
                    comparison_path,
                    time.monotonic() - comparison_started,
                )
            )

        for label, path, seconds in outputs:
            send_audio(chat_id, path, caption=f"{label}\n{format_seconds(seconds)}")

        if VOICE_SETTINGS.play_audio:
            for label, path, _ in outputs:
                playback_started = time.monotonic()
                process = play_audio_file(path)
                send_message(
                    chat_id,
                    f"Reproduciendo {label}\n{format_seconds(time.monotonic() - playback_started)}",
                )
                if process is not None and hasattr(process, "wait"):
                    process.wait()
    except Exception as exc:
        logging.error("Voice summary generation failed: %s", exc)


def warm_voice_provider() -> None:
    if not VOICE_SETTINGS.generate_audio or not VOICE_SETTINGS.warm_on_startup:
        return
    try:
        synthesize_voice_summary(
            "Sistema de voz preparado.",
            VOICE_OUTBOX_DIR / "_warmup.wav",
            provider=VOICE_SETTINGS.provider,
            voice_name=VOICE_SETTINGS.voice_name,
        )
        if VOICE_SETTINGS.comparison_enabled:
            synthesize_voice_summary(
                "Sistema de voz comparativa preparado.",
                VOICE_OUTBOX_DIR / "_warmup-comparison.wav",
                provider=VOICE_SETTINGS.comparison_provider,
                voice_name=VOICE_SETTINGS.comparison_voice_name,
            )
    except Exception as exc:
        logging.warning("Voice provider warmup failed: %s", exc)


def extract_message_text_and_request(message: dict, chat_id: int | str) -> TaskRequest | None:
    text = (message.get("text") or message.get("caption") or "").strip()
    if text:
        return build_request(text, chat_id, source="text")

    voice = message.get("voice")
    audio = message.get("audio")
    if not voice and not audio:
        return None

    media = voice or audio or {}
    file_id = media.get("file_id")
    if not file_id:
        return None

    suffix = ".ogg" if voice else Path(str(media.get("file_name") or "audio")).suffix or ".mp3"
    downloaded = download_telegram_file(TOKEN, file_id, VOICE_INBOX_DIR, suffix=suffix)
    transcription_started = time.monotonic()
    transcript = transcribe_audio_file(
        downloaded,
        language="es",
        prompt="Transcribe exactly what the user said in Spanish, preserving names, addresses, and task instructions.",
    )
    transcription_seconds = time.monotonic() - transcription_started
    if not transcript.strip():
        return None
    metadata = {
        "source": "voice",
        "telegram_file_id": file_id,
        "telegram_file_path": str(downloaded),
        "transcription_seconds": transcription_seconds,
    }
    return build_request(transcript.strip(), chat_id, source="voice", metadata=metadata)


def process_confirmation_reply(text: str, chat_id: int | str) -> bool:
    pending = get_pending_confirmation(str(chat_id), str(chat_id))
    if not pending:
        return False
    if is_confirmation_no(text):
        clear_pending_confirmation(str(chat_id), str(chat_id))
        send_message(chat_id, "Cancelado.")
        return True
    if not is_confirmation_yes(text):
        return False

    clear_pending_confirmation(str(chat_id), str(chat_id))
    request = deserialize_task_request(pending["request"])
    pending_tool_id = str((pending.get("decision") or {}).get("tool_id", ""))
    decision = ORCHESTRATOR.route(request, tool_id=pending_tool_id) if pending_tool_id else ORCHESTRATOR.route(request)
    request = replace(request, metadata={**request.metadata, "human_confirmation_approved": True, "pending_confirmation": pending})
    send_message(chat_id, f"Confirmado. Reanudo {decision.tool_id or request.text}.")
    result = ORCHESTRATOR.handle(request, progress_callback=progress_sender(chat_id))
    deliver_result(chat_id, request, result)
    return True


def deliver_result(chat_id: int | str, request: TaskRequest, result: OrchestratorResult) -> None:
    if result.requires_human_confirmation and result.human_confirmation:
        send_message(chat_id, result.output)
        pending_decision = RouteDecision(
            tool_id=result.tool_id,
            tier=result.tier,
            reason=result.human_confirmation.risk or "Human confirmation required.",
            privacy_mode=result.privacy_mode,
            needs_privacy_confirmation=False,
        )
        set_pending_confirmation(
            str(chat_id),
            str(chat_id),
            request,
            pending_decision,
            result.human_confirmation,
        )
        return

    if not result.ok:
        logging.error("Task failed via %s: %s", result.tool_id, result.error or result.output)
        send_message(chat_id, friendly_error_message(result))
        return

    if result.output:
        task_seconds = result.timings.execution_seconds or result.elapsed_seconds
        send_message(chat_id, f"{result.output}\n\n{format_seconds(task_seconds)}")
    else:
        send_message(chat_id, format_seconds(result.timings.execution_seconds or result.elapsed_seconds))
    for index, attachment in enumerate(result.attachments):
        send_attachment(chat_id, result, index, attachment.path, attachment.label or result.tool_id)
    summarize_and_send_audio(chat_id, request, result)
    send_message(chat_id, "----------")


def process_message(text: str, chat_id: int | str) -> None:
    if process_confirmation_reply(text, chat_id):
        return
    send_message(chat_id, "Recibido\n0.1s")
    request = build_request(text, chat_id)
    result = ORCHESTRATOR.handle(request, progress_callback=progress_sender(chat_id))
    deliver_result(chat_id, request, result)


def process_update(update: dict) -> None:
    message = update.get("message") or update.get("edited_message") or {}
    chat_id = message.get("chat", {}).get("id")
    if not chat_id:
        return
    if str(chat_id) not in ALLOWED_CHAT_IDS:
        logging.warning("Unauthorized Telegram chat: %s", chat_id)
        return

    try:
        if process_confirmation_reply((message.get("text") or "").strip(), chat_id):
            return

        request = extract_message_text_and_request(message, chat_id)
        if request is None:
            return
        if request.metadata.get("source") == "voice":
            seconds = float(request.metadata.get("transcription_seconds", 0))
            send_message(chat_id, f"Transcrito\n{format_seconds(seconds)}")
        else:
            send_message(chat_id, "Recibido\n0.1s")
        result = ORCHESTRATOR.handle(request, progress_callback=progress_sender(chat_id))
        deliver_result(chat_id, request, result)
    except Exception as exc:
        logging.exception("Telegram update processing failed")
        if message.get("voice") or message.get("audio"):
            send_message(
                chat_id,
                "No he podido procesar la nota de voz. El servicio de transcripción no está disponible ahora mismo.",
            )
        else:
            send_message(chat_id, "No he podido completar la petición. El error quedó registrado para revisarlo.")


def friendly_error_message(result: OrchestratorResult) -> str:
    error = (result.error or result.output).casefold()
    if "invalid api key" in error or "401" in error or "unauthorized" in error:
        return "El proveedor seleccionado no tiene una clave válida. He registrado el fallo; prueba de nuevo en unos segundos."
    if "429" in error or "rate limit" in error:
        return "El proveedor está temporalmente saturado. Prueba de nuevo dentro de un momento."
    if "timeout" in error or "timed out" in error:
        return "La petición tardó demasiado y se canceló. Prueba otra vez con una instrucción más corta."
    return "No he podido completar la petición. El detalle técnico quedó guardado en el registro."


def message_chunks(text: str, limit: int = 3500) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return [""]
    chunks: list[str] = []
    remaining = cleaned
    while len(remaining) > limit:
        split_at = remaining.rfind("\n", 0, limit)
        if split_at < limit // 2:
            split_at = remaining.rfind(" ", 0, limit)
        if split_at < limit // 2:
            split_at = limit
        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks


def main() -> int:
    if not TOKEN or not ALLOWED_CHAT_IDS:
        logging.error("Missing Telegram token or allowed chat id.")
        return 1
    warm_voice_provider()
    send_message(next(iter(ALLOWED_CHAT_IDS)), "Orchestrator v2.1 Telegram Gateway activo.")
    offset = None
    while True:
        for update in get_updates(offset):
            offset = update["update_id"] + 1
            process_update(update)
        time.sleep(1)


if __name__ == "__main__":
    raise SystemExit(main())
