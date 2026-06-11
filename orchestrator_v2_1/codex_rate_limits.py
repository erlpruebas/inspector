from __future__ import annotations

import json
import logging
import os
import queue
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class CodexRateLimits:
    five_hour_remaining: int
    weekly_remaining: int
    five_hour_resets_at: int | None
    weekly_resets_at: int | None
    captured_at: float

    def footer(self) -> str:
        if self.five_hour_resets_at is None or self.weekly_resets_at is None:
            return ""
        five_hour_reset = datetime.fromtimestamp(self.five_hour_resets_at)
        weekly_reset = datetime.fromtimestamp(self.weekly_resets_at)
        return (
            f"{self.five_hour_remaining}% {five_hour_reset:%H.%M} "
            f"{self.weekly_remaining}% {weekly_reset.day}/{weekly_reset.month}"
        )


class CodexRateLimitMonitor:
    def __init__(self, *, refresh_seconds: float = 30) -> None:
        self.refresh_seconds = refresh_seconds
        self._snapshot: CodexRateLimits | None = None
        self._snapshot_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="codex-rate-limits", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def snapshot(self) -> CodexRateLimits | None:
        with self._snapshot_lock:
            return self._snapshot

    def footer(self) -> str:
        snapshot = self.snapshot()
        return snapshot.footer() if snapshot else ""

    def _run(self) -> None:
        while not self._stop_event.is_set():
            process: subprocess.Popen[str] | None = None
            try:
                process = start_app_server()
                messages = start_stdout_reader(process)
                initialize_app_server(process, messages)
                while not self._stop_event.is_set():
                    response = request_rate_limits(process, messages)
                    snapshot = parse_rate_limits_response(response)
                    with self._snapshot_lock:
                        self._snapshot = snapshot
                    self._stop_event.wait(self.refresh_seconds)
            except Exception as exc:
                logging.warning("Codex rate-limit monitor unavailable: %s", exc)
                self._stop_event.wait(min(self.refresh_seconds, 10))
            finally:
                terminate_process(process)


def start_app_server() -> subprocess.Popen[str]:
    executable = find_codex_executable()
    return subprocess.Popen(
        [executable, "app-server", "--stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def find_codex_executable() -> str:
    local = os.path.join(
        os.getenv("LOCALAPPDATA", ""),
        "Programs",
        "OpenAI",
        "Codex",
        "bin",
        "codex.exe",
    )
    if os.path.isfile(local):
        return local
    executable = shutil.which("codex") or shutil.which("codex.exe")
    if not executable:
        raise RuntimeError("Codex CLI executable was not found.")
    return executable


def start_stdout_reader(process: subprocess.Popen[str]) -> queue.Queue[dict[str, Any]]:
    messages: queue.Queue[dict[str, Any]] = queue.Queue()

    def read_lines() -> None:
        if process.stdout is None:
            return
        for line in process.stdout:
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                messages.put(payload)

    threading.Thread(target=read_lines, name="codex-rate-limit-reader", daemon=True).start()
    return messages


def initialize_app_server(
    process: subprocess.Popen[str],
    messages: queue.Queue[dict[str, Any]],
) -> None:
    send_message(
        process,
        {
            "method": "initialize",
            "id": 0,
            "params": {
                "clientInfo": {
                    "name": "inspector_orchestrator",
                    "title": "Inspector Orchestrator",
                    "version": "0.1.0",
                },
                "capabilities": {"experimentalApi": True},
            },
        },
    )
    wait_for_response(messages, 0)
    send_message(process, {"method": "initialized", "params": {}})


def request_rate_limits(
    process: subprocess.Popen[str],
    messages: queue.Queue[dict[str, Any]],
) -> dict[str, Any]:
    send_message(process, {"method": "account/rateLimits/read", "id": 1, "params": None})
    return wait_for_response(messages, 1)


def send_message(process: subprocess.Popen[str], payload: dict[str, Any]) -> None:
    if process.stdin is None or process.poll() is not None:
        raise RuntimeError("Codex app-server is not running.")
    process.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
    process.stdin.flush()


def wait_for_response(
    messages: queue.Queue[dict[str, Any]],
    request_id: int,
    *,
    timeout: float = 15,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            payload = messages.get(timeout=min(0.5, max(0.01, deadline - time.monotonic())))
        except queue.Empty:
            continue
        if payload.get("id") != request_id:
            continue
        if payload.get("error"):
            raise RuntimeError(str(payload["error"]))
        return payload
    raise TimeoutError(f"Codex app-server did not answer request {request_id}.")


def parse_rate_limits_response(payload: dict[str, Any]) -> CodexRateLimits:
    result = payload.get("result") or {}
    rate_limits = result.get("rateLimits") or {}
    primary = rate_limits.get("primary") or {}
    secondary = rate_limits.get("secondary") or {}
    primary_used = require_percent(primary.get("usedPercent"), "primary")
    secondary_used = require_percent(secondary.get("usedPercent"), "secondary")
    return CodexRateLimits(
        five_hour_remaining=100 - primary_used,
        weekly_remaining=100 - secondary_used,
        five_hour_resets_at=optional_timestamp(primary.get("resetsAt")),
        weekly_resets_at=optional_timestamp(secondary.get("resetsAt")),
        captured_at=time.time(),
    )


def require_percent(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Missing {label}.usedPercent.")
    return max(0, min(100, round(value)))


def optional_timestamp(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return round(value)


def terminate_process(process: subprocess.Popen[str] | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
