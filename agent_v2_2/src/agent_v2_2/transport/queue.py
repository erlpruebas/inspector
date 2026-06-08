from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from ..config import load_config


@dataclass
class MailboxEntry:
    execution_id: str
    direction: str
    message: str
    chat_id: Optional[int] = None
    media_file_id: Optional[str] = None
    media_type: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ExecutionMailbox:
    """Inbox y outbox aislados por ejecución."""

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        config = load_config()
        self.base_dir = (base_dir or config.workspace_root / "mailboxes").resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _execution_dir(self, execution_id: str) -> Path:
        return self.base_dir / execution_id

    def _box_path(self, execution_id: str, direction: str) -> Path:
        return self._execution_dir(execution_id) / f"{direction}.json"

    def _load(self, execution_id: str, direction: str) -> List[MailboxEntry]:
        path = self._box_path(execution_id, direction)
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return [MailboxEntry(**item) for item in data]
        except Exception:
            return []

    def _save(self, execution_id: str, direction: str, entries: List[MailboxEntry]) -> None:
        path = self._box_path(execution_id, direction)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps([entry.__dict__ for entry in entries], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def append_inbox(
        self,
        execution_id: Optional[str],
        message: str,
        chat_id: Optional[int] = None,
        media_file_id: Optional[str] = None,
        media_type: Optional[str] = None,
    ) -> str:
        execution_id = execution_id or str(uuid4())
        entries = self._load(execution_id, "inbox")
        entries.append(
            MailboxEntry(
                execution_id=execution_id,
                direction="inbox",
                message=message,
                chat_id=chat_id,
                media_file_id=media_file_id,
                media_type=media_type,
            )
        )
        self._save(execution_id, "inbox", entries)
        return execution_id

    def append_outbox(self, execution_id: str, message: str, chat_id: Optional[int] = None) -> None:
        entries = self._load(execution_id, "outbox")
        entries.append(
            MailboxEntry(
                execution_id=execution_id,
                direction="outbox",
                message=message,
                chat_id=chat_id,
            )
        )
        self._save(execution_id, "outbox", entries)

    def list_inbox(self, execution_id: str) -> List[MailboxEntry]:
        return self._load(execution_id, "inbox")

    def list_outbox(self, execution_id: str) -> List[MailboxEntry]:
        return self._load(execution_id, "outbox")

    def clear(self, execution_id: str) -> None:
        for direction in ("inbox", "outbox"):
            path = self._box_path(execution_id, direction)
            if path.exists():
                path.unlink()
        execution_dir = self._execution_dir(execution_id)
        if execution_dir.exists():
            try:
                execution_dir.rmdir()
            except OSError:
                pass
