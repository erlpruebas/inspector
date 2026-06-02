from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from tkinter import Button, Frame, Label, Tk

from orchestrator_v2.desktop_calibration_store import (
    DEFAULT_CLICK_PROFILE_FILE,
    machine_click_profile_file,
    machine_name,
)

CLICK_PROFILE_FILE = machine_click_profile_file()


DEFAULT_PROFILE = {
    "new_chat": {"x": 71, "y": 47, "label": "Nueva conversacion"},
    "initial_input": {"x": 782, "y": 491, "label": "Input conversacion nueva"},
    "initial_send": {"x": 1100, "y": 516, "label": "Enviar conversacion nueva"},
    "initial_stop_no_browser": {"x": 1373, "y": 988, "label": "Stop sin navegador"},
    "browser_toggle": {"x": 1900, "y": 50, "label": "Abrir/cerrar navegador"},
    "browser_input": {"x": 532, "y": 955, "label": "Input con navegador"},
    "browser_send_stop": {"x": 770, "y": 989, "label": "Enviar/stop con navegador"},
}


@dataclass(frozen=True)
class ClickTarget:
    key: str
    label: str
    x: int
    y: int


class CodexClickConsole:
    def __init__(self, profile: dict) -> None:
        self.profile = profile
        self.root = Tk()
        self.root.title("Codex clicks")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)
        self.last_label = Label(self.root, text="listo", font=("Segoe UI", 8), anchor="w")
        self.build()
        self.position_bottom_left()

    def build(self) -> None:
        frame = Frame(self.root, padx=8, pady=8)
        frame.pack(fill="both", expand=True)
        Label(frame, text="Codex Desktop", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        for target in targets_from_profile(self.profile):
            text = f"{target.label}\n{target.x},{target.y}"
            button = Button(frame, text=text, width=28, command=lambda item=target: self.click(item))
            button.pack(fill="x", pady=2)
        self.last_label.pack(fill="x", padx=8, pady=(0, 8))

    def position_bottom_left(self) -> None:
        self.root.update_idletasks()
        width = 235
        height = 345
        screen_h = self.root.winfo_screenheight()
        self.root.geometry(f"{width}x{height}+12+{max(12, screen_h - height - 56)}")

    def click(self, target: ClickTarget) -> None:
        import pyautogui

        pyautogui.click(target.x, target.y)
        self.last_label.config(text=f"{target.key}: {target.x},{target.y}")

    def run(self) -> None:
        self.root.mainloop()


def targets_from_profile(profile: dict) -> list[ClickTarget]:
    order = [
        "new_chat",
        "initial_input",
        "initial_send",
        "initial_stop_no_browser",
        "browser_toggle",
        "browser_input",
        "browser_send_stop",
    ]
    targets: list[ClickTarget] = []
    for key in order:
        raw = profile.get(key, {})
        targets.append(
            ClickTarget(
                key=key,
                label=str(raw.get("label", key)),
                x=int(raw.get("x", 0)),
                y=int(raw.get("y", 0)),
            )
        )
    return targets


def load_profile() -> dict:
    for path in (CLICK_PROFILE_FILE, DEFAULT_CLICK_PROFILE_FILE):
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict):
            return {**DEFAULT_PROFILE, **data}
    return DEFAULT_PROFILE


def write_default_profile() -> None:
    CLICK_PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not CLICK_PROFILE_FILE.exists():
        CLICK_PROFILE_FILE.write_text(json.dumps(DEFAULT_PROFILE, indent=2, ensure_ascii=False), encoding="utf-8")
    DEFAULT_CLICK_PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DEFAULT_CLICK_PROFILE_FILE.exists():
        DEFAULT_CLICK_PROFILE_FILE.write_text(json.dumps(DEFAULT_PROFILE, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Consola de clicks fijos para Codex Desktop.")
    parser.add_argument("--write-default", action="store_true")
    args = parser.parse_args()
    write_default_profile()
    if args.write_default:
        print(CLICK_PROFILE_FILE)
        return 0
    print(f"Usando perfil de clicks para: {machine_name()}")
    CodexClickConsole(load_profile()).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
