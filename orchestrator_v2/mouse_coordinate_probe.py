from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from tkinter import Button, Entry, Frame, Label, Listbox, StringVar, Tk


RUNTIME_ROOT = Path("orchestrator_v2/runtime/desktop_codex_operator")
CAPTURE_FILE = RUNTIME_ROOT / "mouse_coordinate_captures.jsonl"


class MouseCoordinateProbe:
    def __init__(self) -> None:
        self.root = Tk()
        self.root.title("XY")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)
        self.capture_on = False
        self.current_xy = StringVar(value="X: -  Y: -")
        self.status = StringVar(value="captura apagada")
        self.label_var = StringVar(value="")
        self.last_point: tuple[int, int] | None = None

        frame = Frame(self.root, padx=8, pady=8)
        frame.pack(fill="both", expand=True)
        Label(frame, textvariable=self.current_xy, font=("Consolas", 13, "bold")).pack(anchor="w")
        Label(frame, textvariable=self.status, font=("Segoe UI", 8)).pack(anchor="w", pady=(0, 5))
        self.entry = Entry(frame, textvariable=self.label_var, width=28)
        self.entry.pack(fill="x", pady=(0, 5))
        self.entry.insert(0, "nota opcional")
        row = Frame(frame)
        row.pack(fill="x")
        self.capture_button = Button(row, text="Capturar OFF", width=14, bg="#2255aa", fg="white", command=self.toggle_capture)
        self.capture_button.pack(side="left")
        Button(row, text="Guardar punto", width=13, command=self.save_current).pack(side="left", padx=(6, 0))
        self.listbox = Listbox(frame, width=34, height=7, font=("Consolas", 8))
        self.listbox.pack(fill="both", pady=(7, 0))
        self.position_bottom_left()
        self.root.after(80, self.tick)

    def position_bottom_left(self) -> None:
        self.root.update_idletasks()
        width = 270
        height = 245
        screen_h = self.root.winfo_screenheight()
        x = 12
        y = max(12, screen_h - height - 56)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def toggle_capture(self) -> None:
        self.capture_on = not self.capture_on
        if self.capture_on:
            self.capture_button.configure(text="Capturar ON", bg="#c82030")
            self.status.set("clicks manuales: pulsa Guardar punto")
        else:
            self.capture_button.configure(text="Capturar OFF", bg="#2255aa")
            self.status.set("captura apagada")

    def tick(self) -> None:
        point = mouse_position()
        self.last_point = point
        self.current_xy.set(f"X: {point[0]:4d}  Y: {point[1]:4d}")
        self.root.after(80, self.tick)

    def save_current(self) -> None:
        if self.last_point is None:
            return
        label = self.label_var.get().strip()
        if label == "nota opcional":
            label = ""
        record = {
            "timestamp": datetime.now().isoformat(timespec="milliseconds"),
            "x": self.last_point[0],
            "y": self.last_point[1],
            "label": label,
            "capture_on": self.capture_on,
        }
        append_record(record)
        visible = f"{record['x']:4d},{record['y']:4d} {label[:18]}"
        self.listbox.insert(0, visible)
        self.status.set(f"guardado: {record['x']},{record['y']}")

    def run(self) -> None:
        self.root.mainloop()


def mouse_position() -> tuple[int, int]:
    import pyautogui

    pos = pyautogui.position()
    return int(pos.x), int(pos.y)


def append_record(record: dict) -> None:
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    with CAPTURE_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Muestra y guarda coordenadas XY del raton.")
    parser.add_argument("--show-file", action="store_true")
    args = parser.parse_args()
    if args.show_file:
        print(CAPTURE_FILE)
        return 0
    MouseCoordinateProbe().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
