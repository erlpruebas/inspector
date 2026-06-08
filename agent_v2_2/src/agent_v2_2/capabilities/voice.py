import os
import requests
import json
import asyncio
from pathlib import Path
from ..config import load_config
import logging
import subprocess

logger = logging.getLogger("agent_v2_2.capabilities.voice")

class VoiceCapabilities:
    def __init__(self):
        # We assume load_env_files() has been called or dotenv is active.
        self.groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
        
    def transcribe_audio_file(self, audio_path: Path, language: str = "es", prompt: str = "") -> str:
        """
        Transcribe un archivo de audio usando Groq Whisper (vía rápida)
        """
        if not self.groq_api_key:
            raise RuntimeError("Missing GROQ_API_KEY for speech transcription.")
            
        model = os.getenv("ORCH_GROQ_STT_MODEL", "whisper-large-v3-turbo").strip()
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
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {self.groq_api_key}"},
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

    def summarize_for_voice(self, answer_text: str, user_request: str = "", language: str = "es") -> str:
        """
        Resume la respuesta de texto a un formato adecuado para voz (usualmente con Groq Llama 3)
        """
        if not self.groq_api_key:
            return self._fallback_voice_summary(answer_text)

        model = os.getenv("ORCH_VOICE_SUMMARY_MODEL", "llama-3.1-8b-instant").strip()
        prompt = f"""
Resume la respuesta para audio en {language}.

Reglas:
- Escribe en español natural y conversado.
- Máximo dos párrafos.
- Sin viñetas.
- No menciones que eres un modelo.
- Mantén el tono agradable y directo para escuchar por Telegram.

Petición original:
{user_request}

Respuesta obtenida:
{answer_text}

Reglas de estilo prioritarias:
- Empieza directamente por la información útil.
- No empieces con "claro", "entiendo", "te interesa", elogios ni una reformulación de la petición.
- No cierres con una pregunta ni con una oferta de ayuda.
""".strip()
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
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_api_key}",
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
                    return self._normalize_voice_summary(content)
        except Exception as exc:
            logger.warning(f"Voice summary generation failed: {exc}")
        return self._fallback_voice_summary(answer_text)

    def _normalize_voice_summary(self, text: str) -> str:
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

    def _fallback_voice_summary(self, answer_text: str) -> str:
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

    def synthesize_voice(self, text: str, output_path: Path, provider: str = "edge", voice_name: str = "") -> Path:
        """Sintetiza la voz usando Edge TTS por defecto u otros proveedores si se especifica."""
        provider = provider.casefold()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if provider == "edge":
            return self._synthesize_edge(text, output_path, voice_name)
        elif provider == "gemini":
            return self._synthesize_gemini(text, output_path, voice_name)
        elif provider == "elevenlabs":
            return self._synthesize_elevenlabs(text, output_path, voice_name)
        else:
            return self._synthesize_edge(text, output_path, voice_name)
            
    def _synthesize_edge(self, text: str, output_path: Path, voice_name: str) -> Path:
        try:
            import edge_tts
        except Exception as exc:
            raise RuntimeError(f"Edge TTS unavailable: {exc}") from exc

        voice = voice_name or "es-ES-ElviraNeural"
        mp3_path = output_path.with_suffix(".mp3")

        async def generate() -> None:
            await edge_tts.Communicate(text, voice).save(str(mp3_path))

        asyncio.run(generate())
        return mp3_path
        
    def _synthesize_gemini(self, text: str, output_path: Path, voice_name: str) -> Path:
        if not self.gemini_api_key:
            raise RuntimeError("Missing GEMINI_API_KEY for text-to-speech.")
        voice = voice_name or os.getenv("ORCH_GEMINI_TTS_VOICE", "Kore").strip()
        
        try:
            from google import genai
            from google.genai import types
        except Exception as exc:
            raise RuntimeError(f"Gemini SDK unavailable: {exc}") from exc

        client = genai.Client(api_key=self.gemini_api_key)
        response = client.models.generate_content(
            model=os.getenv("ORCH_GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts").strip() or "gemini-2.5-flash-preview-tts",
            contents=text,
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
        import wave
        wav_path = output_path.with_suffix(".wav")
        with wave.open(str(wav_path), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(24000)
            handle.writeframes(pcm_bytes)
        return wav_path

    def _synthesize_elevenlabs(self, text: str, output_path: Path, voice_name: str) -> Path:
        if not self.elevenlabs_api_key:
            raise RuntimeError("Missing ELEVENLABS_API_KEY for text-to-speech.")

        voice_id = "pNInz6obpgDQGcFmaJgB" # default Adam
        # mapping in reality can be much larger, simplified for skeleton
        
        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": self.elevenlabs_api_key,
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
            },
            params={"output_format": "mp3_22050_32"},
            json={
                "text": text,
                "model_id": "eleven_flash_v2_5",
                "language_code": "es",
            },
            timeout=90,
        )
        response.raise_for_status()
        mp3_path = output_path.with_suffix(".mp3")
        mp3_path.write_bytes(response.content)
        return mp3_path

    def play_audio_file(self, audio_path: Path) -> subprocess.Popen:
        """Reproduce un fichero de audio usando el altavoz local (Windows powershell script)"""
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
