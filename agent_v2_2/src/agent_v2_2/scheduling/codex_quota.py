from __future__ import annotations

import json
import logging
import os
import queue
import shutil
import subprocess
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from ..config import load_config

logger = logging.getLogger("agent_v2_2.scheduling.codex_quota")


@dataclass(frozen=True)
class CodexQuotaSnapshot:
    five_hour_remaining: int
    weekly_remaining: int
    five_hour_resets_at: Optional[int]
    weekly_resets_at: Optional[int]
    captured_at: float

    def is_fresh(self, max_age_seconds: int) -> bool:
        return time.time() - self.captured_at <= max_age_seconds

    def footer(self) -> str:
        five_reset = _format_reset(self.five_hour_resets_at, "%H.%M")
        weekly_reset = _format_reset(self.weekly_resets_at, "%d/%m")
        return (
            f"{self.five_hour_remaining}% {five_reset} "
            f"{self.weekly_remaining}% {weekly_reset}"
        )


class CodexQuotaMonitor:
    """Reads and persists the real Codex five-hour and weekly limits."""

    def __init__(
        self,
        *,
        snapshot_path: Optional[Path] = None,
        reader: Optional[Callable[[], CodexQuotaSnapshot]] = None,
    ) -> None:
        config = load_config()
        self.snapshot_path = snapshot_path or (config.workspace_root / "codex_quota.json")
        self.minimum_five_hour_percent = config.quota.minimum_quota_percent
        self.minimum_weekly_percent = config.quota.minimum_weekly_percent
        self.max_snapshot_age_seconds = config.quota.max_snapshot_age_seconds
        self._reader = reader or read_codex_rate_limits
        self._snapshot = self._load_snapshot()

    def refresh(self) -> CodexQuotaSnapshot:
        snapshot = self._reader()
        self._snapshot = snapshot
        self._save_snapshot(snapshot)
        return snapshot

    def snapshot(self, *, refresh: bool = False) -> Optional[CodexQuotaSnapshot]:
        if refresh:
            try:
                return self.refresh()
            except Exception as exc:
                logger.warning("Codex rate-limit refresh failed: %s", exc)
        return self._snapshot

    def can_schedule_codex(self, *, refresh: bool = False) -> bool:
        snapshot = self.snapshot(refresh=refresh)
        if snapshot is None or not snapshot.is_fresh(self.max_snapshot_age_seconds):
            return False
        return (
            snapshot.five_hour_remaining > self.minimum_five_hour_percent
            and snapshot.weekly_remaining > self.minimum_weekly_percent
        )

    def pause_reason(self, *, refresh: bool = False) -> Optional[str]:
        snapshot = self.snapshot(refresh=refresh)
        if snapshot is None:
            return "Codex quota is unknown."
        if not snapshot.is_fresh(self.max_snapshot_age_seconds):
            return "Codex quota snapshot is stale."
        if snapshot.weekly_remaining <= self.minimum_weekly_percent:
            return (
                f"Weekly Codex quota is at {snapshot.weekly_remaining}%; "
                f"reset {_format_reset(snapshot.weekly_resets_at, '%d/%m %H:%M')}."
            )
        if snapshot.five_hour_remaining <= self.minimum_five_hour_percent:
            return (
                f"Five-hour Codex quota is at {snapshot.five_hour_remaining}%; "
                f"reset {_format_reset(snapshot.five_hour_resets_at, '%d/%m %H:%M')}."
            )
        return None

    def should_reject(self, estimated_tokens: int = 0) -> bool:
        del estimated_tokens
        return not self.can_schedule_codex()

    def get_remaining_quota(self) -> str:
        snapshot = self.snapshot()
        if snapshot is None:
            return "Codex quota unavailable."
        return (
            f"Codex: {snapshot.five_hour_remaining}% five-hour, "
            f"{snapshot.weekly_remaining}% weekly."
        )

    def get_footer(self) -> Optional[str]:
        snapshot = self.snapshot()
        return snapshot.footer() if snapshot else None

    def record_usage(self, tool_id: str, tokens: int) -> None:
        # The server owns quota accounting. This remains as a compatibility hook.
        logger.debug("Codex usage completed: tool=%s tokens=%s", tool_id, max(0, int(tokens)))

    def _load_snapshot(self) -> Optional[CodexQuotaSnapshot]:
        if not self.snapshot_path.exists():
            return None
        try:
            payload = json.loads(self.snapshot_path.read_text(encoding="utf-8"))
            return CodexQuotaSnapshot(
                five_hour_remaining=_require_percent(payload.get("five_hour_remaining"), "five_hour"),
                weekly_remaining=_require_percent(payload.get("weekly_remaining"), "weekly"),
                five_hour_resets_at=_optional_timestamp(payload.get("five_hour_resets_at")),
                weekly_resets_at=_optional_timestamp(payload.get("weekly_resets_at")),
                captured_at=float(payload.get("captured_at")),
            )
        except Exception as exc:
            logger.warning("Could not load Codex quota snapshot: %s", exc)
            return None

    def _save_snapshot(self, snapshot: CodexQuotaSnapshot) -> None:
        self.snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        self.snapshot_path.write_text(
            json.dumps(asdict(snapshot), ensure_ascii=True, indent=2),
            encoding="utf-8",
        )


def read_codex_rate_limits() -> CodexQuotaSnapshot:
    process: Optional[subprocess.Popen[str]] = None
    try:
        process = _start_app_server()
        messages = _start_stdout_reader(process)
        _send_message(
            process,
            {
                "method": "initialize",
                "id": 0,
                "params": {
                    "clientInfo": {
                        "name": "inspector_agent_v2_2",
                        "title": "Inspector Agent 2.2",
                        "version": "0.1.0",
                    },
                    "capabilities": {"experimentalApi": True},
                },
            },
        )
        _wait_for_response(messages, 0)
        _send_message(process, {"method": "initialized", "params": {}})
        _send_message(
            process,
            {"method": "account/rateLimits/read", "id": 1, "params": None},
        )
        return parse_rate_limits_response(_wait_for_response(messages, 1))
    finally:
        _terminate_process(process)


def parse_rate_limits_response(payload: dict[str, Any]) -> CodexQuotaSnapshot:
    result = payload.get("result") or {}
    rate_limits = result.get("rateLimits") or {}
    primary = rate_limits.get("primary") or {}
    secondary = rate_limits.get("secondary") or {}
    return CodexQuotaSnapshot(
        five_hour_remaining=100 - _require_percent(primary.get("usedPercent"), "primary"),
        weekly_remaining=100 - _require_percent(secondary.get("usedPercent"), "secondary"),
        five_hour_resets_at=_optional_timestamp(primary.get("resetsAt")),
        weekly_resets_at=_optional_timestamp(secondary.get("resetsAt")),
        captured_at=time.time(),
    )


def _find_codex_executable() -> str:
    local = Path(os.getenv("LOCALAPPDATA", "")) / "Programs" / "OpenAI" / "Codex" / "bin" / "codex.exe"
    if local.is_file():
        return str(local)
    executable = shutil.which("codex") or shutil.which("codex.exe")
    if not executable:
        raise RuntimeError("Codex CLI executable was not found.")
    return executable


def _start_app_server() -> subprocess.Popen[str]:
    return subprocess.Popen(
        [_find_codex_executable(), "app-server", "--stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def _start_stdout_reader(process: subprocess.Popen[str]) -> queue.Queue[dict[str, Any]]:
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

    threading.Thread(target=read_lines, daemon=True, name="codex-quota-reader").start()
    return messages


def _send_message(process: subprocess.Popen[str], payload: dict[str, Any]) -> None:
    if process.stdin is None or process.poll() is not None:
        raise RuntimeError("Codex app-server is not running.")
    process.stdin.write(json.dumps(payload, ensure_ascii=True) + "\n")
    process.stdin.flush()


def _wait_for_response(
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


def _terminate_process(process: Optional[subprocess.Popen[str]]) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()


def _require_percent(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Missing {label} used percent.")
    return max(0, min(100, round(value)))


def _optional_timestamp(value: Any) -> Optional[int]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return round(value)


def _format_reset(value: Optional[int], pattern: str) -> str:
    if value is None:
        return "unknown"
    return datetime.fromtimestamp(value).strftime(pattern)
