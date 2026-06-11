from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import Lock

from memory import MemoryLog


@dataclass
class PendingTask:
    id: str
    chat_id: int
    instruction: str
    thread_name: str
    source: str
    created_at: str


class PendingTaskStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write([])

    def add(self, chat_id: int, instruction: str, thread_name: str, source: str) -> PendingTask:
        task = PendingTask(
            id=uuid.uuid4().hex[:8],
            chat_id=chat_id,
            instruction=instruction,
            thread_name=thread_name,
            source=source,
            created_at=MemoryLog.stamp(),
        )
        with self._lock:
            tasks = self._read()
            tasks.append(task)
            self._write(tasks)
        return task

    def list(self) -> list[PendingTask]:
        with self._lock:
            return self._read()

    def pop_next(self) -> PendingTask | None:
        with self._lock:
            tasks = self._read()
            if not tasks:
                return None
            task = tasks.pop(0)
            self._write(tasks)
            return task

    def clear(self) -> int:
        with self._lock:
            tasks = self._read()
            self._write([])
            return len(tasks)

    def _read(self) -> list[PendingTask]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8") or "[]")
        except (OSError, json.JSONDecodeError):
            raw = []
        if not isinstance(raw, list):
            return []
        tasks: list[PendingTask] = []
        for item in raw:
            if isinstance(item, dict):
                try:
                    tasks.append(PendingTask(**item))
                except TypeError:
                    continue
        return tasks

    def _write(self, tasks: list[PendingTask]) -> None:
        self.path.write_text(json.dumps([asdict(task) for task in tasks], ensure_ascii=False, indent=2), encoding="utf-8")
