from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DesktopCodexResult:
    text: str
    screenshot_path: Path | None = None
    thread_id: str = ""


def run_desktop_codex_operator(*args, **kwargs) -> DesktopCodexResult:
    raise RuntimeError("Codex Desktop operator is not bundled in the clean agent build. Use Codex CLI mode.")


def capture_desktop_screenshot(*args, **kwargs) -> Path | None:
    return None
