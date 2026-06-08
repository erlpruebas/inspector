from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from ..config import load_config


@dataclass
class LifecycleState:
    reload_requested: bool = False
    restart_requested: bool = False
    reason: str = ""
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class LifecycleManager:
    """Recarga y reinicio controlados."""

    def __init__(self, path: Optional[Path] = None) -> None:
        config = load_config()
        self.path = path or (config.workspace_root / "lifecycle.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> LifecycleState:
        if not self.path.exists():
            return LifecycleState()
        try:
            return LifecycleState(**json.loads(self.path.read_text(encoding="utf-8")))
        except Exception:
            return LifecycleState()

    def save(self, state: LifecycleState) -> LifecycleState:
        self.path.write_text(json.dumps(state.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")
        return state

    def request_reload(self, reason: str = "") -> LifecycleState:
        state = self.load()
        state.reload_requested = True
        state.reason = reason
        state.restart_requested = False
        state.updated_at = datetime.now(timezone.utc).isoformat()
        return self.save(state)

    def request_restart(self, reason: str = "") -> LifecycleState:
        state = self.load()
        state.restart_requested = True
        state.reason = reason
        state.reload_requested = False
        state.updated_at = datetime.now(timezone.utc).isoformat()
        return self.save(state)

    def clear(self) -> LifecycleState:
        state = LifecycleState()
        return self.save(state)
