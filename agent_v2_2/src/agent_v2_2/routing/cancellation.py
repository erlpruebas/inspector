from __future__ import annotations

import threading
from collections.abc import Callable


class CancellationManager:
    """Tracks active executions and invokes their concrete cancellation hook."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._active: dict[str, tuple[str, Callable[[str], bool]]] = {}

    def register(
        self,
        owner_id: str,
        execution_id: str,
        cancel_callback: Callable[[str], bool],
    ) -> None:
        with self._lock:
            self._active[owner_id] = (execution_id, cancel_callback)

    def cancel_owner(self, owner_id: str) -> bool:
        with self._lock:
            active = self._active.get(owner_id)
        if active is None:
            return False
        execution_id, callback = active
        return bool(callback(execution_id))

    def active_execution(self, owner_id: str) -> str | None:
        with self._lock:
            active = self._active.get(owner_id)
        return active[0] if active else None

    def clear_owner(self, owner_id: str, execution_id: str | None = None) -> None:
        with self._lock:
            active = self._active.get(owner_id)
            if active is None:
                return
            if execution_id is None or active[0] == execution_id:
                self._active.pop(owner_id, None)
