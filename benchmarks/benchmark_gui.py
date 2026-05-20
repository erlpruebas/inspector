from __future__ import annotations

import json
import queue
import re
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
ENGINE_MATRIX = ROOT / "engine_matrix_cloud.json"


class BenchmarkGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("AI Arena Benchmark")
        self.geometry("1100x760")
        self.events: queue.Queue[str] = queue.Queue()
        self.process: subprocess.Popen[str] | None = None
        self.state_path: Path | None = None
        self.tasks = []
        self.engines: list[str] = []
        self.cell_vars: dict[tuple[str, str], tk.BooleanVar] = {}
        self.cell_widgets: dict[tuple[str, str], ttk.Checkbutton] = {}
        self.task_titles: dict[str, str] = {}
        self.engine_codes: dict[str, str] = {}
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

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        matrix_tab = ttk.Frame(self.notebook, padding=4)
        legacy_tab = ttk.Frame(self.notebook, padding=4)
        self.notebook.add(matrix_tab, text="Matrix")
        self.notebook.add(legacy_tab, text="Lists")

        matrix_toolbar = ttk.Frame(matrix_tab)
        matrix_toolbar.pack(fill=tk.X, pady=(0, 4))
        ttk.Button(matrix_toolbar, text="All", command=self._select_all_cells).pack(side=tk.LEFT)
        ttk.Button(matrix_toolbar, text="None", command=self._clear_all_cells).pack(side=tk.LEFT, padx=4)
        ttk.Button(matrix_toolbar, text="Missing", command=self._select_missing_cells).pack(side=tk.LEFT)
        ttk.Button(matrix_toolbar, text="Run Checked", command=self._run_checked_matrix).pack(side=tk.LEFT, padx=12)
        ttk.Button(matrix_toolbar, text="Refresh Results", command=self._refresh_matrix).pack(side=tk.LEFT)
        ttk.Button(matrix_toolbar, text="Grade Run", command=self._grade_run).pack(side=tk.LEFT, padx=4)
        ttk.Button(matrix_toolbar, text="Show Grades", command=self._show_grades).pack(side=tk.LEFT)
        self.matrix_hint = tk.StringVar(value="Tick cells to choose the next round.")
        ttk.Label(matrix_toolbar, textvariable=self.matrix_hint).pack(side=tk.LEFT, padx=12)

        self.legend_var = tk.StringVar(value="")
        ttk.Label(matrix_tab, textvariable=self.legend_var, wraplength=1400, justify=tk.LEFT).pack(fill=tk.X, pady=(0, 4))

        self.matrix_canvas = tk.Canvas(matrix_tab, highlightthickness=0)
        matrix_y = ttk.Scrollbar(matrix_tab, orient=tk.VERTICAL, command=self.matrix_canvas.yview)
        matrix_x = ttk.Scrollbar(matrix_tab, orient=tk.HORIZONTAL, command=self.matrix_canvas.xview)
        self.matrix_frame = ttk.Frame(self.matrix_canvas)
        self.matrix_frame.bind(
            "<Configure>",
            lambda _event: self.matrix_canvas.configure(scrollregion=self.matrix_canvas.bbox("all")),
        )
        self.matrix_canvas.create_window((0, 0), window=self.matrix_frame, anchor="nw")
        self.matrix_canvas.configure(yscrollcommand=matrix_y.set, xscrollcommand=matrix_x.set)
        self.matrix_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        matrix_y.pack(side=tk.RIGHT, fill=tk.Y)
        matrix_x.pack(side=tk.BOTTOM, fill=tk.X)

        body = ttk.PanedWindow(legacy_tab, orient=tk.HORIZONTAL)
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
        ttk.Button(controls, text="Grade Run", command=self._grade_run).grid(row=1, column=3, pady=6, sticky=tk.W)
        ttk.Button(controls, text="Show Grades", command=self._show_grades).grid(row=1, column=4, pady=6, sticky=tk.W)

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
        self.engines = []
        for group in matrix:
            for engine in group.get("engines", []):
                self.engines.append(engine)
                self.engine_list.insert(tk.END, engine)
        self.engine_codes = {engine: self._engine_code(engine, index) for index, engine in enumerate(self.engines, start=1)}
        self.legend_var.set(" | ".join(f"{code}={engine}" for engine, code in self.engine_codes.items()))
        self._load_tasks()
        self._build_matrix()

    def _load_tasks(self) -> None:
        self.task_list.delete(0, tk.END)
        level = self.level_var.get().strip().upper()
        if level and not level.startswith("L"):
            level = "L" + level
        self.tasks = []
        self.task_titles = {}
        for task in load_tasks(Path(self.tasks_file.get())):
            if level and task.level.upper() != level:
                continue
            self.tasks.append(task)
            self.task_titles[task.id] = task.prompt.splitlines()[0].lstrip("# ").strip()
            self.task_list.insert(tk.END, f"{task.id} | {task.level} | {task.prompt.splitlines()[0][:70]}")
        if hasattr(self, "matrix_frame"):
            self._build_matrix()

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

    def _run_checked_matrix(self) -> None:
        if self.process and self.process.poll() is None:
            self._append("Scheduler already running.\n")
            return
        jobs = [
            f"{engine}::{task_id}"
            for (task_id, engine), var in self.cell_vars.items()
            if var.get()
        ]
        if not jobs:
            self._append("Tick at least one matrix cell.\n")
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
        for job in jobs:
            cmd.extend(["--job", job])
        self._append("> " + " ".join(cmd) + "\n")
        threading.Thread(target=self._run_process, args=(cmd,), daemon=True).start()

    def _build_matrix(self) -> None:
        for child in self.matrix_frame.winfo_children():
            child.destroy()
        self.cell_vars.clear()
        self.cell_widgets.clear()

        ttk.Label(self.matrix_frame, text="Task", width=26).grid(row=0, column=0, sticky=tk.NSEW, padx=1, pady=1)
        for col, engine in enumerate(self.engines, start=1):
            ttk.Label(self.matrix_frame, text=self.engine_codes.get(engine, self._short_engine(engine)), width=8).grid(
                row=0, column=col, sticky=tk.NSEW, padx=1, pady=1
            )

        statuses = self._latest_statuses()
        for row, task in enumerate(self.tasks, start=1):
            title = f"{task.id} {task.level} {self.task_titles.get(task.id, '')[:42]}"
            ttk.Label(self.matrix_frame, text=title, width=42).grid(row=row, column=0, sticky=tk.W, padx=1, pady=1)
            for col, engine in enumerate(self.engines, start=1):
                key = (task.id, engine)
                var = tk.BooleanVar(value=False)
                status = statuses.get((task.id, self._engine_name(engine)), {"status": "pending"})
                widget = ttk.Checkbutton(
                    self.matrix_frame,
                    text=self._status_label(status),
                    variable=var,
                    width=8,
                )
                widget.grid(row=row, column=col, sticky=tk.NSEW, padx=1, pady=1)
                self.cell_vars[key] = var
                self.cell_widgets[key] = widget
        self.matrix_hint.set(f"{len(self.tasks)} tasks x {len(self.engines)} cloud engines")

    def _refresh_matrix(self) -> None:
        statuses = self._latest_statuses()
        for (task_id, engine), widget in self.cell_widgets.items():
            status = statuses.get((task_id, self._engine_name(engine)), {"status": "pending"})
            widget.configure(text=self._status_label(status))

    def _select_all_cells(self) -> None:
        for var in self.cell_vars.values():
            var.set(True)

    def _clear_all_cells(self) -> None:
        for var in self.cell_vars.values():
            var.set(False)

    def _select_missing_cells(self) -> None:
        statuses = self._latest_statuses()
        for (task_id, engine), var in self.cell_vars.items():
            status = statuses.get((task_id, self._engine_name(engine)), {"status": "pending"})
            var.set(status.get("status") in {"pending", "fail", "invalid"})

    def _latest_statuses(self) -> dict[tuple[str, str], dict[str, object]]:
        statuses: dict[tuple[str, str], dict[str, object]] = {}
        result_dirs = sorted((ROOT / "results").glob("20*"), key=lambda path: path.stat().st_mtime)
        for run_dir in result_dirs:
            checks = self._load_expected_checks(run_dir)
            grades = self._load_grades(run_dir)
            for summary_file in run_dir.glob("*.json"):
                if summary_file.name in {"summary.json", "scheduler_state.json", "expected_key_checks.json", "provider_health.json", "grades.json"}:
                    continue
                try:
                    raw = json.loads(summary_file.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                if not isinstance(raw, dict):
                    continue
                task_id = raw.get("task_id")
                engine = raw.get("engine")
                if not task_id or not engine:
                    continue
                if raw.get("returncode") != 0 or raw.get("timed_out"):
                    statuses[(str(task_id), str(engine))] = {"status": "fail"}
                elif (str(task_id), str(engine)) in grades:
                    statuses[(str(task_id), str(engine))] = grades[(str(task_id), str(engine))]
                elif (str(task_id), str(engine)) in checks:
                    statuses[(str(task_id), str(engine))] = {"status": "valid" if checks[(str(task_id), str(engine))] else "invalid"}
                else:
                    statuses[(str(task_id), str(engine))] = {"status": "done"}
        return statuses

    def _load_expected_checks(self, run_dir: Path) -> dict[tuple[str, str], bool]:
        path = run_dir / "expected_key_checks.json"
        if not path.exists():
            return {}
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        checks = {}
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict) and item.get("task_id") and item.get("engine"):
                    checks[(str(item["task_id"]), str(item["engine"]))] = bool(item.get("passed"))
        return checks

    def _load_grades(self, run_dir: Path) -> dict[tuple[str, str], dict[str, object]]:
        path = run_dir / "grades.json"
        if not path.exists():
            return {}
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        grades: dict[tuple[str, str], dict[str, object]] = {}
        if isinstance(raw, list):
            for item in raw:
                if not isinstance(item, dict) or not item.get("task_id") or not item.get("engine"):
                    continue
                try:
                    score = float(item.get("score", item.get("heuristic_score", 0)))
                except (TypeError, ValueError):
                    score = 0.0
                grades[(str(item["task_id"]), str(item["engine"]))] = {
                    "status": "valid" if bool(item.get("passed_expected_keys")) else "invalid",
                    "score": score,
                    "comment": str(item.get("comment", "")),
                }
        return grades

    def _short_engine(self, engine: str) -> str:
        return (
            engine.replace("openrouter:", "or:")
            .replace("opencode:", "oc:")
            .replace("gemini:", "gm:")
            .replace("vikingnano:", "mini nano:")
        )

    def _engine_code(self, engine: str, index: int) -> str:
        codes = {
            "codex:gpt-5.5": "C55",
            "codex:gpt-5.4-mini": "C54M",
            "gemini:gemini-2.5-pro": "G25P",
            "gemini:gemini-2.5-flash": "G25F",
            "gemini:gemini-2.5-flash-lite": "G25L",
            "openrouter:deepseek/deepseek-v4-flash": "ORV4F",
            "openrouter:deepseek/deepseek-v3.2": "ORV32",
            "openrouter:deepseek/deepseek-v3.2-speciale": "ORV32S",
            "groq:llama-3.1-8b-instant": "GRL8",
            "groq:openai/gpt-oss-20b": "GRO20",
            "vikingnano:gemini-nano-local": "MINI",
            "opencode:openrouter/deepseek/deepseek-v4-flash": "OCV4F",
            "opencode:openrouter/deepseek/deepseek-v3.2": "OCOR",
            "opencode:openrouter/deepseek/deepseek-v3.2-speciale": "OCV32S",
            "opencode:groq/llama-3.1-8b-instant": "OCGR8",
            "opencode:groq/openai/gpt-oss-20b": "OCGO20",
            "opencode:google/gemini-2.5-flash": "OCG25F",
        }
        return codes.get(engine, f"M{index:02d}")

    def _engine_name(self, engine: str) -> str:
        return re.sub(r"[^A-Za-z0-9]+", "_", engine).strip("_").lower()

    def _status_label(self, cell: dict[str, object]) -> str:
        status = str(cell.get("status", "pending"))
        if "score" in cell:
            suffix = "OK" if status == "valid" else "!"
            return f"{float(cell.get('score', 0)):.1f} {suffix}"
        labels = {
            "valid": "PASS",
            "invalid": "BAD",
            "done": "DONE",
            "fail": "FAIL",
            "pending": "-",
        }
        return labels.get(status, status.upper())

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

    def _grade_run(self) -> None:
        if self.process and self.process.poll() is None:
            self._append("Another process is already running.\n")
            return
        run_dir = self._current_run_dir()
        if not run_dir:
            self._append("No run directory available to grade.\n")
            return
        cmd = [
            sys.executable,
            str(ROOT / "grade_outputs.py"),
            "--run-dir",
            str(run_dir),
            "--tasks-file",
            self.tasks_file.get(),
        ]
        self._append("> " + " ".join(cmd) + "\n")
        threading.Thread(target=self._run_process, args=(cmd,), daemon=True).start()

    def _show_grades(self) -> None:
        run_dir = self._current_run_dir()
        if not run_dir:
            self._append("No run directory available.\n")
            return
        path = run_dir / "grades.json"
        if not path.exists():
            self._append(f"No grades found yet for {run_dir}. Press Grade Run first.\n")
            return
        try:
            grades = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            self._append(f"Could not read grades: {type(exc).__name__}\n")
            return
        self._append(f"\nGrades for {run_dir.name}\n")
        if isinstance(grades, list):
            for item in grades:
                if not isinstance(item, dict):
                    continue
                score = item.get("score", item.get("heuristic_score", "?"))
                self._append(
                    f"- {item.get('task_id')} | {item.get('engine')} | {score}/10 | {item.get('comment', '')}\n"
                )

    def _current_run_dir(self) -> Path | None:
        if self.state_path and self.state_path.exists():
            try:
                state = json.loads(self.state_path.read_text(encoding="utf-8"))
                run_dir = Path(str(state.get("run_dir", "")))
                if run_dir.exists():
                    return run_dir
            except (OSError, json.JSONDecodeError):
                pass
        candidates = [path for path in (ROOT / "results").iterdir() if path.is_dir()]
        if not candidates:
            return None
        return max(candidates, key=lambda path: path.stat().st_mtime)

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
            self._refresh_matrix()
        self.after(250, self._drain_events)

    def _append(self, text: str) -> None:
        self.log.insert(tk.END, text)
        self.log.see(tk.END)


if __name__ == "__main__":
    BenchmarkGui().mainloop()
