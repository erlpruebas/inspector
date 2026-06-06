from __future__ import annotations

import io
import asyncio
import json
import os
import subprocess
import wave
from pathlib import Path
from typing import Any

import requests
from benchmarks.env_utils import google_api_key, load_env_files


GROQ_STT_ENDPOINT = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_CHAT_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
TELEGRAM_FILE_ENDPOINT = "https://api.telegram.org/file/bot{token}/{path}"
TELEGRAM_GET_FILE_ENDPOINT = "https://api.telegram.org/bot{token}/getFile"
ELEVENLABS_TTS_ENDPOINT = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
ELEVENLABS_VOICES = {
    "adam": "pNInz6obpgDQGcFmaJgB",
    "george": "JBFqnCBsd6RMkjVDRZzb",
    "sarah": "EXAVITQu4vr4xnSDxMaL",
    "alice": "Xb7hH8MSUJpSbSDYk0k2",
    "matilda": "XrExE9yKIg1WjnnlVkGX",
    "lily": "pFZP5JQG7iQjIQuC4Bku",
    "jessica": "cgSgspJ2msm6clMCkdW9",
    "laura": "FGY2WhTYpPnrIDTdsKH5",
}


def download_telegram_file(token: str, file_id: str, target_dir: Path, *, suffix: str = ".ogg") -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    response = requests.get(
        TELEGRAM_GET_FILE_ENDPOINT.format(token=token),
        params={"file_id": file_id},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    file_path = payload.get("result", {}).get("file_path")
    if not file_path:
        raise RuntimeError("Telegram did not return a file path.")
    file_name = Path(file_path).name
    output_path = target_dir / file_name
    if output_path.suffix.lower() != suffix.lower() and suffix:
        output_path = output_path.with_suffix(suffix)
    file_response = requests.get(
        TELEGRAM_FILE_ENDPOINT.format(token=token, path=file_path),
        timeout=120,
    )
    file_response.raise_for_status()
    output_path.write_bytes(file_response.content)
    return output_path


def transcribe_audio_file(audio_path: Path, *, language: str = "es", prompt: str = "") -> str:
    load_env_files()
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing GROQ_API_KEY for speech transcription.")
    model = os.getenv("ORCH_GROQ_STT_MODEL", "whisper-large-v3-turbo").strip() or "whisper-large-v3-turbo"
    with audio_path.open("rb") as handle:
        files = {"file": (audio_path.name, handle, "application/octet-stream")}
        data = {
            "model": model,
            "response_format": "text",
            "temperature": "0",
        }
        if language:
            data["language"] = language
        if prompt:
            data["prompt"] = prompt[:800]
        response = requests.post(
            GROQ_STT_ENDPOINT,
            headers={"Authorization": f"Bearer {api_key}"},
            files=files,
            data=data,
            timeout=180,
        )
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        payload = response.json()
        if isinstance(payload, dict):
            if isinstance(payload.get("text"), str):
                return payload["text"].strip()
            return json.dumps(payload, ensure_ascii=False)
    return response.text.strip()


def build_voice_summary_text(answer_text: str, *, user_request: str = "", language: str = "es") -> str:
    load_env_files()
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return fallback_voice_summary(answer_text)

    model = os.getenv("ORCH_VOICE_SUMMARY_MODEL", "llama-3.1-8b-instant").strip() or "llama-3.1-8b-instant"
    prompt = f"""
Resume la respuesta para audio en {language}.

Reglas:
- Escribe en espanol natural y conversado.
- Maximo dos parrafos.
- Sin viñetas.
- No menciones que eres un modelo.
- Mantén el tono agradable y directo para escuchar por Telegram.

Peticion original:
{user_request}

Respuesta obtenida:
{answer_text}
""".strip()
    prompt += """

Reglas de estilo prioritarias:
- Empieza directamente por la informacion util.
- No empieces con "claro", "entiendo", "te interesa", elogios ni una reformulacion de la peticion.
- No cierres con una pregunta ni con una oferta de ayuda.
""".rstrip()
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Eres un redactor de resúmenes orales breves para Telegram."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 220,
    }
    try:
        response = requests.post(
            GROQ_CHAT_ENDPOINT,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=payload,
            timeout=90,
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices") or []
        if choices:
            content = (((choices[0] or {}).get("message") or {}).get("content") or "").strip()
            if content:
                return normalize_voice_summary(content)
    except Exception:
        pass
    return fallback_voice_summary(answer_text)


def synthesize_voice_summary(
    summary_text: str,
    output_path: Path,
    *,
    voice_name: str | None = None,
    provider: str = "gemini",
) -> Path:
    if provider.casefold() == "edge":
        return synthesize_edge_voice(summary_text, output_path, voice_name=voice_name)
    if provider.casefold() == "elevenlabs":
        return synthesize_elevenlabs_voice(summary_text, output_path, voice_name=voice_name)

    load_env_files()
    api_key = google_api_key()
    if not api_key:
        raise RuntimeError("Missing GOOGLE_API_KEY/GEMINI_API_KEY for text-to-speech.")
    voice = voice_name or os.getenv("ORCH_GEMINI_TTS_VOICE", "Kore").strip() or "Kore"

    try:
        from google import genai
        from google.genai import types
    except Exception as exc:
        raise RuntimeError(f"Gemini SDK unavailable: {exc}") from exc

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=os.getenv("ORCH_GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts").strip() or "gemini-2.5-flash-preview-tts",
        contents=summary_text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice,
                    )
                )
            ),
        ),
    )
    try:
        audio_data = response.candidates[0].content.parts[0].inline_data.data
    except Exception as exc:
        raise RuntimeError(f"Gemini TTS returned no audio: {exc}") from exc

    pcm_bytes = audio_data if isinstance(audio_data, (bytes, bytearray)) else bytes(audio_data)
    write_wave_file(output_path, pcm_bytes)
    return output_path


def synthesize_edge_voice(summary_text: str, output_path: Path, *, voice_name: str | None = None) -> Path:
    try:
        import edge_tts
    except Exception as exc:
        raise RuntimeError(f"Edge TTS unavailable: {exc}") from exc

    voice = voice_name or "es-ES-ElviraNeural"
    mp3_path = output_path.with_suffix(".mp3")
    mp3_path.parent.mkdir(parents=True, exist_ok=True)

    async def generate() -> None:
        await edge_tts.Communicate(summary_text, voice).save(str(mp3_path))

    asyncio.run(generate())
    return mp3_path


def synthesize_elevenlabs_voice(
    summary_text: str,
    output_path: Path,
    *,
    voice_name: str | None = None,
) -> Path:
    load_env_files()
    api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing ELEVENLABS_API_KEY for text-to-speech.")

    requested_voice = (voice_name or "Adam").strip()
    voice_id = ELEVENLABS_VOICES.get(requested_voice.casefold(), requested_voice)
    model = os.getenv("ELEVENLABS_TTS_MODEL", "eleven_flash_v2_5").strip() or "eleven_flash_v2_5"
    response = requests.post(
        ELEVENLABS_TTS_ENDPOINT.format(voice_id=voice_id),
        headers={
            "xi-api-key": api_key,
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
        },
        params={"output_format": "mp3_22050_32"},
        json={
            "text": summary_text,
            "model_id": model,
            "language_code": "es",
            "voice_settings": {
                "stability": 0.4,
                "similarity_boost": 0.7,
                "style": 0.0,
                "use_speaker_boost": False,
            },
        },
        timeout=90,
    )
    response.raise_for_status()
    mp3_path = output_path.with_suffix(".mp3")
    mp3_path.parent.mkdir(parents=True, exist_ok=True)
    mp3_path.write_bytes(response.content)
    return mp3_path


def write_wave_file(filename: Path, pcm: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2) -> None:
    filename.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(filename), "wb") as handle:
        handle.setnchannels(channels)
        handle.setsampwidth(sample_width)
        handle.setframerate(rate)
        handle.writeframes(pcm)


def play_audio_file(audio_path: Path) -> subprocess.Popen:
    resolved = audio_path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(resolved)
    escaped = str(resolved).replace("'", "''")
    if resolved.suffix.casefold() == ".wav":
        script = f"$player = New-Object System.Media.SoundPlayer('{escaped}'); $player.PlaySync()"
    else:
        script = (
            "Add-Type -AssemblyName PresentationCore; "
            "$player = New-Object System.Windows.Media.MediaPlayer; "
            f"$player.Open([Uri]'{escaped}'); "
            "$player.Play(); "
            "while (-not $player.NaturalDuration.HasTimeSpan) { Start-Sleep -Milliseconds 50 }; "
            "Start-Sleep -Milliseconds ([int]$player.NaturalDuration.TimeSpan.TotalMilliseconds + 200); "
            "$player.Close()"
        )
    return subprocess.Popen(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def normalize_voice_summary(text: str) -> str:
    paragraphs = []
    for block in text.replace("\r\n", "\n").replace("\r", "\n").split("\n\n"):
        cleaned = " ".join(block.split()).strip()
        if cleaned:
            paragraphs.append(cleaned)
    if len(paragraphs) > 2:
        paragraphs = paragraphs[:2]
    cleaned = "\n\n".join(paragraphs).strip()
    if len(cleaned) > 1200:
        cleaned = cleaned[:1200].rsplit(" ", 1)[0].strip()
    return cleaned


def fallback_voice_summary(answer_text: str) -> str:
    cleaned = " ".join(answer_text.split())
    if not cleaned:
        return "Te dejo el resumen: no hubo contenido suficiente para narrar."
    if len(cleaned) <= 500:
        return cleaned
    first = cleaned[:500].rsplit(" ", 1)[0].strip()
    remainder = cleaned[500:]
    second = remainder[:400].rsplit(" ", 1)[0].strip()
    if second:
        return f"{first}\n\n{second}"
    return first
