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
    ("new_chat", "Haz clic en Nuevo chat"),
    ("input_box", "Haz clic dentro de la caja de texto"),
    ("send_button", "Haz clic en el boton de enviar"),
]


class Calibrator:
    def __init__(self, window_title_hint: str = "Codex Desktop") -> None:
        self.window_title_hint = window_title_hint
        self.step_index = 0
        self.points: dict[str, dict[str, Any]] = {}
        self.root = Tk()
        self.root.title("Calibrar Codex Desktop")
        self.root.geometry("420x170+80+80")
        self.root.attributes("-topmost", True)
        self.label = Label(self.root, text="", font=("Segoe UI", 12), wraplength=380, justify="left")
        self.label.pack(padx=18, pady=14)
        self.button = Button(self.root, text="Capturar siguiente clic", command=self.capture_next)
        self.button.pack(pady=8)
        self.update_label()

    def update_label(self) -> None:
        if self.step_index >= len(STEPS):
            self.label.config(text="Calibracion completada.")
            self.button.config(text="Cerrar", command=self.root.destroy)
            return
        key, text = STEPS[self.step_index]
        self.label.config(
            text=f"Paso {self.step_index + 1}/{len(STEPS)}\n{text}\n\n"
            "Al pulsar el boton, tienes 3 segundos para colocar el raton y hacer clic."
        )

    def capture_next(self) -> None:
        if self.step_index >= len(STEPS):
            self.root.destroy()
            return
        key, label = STEPS[self.step_index]
        self.root.withdraw()
        time.sleep(0.3)
        messagebox.showinfo("Calibracion", f"{label}.\n\nTienes 3 segundos.")
        time.sleep(3.0)
        point = current_mouse_position()
        self.points[key] = {
            "x": point[0],
            "y": point[1],
            "label": label,
            "captured_at": datetime.now().isoformat(timespec="seconds"),
        }
        save_snapshot(key)
        self.step_index += 1
        self.root.deiconify()
        self.update_label()
        if self.step_index >= len(STEPS):
            self.write_calibration()

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
        messagebox.showinfo("Calibracion lista", f"Guardado en:\n{CALIBRATION_FILE}")

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
