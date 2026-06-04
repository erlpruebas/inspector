from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from tkinter import Button, Label, Tk, messagebox
from typing import Any

from orchestrator_v2.desktop_calibration_store import (
    DEFAULT_CALIBRATION_FILE,
    machine_calibration_file,
    machine_name,
    tracked_machine_calibration_file,
)

RUNTIME_ROOT = machine_calibration_file().parent
CALIBRATION_FILE = machine_calibration_file()
TRACKED_CALIBRATION_FILE = tracked_machine_calibration_file()
SNAPSHOT_DIR = RUNTIME_ROOT / "calibration_snapshots"


STEPS = [
    ("sidebar_toggle", "Haz clic en el boton del panel lateral izquierdo (arriba a la izquierda)"),
    ("new_chat", "Haz clic en Nuevo chat (panel lateral abierto)"),
    ("initial_input", "Haz clic en la caja de texto (en el medio)"),
    ("initial_send", "Haz clic en el boton de enviar (en el medio)"),
    ("browser_toggle", "Haz clic en el boton del panel lateral (navegador)"),
    ("browser_input", "Haz clic en la caja de texto (panel activado)"),
    ("browser_send_stop", "Haz clic en el boton de enviar (panel activado)"),
]


class Calibrator:
    def __init__(self, window_title_hint: str = "Codex Desktop") -> None:
        self.window_title_hint = window_title_hint
        self.step_index = 0
        existing = load_calibration()
        self.points: dict[str, dict[str, Any]] = existing.get("points", {}) if existing else {}
        self.root = Tk()
        self.root.title("Calibrar Codex Desktop")
        self.root.geometry("420x220+80+80")
        self.root.attributes("-topmost", True)
        
        self.label = Label(self.root, text="Elige una opción:", font=("Segoe UI", 12), wraplength=380, justify="center")
        self.label.pack(padx=18, pady=14)
        
        self.btn_calibrate = Button(self.root, text="Calibrar", command=self.start_calibration)
        self.btn_calibrate.pack(pady=4)
        
        self.btn_verify = Button(self.root, text="Comprobar calibración", command=self.start_verification)
        self.btn_verify.pack(pady=4)

        self.btn_close = Button(self.root, text="Cerrar", command=self.root.destroy)
        self.btn_close.pack(pady=4)
        
        self.action_button = Button(self.root, text="")
        self.mode = None

    def start_calibration(self) -> None:
        self.mode = "calibrate"
        self.points = {}
        self.step_index = 0
        self.btn_calibrate.pack_forget()
        self.btn_verify.pack_forget()
        self.btn_close.pack_forget()
        if hasattr(self, "btn_save"):
            self.btn_save.pack_forget()
        if hasattr(self, "btn_recalibrate"):
            self.btn_recalibrate.pack_forget()
        self.action_button.config(text="Preparar siguiente clic", command=self.prepare_next)
        self.action_button.pack(pady=8)
        self.update_label()
        
    def start_verification(self) -> None:
        self.mode = "verify"
        self.step_index = 0
        self.btn_calibrate.pack_forget()
        self.btn_verify.pack_forget()
        self.btn_close.pack_forget()
        self.action_button.config(text="Siguiente", command=self.next_verification)
        self.action_button.pack(pady=8)
        self.next_verification()

    def next_verification(self) -> None:
        if self.step_index >= len(STEPS):
            self.label.config(text="Verificacion completada.")
            self.action_button.config(text="Cerrar", command=self.root.destroy)
            return
            
        key, text = STEPS[self.step_index]
        self.label.config(text=f"Verificando:\n{text}")
        self.root.update()
        
        pt = self.points.get(key)
        if pt:
            import pyautogui
            import time
            pyautogui.moveTo(pt["x"], pt["y"], duration=0.4)
            time.sleep(0.5)
        else:
            self.label.config(text=f"No hay calibracion para:\n{text}")
            
        self.step_index += 1

    def update_label(self) -> None:
        if self.step_index >= len(STEPS):
            self.label.config(text="Calibracion terminada.\n¿Que deseas hacer?")
            self.action_button.pack_forget()
            
            if not hasattr(self, "btn_save"):
                self.btn_save = Button(self.root, text="Guardar calibracion", bg="green", fg="white", command=self._handle_save)
            self.btn_save.pack(pady=4)
            
            if not hasattr(self, "btn_recalibrate"):
                self.btn_recalibrate = Button(self.root, text="Volver a calibrar", command=self.start_calibration)
            self.btn_recalibrate.pack(pady=4)
            
            self.btn_close.config(text="Salir sin guardar")
            self.btn_close.pack(pady=4)
            return
        _key, text = STEPS[self.step_index]
        self.label.config(text=f"Paso {self.step_index + 1}/{len(STEPS)}\n{text}\n\nPulsa el boton de abajo y tu SIGUIENTE clic se registrara.")

    def _handle_save(self) -> None:
        self.write_calibration()
        self.label.config(text="Calibracion guardada correctamente.")
        self.btn_save.pack_forget()
        self.btn_recalibrate.pack_forget()
        self.btn_close.config(text="Cerrar", command=self.root.destroy)

    def prepare_next(self) -> None:
        if self.step_index >= len(STEPS):
            return
        self.action_button.config(state="disabled", text="Esperando clic...")
        
        import pynput.mouse
        def on_click(x, y, button, pressed):
            if pressed and button == pynput.mouse.Button.left:
                self.root.after(10, lambda: self._on_clicked(x, y))
                return False
                
        listener = pynput.mouse.Listener(on_click=on_click)
        listener.start()

    def _on_clicked(self, x, y) -> None:
        import pyautogui
        try:
            r, g, b = pyautogui.pixel(int(x), int(y))
            color = [r, g, b]
        except Exception:
            color = [0, 0, 0]

        key, label = STEPS[self.step_index]
        self.points[key] = {
            "x": int(x),
            "y": int(y),
            "color": color,
            "label": label,
            "captured_at": datetime.now().isoformat(timespec="seconds"),
        }
        save_snapshot(key)
        self.step_index += 1
        self.action_button.config(state="normal", text="Preparar siguiente clic")
        self.update_label()

    def write_calibration(self) -> None:
        RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "window_title_hint": self.window_title_hint,
            "machine_name": machine_name(),
            "points": self.points,
            "notes": "Coordenadas absolutas de pantalla para Codex Desktop.",
        }
        CALIBRATION_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        TRACKED_CALIBRATION_FILE.parent.mkdir(parents=True, exist_ok=True)
        TRACKED_CALIBRATION_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        DEFAULT_CALIBRATION_FILE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_CALIBRATION_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def run(self) -> None:
        self.root.mainloop()


def current_mouse_position() -> tuple[int, int]:
    import pyautogui

    pos = pyautogui.position()
    return int(pos.x), int(pos.y)


def save_snapshot(key: str) -> None:
    try:
        from PIL import ImageGrab
    except ImportError:
        return
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    image = ImageGrab.grab()
    image.save(SNAPSHOT_DIR / f"{key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")


def load_calibration() -> dict[str, Any]:
    if not CALIBRATION_FILE.exists():
        return {}
    return json.loads(CALIBRATION_FILE.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Calibra coordenadas fijas de Codex Desktop.")
    parser.add_argument("--show", action="store_true", help="Muestra la calibracion actual.")
    args = parser.parse_args()
    if args.show:
        print(json.dumps(load_calibration(), indent=2, ensure_ascii=False))
        return 0
    Calibrator().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
