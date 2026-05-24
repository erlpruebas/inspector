import base64
import ctypes
import json
import subprocess
import threading
import time
import urllib.request
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, Button, Entry, Frame, Label, Text, Tk, messagebox

import sounddevice as sd
import soundfile as sf


ROOT = Path(__file__).resolve().parent
MEDIA_DIR = ROOT / "assistant" / "media" / "desktop"
SERVER_URL = "http://127.0.0.1:8787"
THREAD_ID = "desktop-tkinter"


class MciPlayer:
    def __init__(self):
        self.alias = "inspectorvoice"

    def play(self, path):
        self.stop()
        winmm = ctypes.windll.winmm
        winmm.mciSendStringW(f'open "{path}" type mpegvideo alias {self.alias}', None, 0, None)
        winmm.mciSendStringW(f"play {self.alias}", None, 0, None)

    def stop(self):
        winmm = ctypes.windll.winmm
        winmm.mciSendStringW(f"stop {self.alias}", None, 0, None)
        winmm.mciSendStringW(f"close {self.alias}", None, 0, None)


class DesktopAssistant:
    def __init__(self):
        MEDIA_DIR.mkdir(parents=True, exist_ok=True)
        self.root = Tk()
        self.root.title("Inspector")
        self.root.attributes("-topmost", True)
        self.root.geometry("430x260+24+560")
        self.root.configure(bg="#101820")

        self.player = MciPlayer()
        self.recording = False
        self.frames = []
        self.stream = None
        self.sample_rate = 16000

        self.status = Label(
            self.root,
            text="Listo",
            bg="#101820",
            fg="#f2f6f9",
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        )
        self.status.pack(fill="x", padx=14, pady=(12, 4))

        self.reply = Text(
            self.root,
            height=6,
            wrap="word",
            bg="#f7f4ec",
            fg="#172026",
            relief="flat",
            font=("Segoe UI", 10),
        )
        self.reply.pack(fill=BOTH, expand=True, padx=14, pady=6)
        self.reply.insert(END, "Pulsa REC o escribe una peticion abajo.")

        bottom = Frame(self.root, bg="#101820")
        bottom.pack(fill="x", padx=14, pady=(4, 14))

        self.record_button = Button(
            bottom,
            text="REC",
            command=self.toggle_recording,
            width=5,
            height=2,
            bg="#d94f30",
            fg="white",
            activebackground="#ef6a4d",
            relief="flat",
            font=("Segoe UI", 14, "bold"),
        )
        self.record_button.pack(side=LEFT)

        self.entry = Entry(
            bottom,
            bg="#ffffff",
            fg="#172026",
            relief="flat",
            font=("Segoe UI", 11),
        )
        self.entry.pack(side=LEFT, fill="x", expand=True, padx=(10, 8), ipady=10)
        self.entry.bind("<Return>", self.send_text_event)

        self.send_button = Button(
            bottom,
            text="Enviar",
            command=self.send_text,
            bg="#2f6f73",
            fg="white",
            activebackground="#3f878b",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
        )
        self.send_button.pack(side=RIGHT)

        threading.Thread(target=self.ensure_server, daemon=True).start()
        self.root.after(5000, self.poll_alarms)

    def set_status(self, text):
        self.root.after(0, lambda: self.status.config(text=text))

    def set_reply(self, text):
        def update():
            self.reply.delete("1.0", END)
            self.reply.insert(END, text)

        self.root.after(0, update)

    def request_json(self, method, path, payload=None, timeout=240):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{SERVER_URL}{path}",
            data=data,
            method=method,
            headers={"content-type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def ensure_server(self):
        try:
            self.request_json("GET", "/api/assistant/state", timeout=3)
            return
        except Exception:
            self.set_status("Arrancando gestor...")

        subprocess.Popen(
            ["cmd.exe", "/c", "npm start"],
            cwd=str(ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        for _ in range(40):
            try:
                self.request_json("GET", "/api/assistant/state", timeout=2)
                self.set_status("Listo")
                return
            except Exception:
                time.sleep(0.5)
        self.set_status("No pude arrancar el gestor")

    def toggle_recording(self):
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        self.frames = []
        self.recording = True
        self.record_button.config(text="STOP", bg="#9f2d20")
        self.set_status("Grabando...")
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            callback=self.audio_callback,
        )
        self.stream.start()

    def audio_callback(self, indata, frames, time_info, status):
        if self.recording:
            self.frames.append(indata.copy())

    def stop_recording(self):
        self.recording = False
        self.record_button.config(text="REC", bg="#d94f30")
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        audio_path = MEDIA_DIR / f"recording-{int(time.time())}.wav"
        if not self.frames:
            self.set_status("No hay audio")
            return
        sf.write(str(audio_path), self.frames_to_array(), self.sample_rate)
        threading.Thread(target=self.process_audio, args=(audio_path,), daemon=True).start()

    def frames_to_array(self):
        import numpy as np

        return np.concatenate(self.frames, axis=0)

    def send_text_event(self, event):
        self.send_text()
        return "break"

    def send_text(self):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, END)
        threading.Thread(target=self.process_text, args=(text,), daemon=True).start()

    def process_audio(self, audio_path):
        try:
            self.set_status("Transcribiendo...")
            payload = {
                "source": "desktop",
                "threadId": THREAD_ID,
                "language": "es",
                "preferGroq": True,
                "audio": {
                    "name": audio_path.name,
                    "mimeType": "audio/wav",
                    "base64": base64.b64encode(audio_path.read_bytes()).decode("ascii"),
                },
            }
            result = self.request_json("POST", "/api/assistant/transcribe", payload)
            text = result["transcription"]["text"]
            self.process_text(text, from_audio=True)
        except Exception as error:
            self.set_status("Error")
            self.set_reply(str(error))

    def process_text(self, text, from_audio=False):
        try:
            self.set_status("Procesando...")
            result = self.request_json(
                "POST",
                "/api/assistant/message",
                {
                    "source": "desktop",
                    "threadId": THREAD_ID,
                    "label": "Desktop",
                    "text": text,
                    "language": "es",
                    "preferGroq": True,
                    "synthesize": False,
                },
            )
            reply = result.get("reply") or ""
            prefix = "Transcripcion:\n" + text + "\n\n" if from_audio else ""
            self.set_reply(prefix + reply)
            self.set_status("Generando voz...")
            voice_text = result.get("voiceText") or reply
            speech_result = self.request_json(
                "POST",
                "/api/assistant/speech",
                {
                    "source": "desktop",
                    "threadId": THREAD_ID,
                    "label": "Desktop",
                    "text": voice_text,
                    "forceFull": bool(result.get("forceFullVoice")),
                    "notifyTelegram": True,
                    "notifyText": reply,
                },
            )
            self.play_speech(speech_result.get("speech"))
            self.set_status("Listo")
        except Exception as error:
            self.set_status("Error")
            self.set_reply(str(error))

    def play_speech(self, speech):
        if not speech or not speech.get("base64"):
            return
        extension = ".mp3" if "mpeg" in speech.get("mimeType", "") else ".wav"
        path = MEDIA_DIR / f"speech-{int(time.time())}{extension}"
        path.write_bytes(base64.b64decode(speech["base64"]))
        self.player.play(str(path))

    def poll_alarms(self):
        # The Node runtime is the alarm owner: it marks alarms as delivered,
        # plays the local speaker, and sends Telegram text plus audio.
        self.root.after(15000, self.poll_alarms)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    try:
        DesktopAssistant().run()
    except Exception as exc:
        messagebox.showerror("Inspector", str(exc))
