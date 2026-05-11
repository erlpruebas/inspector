from __future__ import annotations

import queue
import sys
import threading
import time
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk

from orchestrator import Orchestrator, RESTART_EXIT_CODE


class OrchestratorGui:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Inspector - Orquestador Telegram")
        self.root.geometry("1120x760")
        self.root.minsize(860, 560)

        self.events: queue.Queue[tuple[str, str]] = queue.Queue()
        self.orchestrator: Orchestrator | None = None
        self.worker: threading.Thread | None = None
        self.running = False
        self.last_log_text = ""

        self.status_var = tk.StringVar(value="Inicializando...")
        self.command_var = tk.StringVar()

        self._build_ui()
        self._start_orchestrator()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(500, self._tick)

    def run(self) -> None:
        self.root.mainloop()

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)
        outer.columnconfigure(0, weight=2)
        outer.columnconfigure(1, weight=3)
        outer.rowconfigure(1, weight=1)

        title = ttk.Label(outer, text="Inspector - Orquestador Telegram", font=("Segoe UI", 15, "bold"))
        title.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        left = ttk.Frame(outer)
        left.grid(row=1, column=0, sticky=tk.NSEW, padx=(0, 8))
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        right = ttk.Frame(outer)
        right.grid(row=1, column=1, sticky=tk.NSEW)
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        controls = ttk.Frame(left)
        controls.grid(row=0, column=0, sticky=tk.EW, pady=(0, 8))
        controls.columnconfigure(2, weight=1)

        self.start_button = ttk.Button(controls, text="Arrancar", command=self._start_orchestrator)
        self.start_button.grid(row=0, column=0, padx=(0, 6))
        ttk.Button(controls, text="Detener tarea", command=self._stop_current_task).grid(row=0, column=1, padx=(0, 6))
        ttk.Button(controls, text="Parar orquestador", command=self._stop_orchestrator).grid(row=0, column=2, sticky=tk.W)

        status_box = ttk.LabelFrame(left, text="Estado")
        status_box.grid(row=1, column=0, sticky=tk.NSEW)
        status_box.rowconfigure(0, weight=1)
        status_box.columnconfigure(0, weight=1)
        self.status_text = scrolledtext.ScrolledText(status_box, wrap=tk.WORD, height=18, font=("Consolas", 10))
        self.status_text.grid(row=0, column=0, sticky=tk.NSEW, padx=6, pady=6)
        self.status_text.configure(state=tk.DISABLED)

        command_box = ttk.LabelFrame(left, text="Inyectar comando")
        command_box.grid(row=2, column=0, sticky=tk.EW, pady=(8, 0))
        command_box.columnconfigure(0, weight=1)
        command_entry = ttk.Entry(command_box, textvariable=self.command_var)
        command_entry.grid(row=0, column=0, sticky=tk.EW, padx=6, pady=6)
        command_entry.bind("<Return>", lambda _event: self._inject_command())
        ttk.Button(command_box, text="Enviar", command=self._inject_command).grid(row=0, column=1, padx=(0, 6), pady=6)

        examples = ttk.Frame(command_box)
        examples.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=6, pady=(0, 6))
        for label, command in (
            ("voz", "/voz"),
            ("voz on", "voz on"),
            ("altavoz on", "altavoz on"),
            ("status", "/status"),
            ("pendientes", "/pendientes"),
        ):
            ttk.Button(examples, text=label, command=lambda value=command: self._set_and_inject(value)).pack(side=tk.LEFT, padx=(0, 5))

        log_header = ttk.Frame(right)
        log_header.grid(row=0, column=0, sticky=tk.EW, pady=(0, 8))
        log_header.columnconfigure(0, weight=1)
        ttk.Label(log_header, textvariable=self.status_var).grid(row=0, column=0, sticky=tk.W)
        ttk.Button(log_header, text="Refrescar", command=self._refresh_all).grid(row=0, column=1)

        log_box = ttk.LabelFrame(right, text="Eventos recientes")
        log_box.grid(row=1, column=0, sticky=tk.NSEW)
        log_box.rowconfigure(0, weight=1)
        log_box.columnconfigure(0, weight=1)
        self.log_text = scrolledtext.ScrolledText(log_box, wrap=tk.WORD, font=("Consolas", 10))
        self.log_text.grid(row=0, column=0, sticky=tk.NSEW, padx=6, pady=6)
        self.log_text.configure(state=tk.DISABLED)

    def _start_orchestrator(self) -> None:
        if self.worker and self.worker.is_alive():
            return
        try:
            self.orchestrator = Orchestrator()
        except Exception as exc:
            messagebox.showerror("No se pudo iniciar", str(exc))
            return
        self.running = True
        self.worker = threading.Thread(target=self._run_worker, daemon=True)
        self.worker.start()
        self.status_var.set("Orquestador arrancado")

    def _run_worker(self) -> None:
        assert self.orchestrator is not None
        try:
            code = self.orchestrator.run()
            if code == RESTART_EXIT_CODE:
                self.events.put(("status", "El orquestador pidio reinicio por hot reload. Pulsa Arrancar."))
            else:
                self.events.put(("status", f"Orquestador detenido con codigo {code}."))
        except Exception:
            self.events.put(("status", "Error en orquestador:\n" + traceback.format_exc()))
        finally:
            self.running = False

    def _stop_current_task(self) -> None:
        if self.orchestrator is None:
            return
        chat_id = self.orchestrator.settings.telegram_allowed_user_id
        self.orchestrator._cancel_current_task(chat_id, "gui")
        self._refresh_all()

    def _stop_orchestrator(self) -> None:
        if self.orchestrator is not None:
            self.orchestrator.stop()
        self.status_var.set("Parando orquestador...")

    def _inject_command(self) -> None:
        command = self.command_var.get().strip()
        if not command or self.orchestrator is None:
            return
        self.command_var.set("")
        threading.Thread(target=self._inject_worker, args=(command,), daemon=True).start()

    def _inject_worker(self, command: str) -> None:
        try:
            assert self.orchestrator is not None
            self.orchestrator.inject_text(command)
            self.events.put(("status", f"Comando inyectado: {command}"))
        except Exception:
            self.events.put(("status", "Error inyectando comando:\n" + traceback.format_exc()))

    def _set_and_inject(self, command: str) -> None:
        self.command_var.set(command)
        self._inject_command()

    def _tick(self) -> None:
        self._drain_events()
        self._refresh_all()
        self.root.after(1000, self._tick)

    def _drain_events(self) -> None:
        while True:
            try:
                kind, text = self.events.get_nowait()
            except queue.Empty:
                return
            if kind == "status":
                self.status_var.set(text.splitlines()[0][:160])
                self._append_log("\n[GUI]\n" + text + "\n")

    def _refresh_all(self) -> None:
        if self.orchestrator is None:
            return
        self._set_text(self.status_text, self.orchestrator._status_text())
        log_text = self._tail_file(self.orchestrator.settings.memory_file, max_chars=24000)
        if log_text != self.last_log_text:
            self.last_log_text = log_text
            self._set_text(self.log_text, log_text, scroll_end=True)
        state = "activo" if self.running else "detenido"
        busy = "ocupado" if self.orchestrator._busy.locked() else "libre"
        self.status_var.set(f"Orquestador {state} | Codex {busy} | {time.strftime('%H:%M:%S')}")

    @staticmethod
    def _tail_file(path: Path, max_chars: int) -> str:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return "(sin eventos todavia)"
        if len(text) <= max_chars:
            return text
        return text[-max_chars:]

    @staticmethod
    def _set_text(widget: scrolledtext.ScrolledText, value: str, scroll_end: bool = False) -> None:
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, value)
        if scroll_end:
            widget.see(tk.END)
        widget.configure(state=tk.DISABLED)

    def _append_log(self, value: str) -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, value)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _on_close(self) -> None:
        if self.orchestrator is not None:
            self.orchestrator.stop()
        self.root.after(300, self.root.destroy)


def main() -> int:
    app = OrchestratorGui()
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
