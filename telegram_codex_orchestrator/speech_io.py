from __future__ import annotations

import base64
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import wave
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from voice_state import VoiceState


@dataclass(slots=True)
class SpeechResult:
    path: Path
    provider: str
    detail: str


class SpeechIO:
    def __init__(self, runtime_dir: Path) -> None:
        self.runtime_dir = runtime_dir
        self.tts_dir = runtime_dir / "tts"
        self.incoming_dir = runtime_dir / "telegram_audio"
        self.tts_dir.mkdir(parents=True, exist_ok=True)
        self.incoming_dir.mkdir(parents=True, exist_ok=True)

    def transcribe_with_gemini(self, audio_path: Path, mime_type: str, api_key: str, model: str = "gemini-2.5-flash") -> str:
        if not api_key:
            raise RuntimeError("No hay API key de Gemini para transcribir audio")
        data = base64.b64encode(audio_path.read_bytes()).decode("ascii")
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                "Transcribe literalmente este audio en español. "
                                "Devuelve solo el texto, sin explicaciones."
                            )
                        },
                        {"inlineData": {"mimeType": mime_type or "audio/ogg", "data": data}},
                    ],
                }
            ],
            "generationConfig": {"temperature": 0},
        }
        response = self._post_json(
            "https://generativelanguage.googleapis.com/v1beta/models/"
            + urllib.parse.quote(model, safe="")
            + ":generateContent?key="
            + urllib.parse.quote(api_key, safe=""),
            payload,
            timeout=90,
        )
        parts = (((response.get("candidates") or [{}])[0].get("content") or {}).get("parts") or [])
        text = "".join(str(part.get("text", "")) for part in parts if isinstance(part, dict)).strip()
        if not text:
            raise RuntimeError("Gemini no devolvio transcripcion")
        return text

    def transcribe(self, audio_path: Path, mime_type: str, groq_api_key: str, gemini_api_key: str) -> str:
        errors: list[str] = []
        if groq_api_key:
            try:
                return self.transcribe_with_groq(audio_path, groq_api_key)
            except Exception as exc:
                errors.append(f"groq={exc}")
        if gemini_api_key:
            try:
                return self.transcribe_with_gemini(audio_path, mime_type, gemini_api_key)
            except Exception as exc:
                errors.append(f"gemini={exc}")
        raise RuntimeError("No se pudo transcribir audio. " + " | ".join(errors))

    def transcribe_with_groq(self, audio_path: Path, api_key: str, model: str = "whisper-large-v3-turbo") -> str:
        if not api_key:
            raise RuntimeError("No hay API key de Groq para transcribir audio")
        boundary = "----codex-groq-" + datetime.now().strftime("%Y%m%d%H%M%S%f")
        fields = {
            "model": model,
            "language": "es",
            "temperature": "0",
            "response_format": "verbose_json",
        }
        body: list[bytes] = []
        for key, value in fields.items():
            body.extend(
                [
                    f"--{boundary}\r\n".encode("ascii"),
                    f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"),
                    str(value).encode("utf-8"),
                    b"\r\n",
                ]
            )
        body.extend(
            [
                f"--{boundary}\r\n".encode("ascii"),
                f'Content-Disposition: form-data; name="file"; filename="{audio_path.name}"\r\n'.encode("utf-8"),
                b"Content-Type: application/octet-stream\r\n\r\n",
                audio_path.read_bytes(),
                b"\r\n",
                f"--{boundary}--\r\n".encode("ascii"),
            ]
        )
        request = urllib.request.Request(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            data=b"".join(body),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = json.loads(response.read().decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"Groq STT HTTP {exc.code}: {detail}") from exc
        text = str(payload.get("text", "")).strip()
        if not text:
            raise RuntimeError("Groq no devolvio transcripcion")
        return text

    def synthesize(self, text: str, state: VoiceState) -> SpeechResult:
        errors: list[str] = []
        order = self._ordered_backends(state)
        for backend in order:
            try:
                if backend == "gemini":
                    return self._synthesize_gemini(text, state)
                if backend == "groq":
                    return self._synthesize_groq(text, state)
                if backend == "kokoro":
                    return self._synthesize_kokoro(text, state)
                if backend == "piper":
                    return self._synthesize_piper(text, state)
            except Exception as exc:
                errors.append(f"{backend}: {exc}")
        raise RuntimeError("No se pudo generar audio. " + " | ".join(errors))

    def play(self, audio_path: Path) -> None:
        suffix = audio_path.suffix.lower()
        if suffix == ".wav":
            self._play_wav(audio_path)
            return
        self._play_default(audio_path)

    def _ordered_backends(self, state: VoiceState) -> list[str]:
        order = state.normalized_order()
        if state.tts_backend in order:
            order.remove(state.tts_backend)
        return [state.tts_backend, *order]

    def _synthesize_gemini(self, text: str, state: VoiceState) -> SpeechResult:
        if not state.gemini_api_key:
            raise RuntimeError("Gemini TTS no tiene API key")
        payload = {
            "contents": [{"parts": [{"text": text}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {"voiceName": state.gemini_voice}
                    }
                },
            },
        }
        response = self._post_json(
            "https://generativelanguage.googleapis.com/v1beta/models/"
            + urllib.parse.quote(state.gemini_model, safe="")
            + ":generateContent?key="
            + urllib.parse.quote(state.gemini_api_key, safe=""),
            payload,
            timeout=120,
        )
        parts = (((response.get("candidates") or [{}])[0].get("content") or {}).get("parts") or [])
        inline = parts[0].get("inlineData") if parts and isinstance(parts[0], dict) else None
        if not isinstance(inline, dict) or not inline.get("data"):
            raise RuntimeError("Gemini TTS no devolvio audio")
        pcm = base64.b64decode(str(inline["data"]))
        output_path = self.tts_dir / f"gemini_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.wav"
        self._write_pcm_wav(output_path, pcm, sample_rate=24000)
        return SpeechResult(output_path, "gemini", f"modelo={state.gemini_model}, voz={state.gemini_voice}")

    def _synthesize_groq(self, text: str, state: VoiceState) -> SpeechResult:
        if not state.groq_api_key:
            raise RuntimeError("Groq TTS no tiene API key")
        clean_text = " ".join(text.strip().split())
        if not clean_text:
            raise RuntimeError("No hay texto para sintetizar")
        if len(clean_text) > 200:
            clean_text = clean_text[:197].rstrip() + "..."
        payload = {
            "model": state.groq_model,
            "voice": state.groq_voice,
            "input": clean_text,
            "response_format": "wav",
        }
        request = urllib.request.Request(
            "https://api.groq.com/openai/v1/audio/speech",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {state.groq_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                audio = response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"Groq TTS HTTP {exc.code}: {detail}") from exc
        output_path = self.tts_dir / f"groq_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.wav"
        output_path.write_bytes(audio)
        return SpeechResult(output_path, "groq", f"modelo={state.groq_model}, voz={state.groq_voice}")

    def _synthesize_kokoro(self, text: str, state: VoiceState) -> SpeechResult:
        try:
            import numpy as np
            import soundfile as sf
            from kokoro_onnx import Kokoro
        except Exception as exc:
            raise RuntimeError(f"Kokoro no esta instalado en este entorno ({exc})") from exc

        model_path = self.runtime_dir.parent / "models" / "kokoro" / "kokoro-v1.0.onnx"
        voices_path = self.runtime_dir.parent / "models" / "kokoro" / "voices-v1.0.bin"
        self._ensure_kokoro_assets(model_path, voices_path)
        voices = np.load(voices_path)
        if state.kokoro_voice not in voices.files:
            raise RuntimeError(f"voz Kokoro no encontrada: {state.kokoro_voice}")
        output_path = self.tts_dir / f"kokoro_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.wav"
        pipeline = Kokoro(str(model_path), str(voices_path))
        audio, sample_rate = pipeline.create(text, voice=state.kokoro_voice, speed=1.0, lang="es")
        sf.write(output_path, audio, sample_rate)
        return SpeechResult(output_path, "kokoro", f"voz={state.kokoro_voice}")

    @staticmethod
    def _ensure_kokoro_assets(model_path: Path, voices_path: Path) -> None:
        model_path.parent.mkdir(parents=True, exist_ok=True)
        downloads = (
            (
                "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
                model_path,
            ),
            (
                "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
                voices_path,
            ),
        )
        for url, destination in downloads:
            if destination.is_file():
                continue
            with urllib.request.urlopen(url, timeout=600) as response:
                destination.write_bytes(response.read())

    def _synthesize_piper(self, text: str, state: VoiceState) -> SpeechResult:
        command = self._piper_command()
        if command is None:
            raise RuntimeError("Piper no esta disponible")
        model_dir = self.runtime_dir.parent / "models" / "piper"
        model_path = model_dir / f"{state.piper_voice}.onnx"
        config_path = model_dir / f"{state.piper_voice}.onnx.json"
        if not model_path.is_file():
            self._download_piper_assets(state.piper_voice, model_path, config_path)
        output_path = self.tts_dir / f"piper_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.wav"
        full_command = [*command, "--model", str(model_path), "--output_file", str(output_path)]
        if config_path.is_file():
            full_command.extend(["--config", str(config_path)])
        process = subprocess.run(
            full_command,
            input=(text.strip() + "\n").encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if process.returncode != 0:
            detail = process.stderr.decode("utf-8", errors="ignore").strip()
            raise RuntimeError(f"Piper fallo ({process.returncode}): {detail}")
        return SpeechResult(output_path, "piper", f"voz={state.piper_voice}")

    @staticmethod
    def _download_piper_assets(voice_name: str, model_path: Path, config_path: Path) -> None:
        if voice_name != "es_ES-davefx-medium":
            raise RuntimeError(f"falta modelo Piper: {model_path}")
        base = "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        for url, destination in (
            (base + "es_ES-davefx-medium.onnx?download=true", model_path),
            (base + "es_ES-davefx-medium.onnx.json?download=true", config_path),
        ):
            with urllib.request.urlopen(url, timeout=180) as response:
                destination.write_bytes(response.read())

    def _piper_command(self) -> list[str] | None:
        candidates = [
            [str(Path(sys.executable).with_name("piper.exe"))],
            ["piper"],
            ["piper.exe"],
            [sys.executable, "-m", "piper"],
        ]
        for candidate in candidates:
            executable = candidate[0]
            if executable == sys.executable:
                return candidate
            if Path(executable).exists() or shutil.which(executable):
                return candidate
        return None

    @staticmethod
    def _write_pcm_wav(output_path: Path, pcm: bytes, sample_rate: int) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(output_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm)

    @staticmethod
    def _post_json(url: str, payload: dict, timeout: int) -> dict:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))

    @staticmethod
    def _play_wav(audio_path: Path) -> None:
        escaped = str(audio_path).replace("'", "''")
        script = (
            "$ErrorActionPreference='Stop'; "
            "Add-Type -AssemblyName System; "
            f"$p=New-Object System.Media.SoundPlayer('{escaped}'); "
            "$p.PlaySync();"
        )
        subprocess.Popen(
            ["powershell", "-NoProfile", "-Command", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

    @staticmethod
    def _play_default(audio_path: Path) -> None:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-Command", f"Start-Process -FilePath '{str(audio_path).replace(chr(39), chr(39) + chr(39))}'"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

    def temp_download_path(self, suffix: str) -> Path:
        clean_suffix = suffix if suffix.startswith(".") else f".{suffix}"
        handle = tempfile.NamedTemporaryFile(prefix="telegram_audio_", suffix=clean_suffix, dir=self.incoming_dir, delete=False)
        handle.close()
        return Path(handle.name)
