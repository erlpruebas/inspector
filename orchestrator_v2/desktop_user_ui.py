from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from pathlib import Path
import queue
import re
import subprocess
import threading
import wave

from .models import TaskRequest
from .orchestrator import GestorOrquestador
from .response_voice import voice_text_for_response
from .router import choose_tool
from .settings import UserPreferences, load_user_preferences, save_user_preferences
from .voice_io import transcribe_with_fallback
from .workspace import workspace_for


RUNTIME_ROOT = Path("orchestrator_v2/runtime/desktop_ui")
PREFERENCES_FILE = RUNTIME_ROOT / "preferences.json"

YES_WORDS = {"si", "sí", "correcto", "adelante", "hazlo", "realiza", "confirmo", "vale", "ok", "okay"}
NO_WORDS = {"no", "cancelar", "cancela", "para", "detente", "espera", "incorrecto"}


class DesktopUserInterface:
    def __init__(self, user_id: str = "desktop", thread_id: str = "ui", sample_rate: int = 16_000):
        self.user_id = user_id
        self.thread_id = thread_id
        self.workspace = workspace_for(user_id, thread_id)
        self.sample_rate = sample_rate
        self.preferences = self._load_preferences()
        self.preferences.always_confirm_voice_orders = True
        self.preferences.privacy_default = "clear"
        save_user_preferences(PREFERENCES_FILE, self.preferences)

        self.recording = False
        self.awaiting_confirmation = False
        self.frames: "queue.Queue[bytes]" = queue.Queue()
        self.stream = None
        self.pending_text = ""
        self.pending_request: TaskRequest | None = None
        self.pending_tool = ""

        self._root = None
        self._button = None
        self._status_var = None

    def _load_preferences(self) -> UserPreferences:
        if PREFERENCES_FILE.exists():
            return load_user_preferences(PREFERENCES_FILE, self.user_id)
        prefs = UserPreferences(user_id=self.user_id)
        save_user_preferences(PREFERENCES_FILE, prefs)
        return prefs

    def run(self) -> None:
        import tkinter as tk

        root = tk.Tk()
        self._root = root
        root.title("Inspector voz")
        root.attributes("-topmost", True)
        root.geometry("190x150+18+820")
        root.resizable(False, False)
        root.configure(bg="#101412")

        self._status_var = tk.StringVar(value="Listo")
        self._button = tk.Button(
            root,
            text="GRABAR",
            command=self.toggle_recording,
            bg="#18a558",
            fg="white",
            activebackground="#148a49",
            activeforeground="white",
            font=("Segoe UI", 18, "bold"),
            relief="flat",
            bd=0,
        )
        self._button.pack(fill="both", expand=True, padx=12, pady=(12, 6))

        tk.Label(
            root,
            textvariable=self._status_var,
            bg="#101412",
            fg="#d6e6dc",
            font=("Segoe UI", 9),
        ).pack(fill="x", padx=12, pady=(0, 10))

        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.mainloop()

    def on_close(self) -> None:
        if self.recording:
            try:
                self.stop()
            except Exception:
                pass
        if self._root is not None:
            self._root.destroy()

    def toggle_recording(self) -> None:
        if self.recording:
            path = self.stop()
            self._set_button_waiting()
            threading.Thread(target=self._handle_voice, args=(path,), daemon=True).start()
            return
        try:
            self.start()
        except Exception as exc:
            self._show_status(f"Error micro: {type(exc).__name__}")
            self._speak(f"No pude iniciar la grabacion: {exc}")
            return
        self._set_button_recording()

    def _set_button_recording(self) -> None:
        self.recording = True
        if self._button is not None:
            self._button.configure(text="PARAR", bg="#c62828", activebackground="#a82020")
        self._show_status("Grabando")

    def _set_button_waiting(self) -> None:
        self.recording = False
        if self._button is not None:
            self._button.configure(text="GRABAR", bg="#18a558", activebackground="#148a49")
        self._show_status("Procesando")

    def _show_status(self, text: str) -> None:
        if self._status_var is not None:
            self._status_var.set(text)

    def start(self) -> None:
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise RuntimeError("sounddevice no esta instalado.") from exc
        self.recording = True
        self.frames = queue.Queue()

        def callback(indata, frames, time, status) -> None:
            if status:
                print(status)
            self.frames.put(bytes(indata))

        self.stream = sd.RawInputStream(samplerate=self.sample_rate, channels=1, dtype="int16", callback=callback)
        self.stream.start()

    def stop(self) -> Path:
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.recording = False
        path = self.workspace.inbox / f"voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        with wave.open(str(path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(self.sample_rate)
            while not self.frames.empty():
                wav.writeframes(self.frames.get())
        return path

    def _handle_voice(self, path: Path) -> None:
        try:
            text = transcribe_with_fallback(path).strip()
        except Exception as exc:
            self._after_ui(lambda: self._show_status("Fallo STT"))
            self._speak(f"No pude transcribir la nota de voz: {exc}")
            return
        if not text:
            self._after_ui(lambda: self._show_status("No entendi audio"))
            self._speak("No he entendido la nota de voz. Puedes repetirla.")
            return
        if self.awaiting_confirmation:
            self._handle_confirmation(text)
        else:
            self._prepare_order(text)

    def _prepare_order(self, text: str) -> None:
        request = TaskRequest(
            text=text,
            user_id=self.user_id,
            thread_id=self.thread_id,
            privacy_mode=self.preferences.privacy_default,
        )
        decision = choose_tool(request)
        self.pending_text = text
        self.pending_tool = self._tool_label(decision.tool_id)
        self.pending_request = replace(request, metadata={"source": "desktop_voice_ui", "desktop_send": True})
        self.awaiting_confirmation = True
        self._after_ui(lambda: self._show_status("Confirma por voz"))
        self._speak(
            f"He entendido: {text}. "
            f"A continuacion voy a utilizar {self.pending_tool}. "
            "Quieres que lo realice?"
        )

    def _handle_confirmation(self, text: str) -> None:
        decision = self._confirmation_decision(text)
        if decision == "yes":
            self.awaiting_confirmation = False
            self._after_ui(lambda: self._show_status("Ejecutando"))
            self._speak("De acuerdo. Lo ejecuto ahora.")
            self._execute_pending()
            return
        if decision == "no":
            self.awaiting_confirmation = False
            self.pending_request = None
            self.pending_text = ""
            self._after_ui(lambda: self._show_status("Cancelado"))
            self._speak("Cancelado. Espero una nueva orden.")
            return
        self._after_ui(lambda: self._show_status("Di si o no"))
        self._speak("No he entendido si quieres continuar. Di si para ejecutar o no para cancelar.")

    def _execute_pending(self) -> None:
        try:
            assert self.pending_request is not None
            result = GestorOrquestador().handle(self.pending_request)
            summary = result.output or result.error or "La tarea termino sin texto de respuesta."
            spoken = voice_text_for_response(summary)
            self._after_ui(lambda: self._show_status("Listo"))
            self._speak(spoken)
        except Exception as exc:
            self._after_ui(lambda: self._show_status("Error"))
            self._speak(f"Ha fallado la ejecucion: {exc}")
        finally:
            self.pending_request = None
            self.pending_text = ""
            self.pending_tool = ""

    @staticmethod
    def _confirmation_decision(text: str) -> str:
        words = set(re.findall(r"[a-zA-ZáéíóúÁÉÍÓÚñÑ]+", text.casefold()))
        normalized = {word.replace("í", "i") for word in words}
        if normalized & {word.replace("í", "i") for word in YES_WORDS}:
            return "yes"
        if normalized & NO_WORDS:
            return "no"
        return "unknown"

    def _speak(self, text: str) -> None:
        threading.Thread(target=self._speak_blocking, args=(text,), daemon=True).start()

    @staticmethod
    def _speak_blocking(text: str) -> None:
        clean = re.sub(r"\s+", " ", text).strip()
        if not clean:
            return
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.say(clean)
            engine.runAndWait()
            return
        except Exception:
            pass
        ps = (
            "Add-Type -AssemblyName System.Speech; "
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "$s.Speak($input)"
        )
        try:
            subprocess.run(["powershell", "-NoProfile", "-Command", ps], input=clean, text=True, timeout=120)
        except Exception:
            pass

    def _after_ui(self, callback) -> None:
        if self._root is None:
            callback()
            return
        self._root.after(0, callback)

    @staticmethod
    def _tool_label(tool_id: str) -> str:
        mapping = {
            "desktop_codex_operator": "Codex Desktop",
            "runtime_opencode_deepseek32": "OpenCode",
            "worker_openrouter_gpt54mini": "GPT-5.4 mini",
            "worker_openrouter_deepseek32": "DeepSeek V3.2",
            "worker_groq_compound_mini": "Groq Compound Mini",
            "gemini_flash_files": "Gemini Flash",
            "gemini_pro_long_context": "Gemini Pro",
            "premium_codex_55": "Codex GPT-5.5",
            "router_groq_qwen32": "Groq Qwen 32B",
            "router_groq_llama8": "Groq Llama 8B",
        }
        return mapping.get(tool_id, tool_id)


def main() -> int:
    DesktopUserInterface().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
