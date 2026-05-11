from __future__ import annotations

import json
import queue
import subprocess
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import scrolledtext, ttk

from provider_health import main as provider_health_main
from task_loader import load_tasks


ROOT = Path(__file__).resolve().parent
DEFAULT_TASKS = ROOT / "tasks" / "assistant_tasks.json"
ENGINE_MATRIX = ROOT / "engine_matrix.json"


class BenchmarkGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("AI Arena Benchmark")
        self.geometry("1100x760")
        self.events: queue.Queue[str] = queue.Queue()
        self.process: subprocess.Popen[str] | None = None
        self.state_path: Path | None = None
        self._build()
        self._load_defaults()
        self.after(250, self._drain_events)

    def _build(self) -> None:
        top = ttk.Frame(self, padding=8)
        top.pack(fill=tk.X)
        ttk.Label(top, text="Tasks file").grid(row=0, column=0, sticky=tk.W)
        self.tasks_file = tk.StringVar(value=str(DEFAULT_TASKS))
        ttk.Entry(top, textvariable=self.tasks_file, width=80).grid(row=0, column=1, sticky=tk.EW, padx=6)
        ttk.Button(top, text="Reload", command=self._load_tasks).grid(row=0, column=2)
        ttk.Button(top, text="Health", command=self._health).grid(row=0, column=3, padx=4)
        top.columnconfigure(1, weight=1)

        body = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        left = ttk.Frame(body, padding=4)
        middle = ttk.Frame(body, padding=4)
        right = ttk.Frame(body, padding=4)
        body.add(left, weight=1)
        body.add(middle, weight=1)
        body.add(right, weight=2)

        ttk.Label(left, text="Engines / models").pack(anchor=tk.W)
        self.engine_list = tk.Listbox(left, selectmode=tk.EXTENDED, exportselection=False)
        self.engine_list.pack(fill=tk.BOTH, expand=True)

        ttk.Label(middle, text="Tasks").pack(anchor=tk.W)
        filter_row = ttk.Frame(middle)
        filter_row.pack(fill=tk.X)
        self.level_var = tk.StringVar(value="")
        ttk.Label(filter_row, text="Level").pack(side=tk.LEFT)
        ttk.Entry(filter_row, textvariable=self.level_var, width=8).pack(side=tk.LEFT, padx=4)
        ttk.Button(filter_row, text="Filter", command=self._load_tasks).pack(side=tk.LEFT)
        self.task_list = tk.Listbox(middle, selectmode=tk.EXTENDED, exportselection=False)
        self.task_list.pack(fill=tk.BOTH, expand=True)

        controls = ttk.Frame(right)
        controls.pack(fill=tk.X)
        self.cooldown = tk.IntVar(value=7200)
        self.rest = tk.IntVar(value=0)
        self.once = tk.BooleanVar(value=True)
        ttk.Label(controls, text="Cooldown s").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(controls, textvariable=self.cooldown, width=8).grid(row=0, column=1, sticky=tk.W)
        ttk.Label(controls, text="Rest s").grid(row=0, column=2, sticky=tk.W, padx=(12, 0))
        ttk.Entry(controls, textvariable=self.rest, width=8).grid(row=0, column=3, sticky=tk.W)
        ttk.Checkbutton(controls, text="Once", variable=self.once).grid(row=0, column=4, sticky=tk.W, padx=8)
        ttk.Button(controls, text="Run Scheduler", command=self._run_scheduler).grid(row=1, column=0, pady=6, sticky=tk.W)
        ttk.Button(controls, text="Stop", command=self._stop).grid(row=1, column=1, pady=6, sticky=tk.W)
        ttk.Button(controls, text="Refresh State", command=self._refresh_state).grid(row=1, column=2, pady=6, sticky=tk.W)

        status = ttk.LabelFrame(right, text="Scheduler state", padding=6)
        status.pack(fill=tk.X, pady=(2, 6))
        self.state_file = tk.StringVar(value="")
        self.state_counts = tk.StringVar(value="No scheduler state loaded.")
        ttk.Label(status, textvariable=self.state_file).pack(anchor=tk.W)
        ttk.Label(status, textvariable=self.state_counts).pack(anchor=tk.W)
        self.state_list = tk.Listbox(status, height=6, exportselection=False)
        self.state_list.pack(fill=tk.X, expand=False)

        self.log = scrolledtext.ScrolledText(right, height=30)
        self.log.pack(fill=tk.BOTH, expand=True)

    def _load_defaults(self) -> None:
        self.engine_list.delete(0, tk.END)
        matrix = json.loads(ENGINE_MATRIX.read_text(encoding="utf-8"))
        for group in matrix:
            for engine in group.get("engines", []):
                self.engine_list.insert(tk.END, engine)
        self._load_tasks()

    def _load_tasks(self) -> None:
        self.task_list.delete(0, tk.END)
        level = self.level_var.get().strip().upper()
        if level and not level.startswith("L"):
            level = "L" + level
        for task in load_tasks(Path(self.tasks_file.get())):
            if level and task.level.upper() != level:
                continue
            self.task_list.insert(tk.END, f"{task.id} | {task.level} | {task.prompt.splitlines()[0][:70]}")

    def _selected_engines(self) -> list[str]:
        return [self.engine_list.get(index) for index in self.engine_list.curselection()]

    def _selected_tasks(self) -> list[str]:
        values = []
        for index in self.task_list.curselection():
            values.append(self.task_list.get(index).split("|", 1)[0].strip())
        return values

    def _run_scheduler(self) -> None:
        if self.process and self.process.poll() is None:
            self._append("Scheduler already running.\n")
            return
        engines = self._selected_engines()
        tasks = self._selected_tasks()
        if not engines:
            self._append("Select at least one engine.\n")
            return
        state_name = "gui_scheduler_state_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".json"
        self.state_path = ROOT / "results" / state_name
        self.state_file.set(str(self.state_path))
        cmd = [
            sys.executable,
            str(ROOT / "benchmark_scheduler.py"),
            "--tasks-file",
            self.tasks_file.get(),
            "--cooldown-seconds",
            str(self.cooldown.get()),
            "--rest-seconds",
            str(self.rest.get()),
            "--state",
            str(self.state_path),
        ]
        if self.once.get():
            cmd.append("--once")
        for engine in engines:
            cmd.extend(["--engine", engine])
        for task in tasks:
            cmd.extend(["--task", task])
        self._append("> " + " ".join(cmd) + "\n")
        threading.Thread(target=self._run_process, args=(cmd,), daemon=True).start()

    def _run_process(self, cmd: list[str]) -> None:
        self.process = subprocess.Popen(cmd, text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert self.process.stdout is not None
        for line in self.process.stdout:
            self.events.put(line)
        self.events.put(f"\n[exit {self.process.wait()}]\n")

    def _health(self) -> None:
        threading.Thread(target=self._health_worker, daemon=True).start()

    def _health_worker(self) -> None:
        cmd = [sys.executable, str(ROOT / "provider_health.py"), "--live"]
        self._run_process(cmd)

    def _stop(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self._append("Stopping...\n")

    def _refresh_state(self) -> None:
        if not self.state_path or not self.state_path.exists():
            self.state_counts.set("No scheduler state available yet.")
            return
        try:
            state = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            self.state_counts.set(f"Could not read state: {type(exc).__name__}")
            return
        jobs = state.get("jobs", [])
        completed = state.get("completed", [])
        deferred = state.get("deferred", [])
        failed = state.get("failed", [])
        pending = [job for job in jobs if not job.get("done")]
        running = state.get("running") or {}
        running_label = running.get("job", "none") if isinstance(running, dict) else "none"
        self.state_counts.set(
            f"running={running_label} | jobs={len(jobs)} completed={len(completed)} deferred={len(deferred)} failed={len(failed)} pending={len(pending)}"
        )
        self.state_list.delete(0, tk.END)
        recent = list(reversed(deferred[-3:] + failed[-3:] + completed[-3:]))
        for item in recent:
            label = item.get("job", "")
            reason = item.get("reason") or item.get("returncode") or item.get("at", "")
            self.state_list.insert(tk.END, f"{label} | {reason}")

    def _drain_events(self) -> None:
        while True:
            try:
                self._append(self.events.get_nowait())
            except queue.Empty:
                break
        if self.state_path and self.state_path.exists():
            self._refresh_state()
        self.after(250, self._drain_events)

    def _append(self, text: str) -> None:
        self.log.insert(tk.END, text)
        self.log.see(tk.END)


if __name__ == "__main__":
    BenchmarkGui().mainloop()
