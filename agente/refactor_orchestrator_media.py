import re
from pathlib import Path

file_path = Path("D:/inspector/agente/telegram_codex_orchestrator/orchestrator.py")
text = file_path.read_text(encoding="utf-8")

target = """            if result.ok:
                self._reply(chat_id, response, thread=thread_record.name)
                self._send_codex_desktop_screenshot(chat_id, result, thread_record)
                return"""

replacement = """            if result.ok:
                # 1. Enviar el texto como respuesta al chat
                self._reply(chat_id, response, thread=thread_record.name)
                # 2. Enviar la captura de pantalla
                self._send_codex_desktop_screenshot(chat_id, result, thread_record)
                # 3. Generar y enviar el audio si hay un resumen narrativo de Gemini
                if vision_narrative:
                    try:
                        audio_res = self.speech_io.synthesize(vision_narrative, self.voice_state)
                        self.telegram.send_audio(chat_id, audio_res.path)
                    except Exception as e:
                        self.memory.write("codex_desktop_tts_error", str(e), "system", thread=thread_record.name)
                return"""

text = text.replace(target, replacement)
file_path.write_text(text, encoding="utf-8")
print("Multimedia logic injected into orchestrator.py successfully.")
