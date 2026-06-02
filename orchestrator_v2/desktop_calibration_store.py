from __future__ import annotations

import os
import re
import socket
from pathlib import Path


RUNTIME_ROOT = Path("orchestrator_v2/runtime/desktop_codex_operator")
MACHINES_ROOT = RUNTIME_ROOT / "machines"
TRACKED_CALIBRATIONS_ROOT = Path("configs/desktop_calibrations")
DEFAULT_CALIBRATION_FILE = RUNTIME_ROOT / "calibration.json"
DEFAULT_CLICK_PROFILE_FILE = RUNTIME_ROOT / "codex_click_profile.json"
MOUSE_CAPTURE_FILE = RUNTIME_ROOT / "mouse_coordinate_captures.jsonl"


def safe_id(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return clean[:80] or "default"


def machine_name() -> str:
    for key in ("COMPUTERNAME", "HOSTNAME"):
        value = os.getenv(key, "").strip()
        if value:
            return value
    return socket.gethostname().strip() or "default"


def machine_id() -> str:
    return safe_id(machine_name())


def machine_root() -> Path:
    return MACHINES_ROOT / machine_id()


def tracked_machine_root() -> Path:
    return TRACKED_CALIBRATIONS_ROOT / machine_id()


def machine_calibration_file() -> Path:
    return machine_root() / "calibration.json"


def tracked_machine_calibration_file() -> Path:
    return tracked_machine_root() / "calibration.json"


def machine_click_profile_file() -> Path:
    return machine_root() / "codex_click_profile.json"


def machine_mouse_capture_file() -> Path:
    return machine_root() / "mouse_coordinate_captures.jsonl"
