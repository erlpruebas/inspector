from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Protocol


class Transcriber(Protocol):
    def transcribe(self, audio_path: Path) -> str:
        ...


@dataclass
class LocalWhisperTranscriber:
    model_size: str = "large-v3"
    device: str = "auto"
    compute_type: str = "auto"

    def transcribe(self, audio_path: Path) -> str:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError("faster-whisper no esta instalado; no puedo usar Whisper local.") from exc
        model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
        segments, _info = model.transcribe(str(audio_path), vad_filter=True)
        return " ".join(segment.text.strip() for segment in segments).strip()


@dataclass
class GroqWhisperTranscriber:
    api_key: str
    model: str = "whisper-large-v3-turbo"

    def transcribe(self, audio_path: Path) -> str:
        try:
            import requests
        except ImportError as exc:
            raise RuntimeError("requests no esta instalado; no puedo llamar a Groq Whisper.") from exc
        with audio_path.open("rb") as handle:
            response = requests.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                files={"file": (audio_path.name, handle, "application/octet-stream")},
                data={"model": self.model},
                timeout=120,
            )
        response.raise_for_status()
        data = response.json()
        return str(data.get("text", "")).strip()


def default_transcriber() -> Transcriber:
    if os.getenv("ORCH_STT_PRIMARY", "local").casefold().startswith("local"):
        return LocalWhisperTranscriber(model_size=os.getenv("ORCH_LOCAL_WHISPER_MODEL", "large-v3"))
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise RuntimeError("No hay GROQ_API_KEY para usar Groq Whisper.")
    return GroqWhisperTranscriber(api_key=api_key)


def transcribe_with_fallback(audio_path: Path) -> str:
    try:
        return default_transcriber().transcribe(audio_path)
    except Exception as first_error:
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            raise
        try:
            return GroqWhisperTranscriber(api_key=api_key).transcribe(audio_path)
        except Exception as second_error:
            raise RuntimeError(f"STT fallo local y fallback Groq: {first_error}; {second_error}") from second_error
