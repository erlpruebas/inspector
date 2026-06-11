from __future__ import annotations

from datetime import datetime
from pathlib import Path
from threading import Lock


class MemoryLog:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def stamp() -> str:
        return datetime.now().strftime("%y%m%d%H%M%S")

    def write(self, event_type: str, text: str, source: str = "system", thread: str | None = None) -> None:
        clean_text = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
        thread_part = f" thread={thread}" if thread else ""
        block = [
            f"[{self.stamp()}] {event_type}{thread_part} source={source}",
            clean_text if clean_text else "(sin contenido)",
            "",
        ]
        with self._lock:
            with self.path.open("a", encoding="utf-8", errors="replace") as fh:
                fh.write("\n".join(block))
                fh.write("\n")
