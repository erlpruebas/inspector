from __future__ import annotations

from pathlib import Path
from threading import Lock

from memory import MemoryLog


class RememberStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("", encoding="utf-8")

    def add(self, text: str) -> None:
        stamp = MemoryLog.stamp()
        clean = " ".join((text or "").split())
        if not clean:
            return
        with self._lock:
            with self.path.open("a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"[{stamp}] {clean}\n")

    def tail(self, limit: int = 20) -> list[str]:
        try:
            lines = self.path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return []
        return lines[-limit:]
