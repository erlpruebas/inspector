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

    def search(self, query: str, limit: int = 12) -> list[str]:
        words = [word.casefold() for word in (query or "").split() if len(word) >= 3]
        try:
            lines = self.path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return []
        if not words:
            return lines[-limit:]
        matches = []
        for line in reversed(lines):
            folded = line.casefold()
            score = sum(1 for word in words if word in folded)
            if score:
                matches.append((score, line))
        matches.sort(key=lambda item: item[0], reverse=True)
        return [line for _score, line in matches[:limit]]
