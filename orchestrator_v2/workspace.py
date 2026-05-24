from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


DEFAULT_RUNTIME_ROOT = Path("orchestrator_v2/runtime")


def safe_id(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return clean[:80] or "default"


@dataclass(frozen=True)
class UserWorkspace:
    root: Path
    user_id: str
    thread_id: str

    @property
    def user_root(self) -> Path:
        return self.root / "users" / safe_id(self.user_id)

    @property
    def thread_root(self) -> Path:
        return self.user_root / "threads" / safe_id(self.thread_id)

    @property
    def inbox(self) -> Path:
        return self.thread_root / "inbox"

    @property
    def outbox(self) -> Path:
        return self.thread_root / "outbox"

    @property
    def memory(self) -> Path:
        return self.user_root / "memory"

    @property
    def config_path(self) -> Path:
        return self.user_root / "config" / "preferences.json"

    def ensure(self) -> "UserWorkspace":
        for path in (self.inbox, self.outbox, self.memory, self.config_path.parent):
            path.mkdir(parents=True, exist_ok=True)
        return self


def workspace_for(user_id: str, thread_id: str = "default", root: Path = DEFAULT_RUNTIME_ROOT) -> UserWorkspace:
    return UserWorkspace(root=root, user_id=user_id, thread_id=thread_id).ensure()
