from __future__ import annotations

import argparse
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any
from tkinter import Button, Frame, Label, Tk, messagebox, StringVar
from tkinter import ttk

from orchestrator_v2.desktop_calibration_store import machine_calibration_file, machine_name, tracked_machine_calibration_file


CALIBRATION_FILE = machine_calibration_file()
TRACKED_CALIBRATION_FILE = tracked_machine_calibration_file()


APPLICATIONS: dict[str, dict[str, Any]] = {
    "codex_desktop": {
        "display_name": "Codex Desktop",
        "window_title_hint": "Codex",
        "steps": [
            ("new_chat", "Haz clic en Nuevo chat"),
            ("initial_input", "Haz clic en la caja de texto inicial"),
            ("initial_send", "Haz clic en Enviar inicial"),
            ("browser_toggle", "Haz clic en Abrir pantalla lateral del navegador"),
            ("browser_input", "Haz clic en la caja de texto con el navegador abierto"),
            ("browser_send_stop", "Haz clic en Enviar con el navegador abierto"),
        ],
    }
}


class DesktopAppCalibrator:
    def __init__(self) -> None:
        self.root = Tk()
        self.root.title("Calibrador de Codex Desktop")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.machine_label = StringVar(value=f"Equipo: {machine_name()}")
        self.app_var = StringVar(value=self.default_app_name())
        self.step_label = StringVar(value="")
        self.status_label = StringVar(value="Selecciona la app y empieza la calibracion.")
        self.progress_label = StringVar(value="")

        self.store: dict[str, Any] = load_store()
        self.current_app_id = self.app_var_to_id(self.app_var.get())
        self.current_step_index = 0
        self.armed = False
        self.listener = None
        self.capture_lock = threading.Lock()
        self.pending_step_key = ""

        self._build_ui()
        self._position_bottom_left()
        self._refresh_app_state()

    def default_app_name(self) -> str:
        first_app = next(iter(APPLICATIONS.values()))
        return first_app["display_name"]

    def app_id_to_name(self, app_id: str) -> str:
        app = APPLICATIONS.get(app_id)
        return str(app["display_name"]) if app else app_id

    def app_var_to_id(self, display_name: str) -> str:
        for app_id, app in APPLICATIONS.items():
            if app["display_name"] == display_name:
                return app_id
        return next(iter(APPLICATIONS))

    def _build_ui(self) -> None:
        frame = Frame(self.root, padx=8, pady=8)
        frame.pack(fill="both", expand=True)

        Label(frame, textvariable=self.machine_label, font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x")
        Label(frame, text="App a configurar", font=("Segoe UI", 8), anchor="w").pack(fill="x", pady=(4, 0))

        app_names = [app["display_name"] for app in APPLICATIONS.values()]
        self.app_combo = ttk.Combobox(frame, values=app_names, textvariable=self.app_var, state="readonly", width=28)
        self.app_combo.pack(fill="x", pady=(0, 6))
        self.app_combo.bind("<<ComboboxSelected>>", self.on_app_change)

        Label(frame, textvariable=self.step_label, font=("Segoe UI", 11, "bold"), wraplength=300, justify="left").pack(fill="x", pady=(2, 4))
        Label(frame, textvariable=self.progress_label, font=("Consolas", 8), justify="left", anchor="w").pack(fill="x")
        Label(frame, textvariable=self.status_label, font=("Segoe UI", 8), wraplength=300, justify="left", anchor="w").pack(fill="x", pady=(4, 4))

        row = Frame(frame)
        row.pack(fill="x", pady=(2, 0))
        self.ready_button = Button(row, text="Listo", width=10, command=self.arm_next_capture)
        self.ready_button.pack(side="left")
        Button(row, text="Reiniciar", width=10, command=self.reset_current_app).pack(side="left", padx=(6, 0))
        Button(row, text="Guardar", width=10, command=self.save_store).pack(side="left", padx=(6, 0))

    def _position_bottom_left(self) -> None:
        self.root.update_idletasks()
        width = 345
        height = 255
        screen_h = self.root.winfo_screenheight()
        x = 12
        y = max(12, screen_h - height - 56)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def on_app_change(self, _event: object | None = None) -> None:
        self.current_app_id = self.app_var_to_id(self.app_var.get())
        self.current_step_index = 0
        self._refresh_app_state()

    def _refresh_app_state(self) -> None:
        app = APPLICATIONS[self.current_app_id]
        app_store = self.store.get("applications", {}).get(self.current_app_id, {})
        points = app_store.get("points", {}) if isinstance(app_store, dict) else {}
        steps = app["steps"]
        self.current_step_index = self._next_step_index(points)
        total = len(steps)
        if self.current_step_index >= total:
            self.pending_step_key = ""
            self.step_label.set(f"{app['display_name']}: calibracion completada")
            self.status_label.set("Todos los pasos estan guardados para esta app.")
        else:
            key, prompt = steps[self.current_step_index]
            self.pending_step_key = key
            self.step_label.set(f"Paso {self.current_step_index + 1}/{total}: {prompt}")
            self.status_label.set("Pulsa Listo y despues haz el siguiente clic en la app.")
        self._refresh_progress(points)

    def _next_step_index(self, points: dict[str, Any]) -> int:
        steps = APPLICATIONS[self.current_app_id]["steps"]
        for index, (key, _prompt) in enumerate(steps):
            point = points.get(key, {})
            try:
                int(point["x"])
                int(point["y"])
            except (KeyError, TypeError, ValueError):
                return index
        return len(steps)

    def _captured_points_for_app(self, points: dict[str, Any]) -> list[str]:
        app = APPLICATIONS[self.current_app_id]
        ordered = []
        for key, _prompt in app["steps"]:
            point = points.get(key, {})
            try:
                x = int(point["x"])
                y = int(point["y"])
            except (KeyError, TypeError, ValueError):
                continue
            ordered.append(f"{key}: {x},{y}")
        return ordered

    def _refresh_progress(self, points: dict[str, Any] | None = None) -> None:
        if points is None:
            points = self.store.get("applications", {}).get(self.current_app_id, {}).get("points", {})
        if not points:
            self.progress_label.set("Sin puntos guardados aun.")
            return
        lines = []
        for key, _prompt in APPLICATIONS[self.current_app_id]["steps"]:
            point = points.get(key, {})
            try:
                x = int(point["x"])
                y = int(point["y"])
            except (KeyError, TypeError, ValueError):
                continue
            lines.append(f"{key:<18} {x:4d},{y:4d}")
        self.progress_label.set("\n".join(lines[:6]))

    def reset_current_app(self) -> None:
        applications = self.store.setdefault("applications", {})
        applications[self.current_app_id] = {
            "display_name": APPLICATIONS[self.current_app_id]["display_name"],
            "window_title_hint": APPLICATIONS[self.current_app_id]["window_title_hint"],
            "steps": [key for key, _ in APPLICATIONS[self.current_app_id]["steps"]],
            "points": {},
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        self.store["points"] = {}
        self.current_step_index = 0
        self.pending_step_key = ""
        self.status_label.set("Progreso reiniciado para esta app.")
        self._refresh_app_state()
        self.save_store()

    def arm_next_capture(self) -> None:
        if self.armed:
            return
        if self.current_step_index >= len(APPLICATIONS[self.current_app_id]["steps"]):
            self.status_label.set("Esta app ya esta completa. Usa Reiniciar si quieres recalibrarla.")
            return
        self.armed = True
        self.ready_button.config(state="disabled")
        self.status_label.set("Ahora haz el siguiente clic que quieres guardar.")
        self.root.withdraw()
        self._start_listener()

    def _start_listener(self) -> None:
        try:
            from pynput import mouse
        except ImportError as exc:
            self.armed = False
            self.root.deiconify()
            self.ready_button.config(state="normal")
            messagebox.showerror(
                "Falta dependencia",
                "No se encontro pynput.\nInstala las dependencias de requirements.txt para capturar el siguiente clic.",
                parent=self.root,
            )
            self.status_label.set("Falta pynput para capturar clics.")
            return

        def on_click(x: int, y: int, button: Any, pressed: bool) -> bool | None:
            if not self.armed or not pressed or button != mouse.Button.left:
                return None
            with self.capture_lock:
                if not self.armed:
                    return False
                self.armed = False
            self.root.after(0, lambda: self._handle_capture(int(x), int(y)))
            return False

        self.listener = mouse.Listener(on_click=on_click)
        self.listener.start()

    def _handle_capture(self, x: int, y: int) -> None:
        app = APPLICATIONS[self.current_app_id]
        step_key, step_prompt = app["steps"][self.current_step_index]
        applications = self.store.setdefault("applications", {})
        app_store = applications.setdefault(
            self.current_app_id,
            {
                "display_name": app["display_name"],
                "window_title_hint": app["window_title_hint"],
                "steps": [key for key, _ in app["steps"]],
                "points": {},
            },
        )
        points = app_store.setdefault("points", {})
        points[step_key] = {
            "x": x,
            "y": y,
            "label": step_prompt,
            "captured_at": datetime.now().isoformat(timespec="seconds"),
            "machine_name": machine_name(),
        }
        app_store["updated_at"] = datetime.now().isoformat(timespec="seconds")
        self.store["version"] = 2
        self.store["machine_name"] = machine_name()
        self.store["selected_application"] = self.current_app_id
        self.store["updated_at"] = datetime.now().isoformat(timespec="seconds")
        self.store["points"] = dict(points)
        self.current_step_index += 1
        self._refresh_app_state()
        self.save_store()
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.ready_button.config(state="normal")
        self.status_label.set(f"Guardado {step_key}: {x},{y}")
        if self.current_step_index >= len(app["steps"]):
            messagebox.showinfo("Calibracion completa", f"Ya quedaron guardadas todas las coordenadas de {app['display_name']}.", parent=self.root)

    def save_store(self) -> None:
        self.store.setdefault("version", 2)
        self.store["machine_name"] = machine_name()
        self.store["updated_at"] = datetime.now().isoformat(timespec="seconds")
        CALIBRATION_FILE.parent.mkdir(parents=True, exist_ok=True)
        CALIBRATION_FILE.write_text(json.dumps(self.store, indent=2, ensure_ascii=False), encoding="utf-8")
        TRACKED_CALIBRATION_FILE.parent.mkdir(parents=True, exist_ok=True)
        TRACKED_CALIBRATION_FILE.write_text(json.dumps(self.store, indent=2, ensure_ascii=False), encoding="utf-8")

    def close(self) -> None:
        self.armed = False
        try:
            if self.listener is not None:
                self.listener.stop()
        except Exception:
            pass
        self.save_store()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def load_store() -> dict[str, Any]:
    source_file = CALIBRATION_FILE if CALIBRATION_FILE.exists() else TRACKED_CALIBRATION_FILE
    if not source_file.exists():
        return {"version": 2, "machine_name": machine_name(), "applications": {}}
    try:
        data = json.loads(source_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 2, "machine_name": machine_name(), "applications": {}}
    if not isinstance(data, dict):
        return {"version": 2, "machine_name": machine_name(), "applications": {}}
    if "applications" not in data or not isinstance(data["applications"], dict):
        data["applications"] = {}
    if "points" in data and "codex_desktop" not in data["applications"] and isinstance(data["points"], dict):
        data["applications"]["codex_desktop"] = {
            "display_name": APPLICATIONS["codex_desktop"]["display_name"],
            "window_title_hint": APPLICATIONS["codex_desktop"]["window_title_hint"],
            "steps": [key for key, _ in APPLICATIONS["codex_desktop"]["steps"]],
            "points": data["points"],
            "updated_at": data.get("updated_at", datetime.now().isoformat(timespec="seconds")),
        }
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Calibrador guiado de Codex Desktop por equipo.")
    parser.add_argument("--show-file", action="store_true", help="Imprime el archivo de calibracion actual.")
    args = parser.parse_args()
    if args.show_file:
        print(CALIBRATION_FILE)
        return 0
    DesktopAppCalibrator().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
