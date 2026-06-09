from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ..config import load_config
from ..models import TaskRequest
from .codex_quota import CodexQuotaMonitor
from .queue import PendingTask, TaskQueue


CODEX_TOOL_MARKERS = ("codex", "gpt-5.5", "gpt_5_5")


@dataclass
class AutonomousCheckpoint:
    status: str
    reason: str
    current_task_id: Optional[str]
    next_action: str
    updated_at: str


class QuotaAwareScheduler:
    """Selects runnable work while preserving Codex quota and queue state."""

    def __init__(
        self,
        *,
        task_queue: Optional[TaskQueue] = None,
        quota_monitor: Optional[CodexQuotaMonitor] = None,
        checkpoint_path: Optional[Path] = None,
    ) -> None:
        config = load_config()
        self.task_queue = task_queue or TaskQueue()
        self.quota_monitor = quota_monitor or CodexQuotaMonitor()
        self.checkpoint_path = checkpoint_path or (
            config.workspace_root / "autonomous_checkpoint.json"
        )

    def next_runnable(self, *, refresh_quota: bool = True) -> Optional[PendingTask]:
        codex_allowed: Optional[bool] = None
        quota_reason: Optional[str] = None

        for task in self.task_queue.list_tasks():
            if task.status not in {"pending", "paused_quota"}:
                continue
            if not requires_codex(task.request):
                if task.status == "paused_quota":
                    self.task_queue.resume(task.task_id)
                return task

            if codex_allowed is None:
                codex_allowed = self.quota_monitor.can_schedule_codex(
                    refresh=refresh_quota
                )
                quota_reason = self.quota_monitor.pause_reason()

            if codex_allowed:
                if task.status == "paused_quota":
                    self.task_queue.resume(task.task_id)
                return task

            if task.status != "paused_quota" or task.pause_reason != quota_reason:
                self.task_queue.mark_paused(
                    task.task_id,
                    reason=quota_reason or "Codex quota unavailable.",
                    status="paused_quota",
                )

        self.write_checkpoint(
            status="waiting",
            reason=quota_reason or "No runnable tasks.",
            current_task_id=None,
            next_action="Refresh quota and inspect the persistent task queue.",
        )
        return None

    def write_checkpoint(
        self,
        *,
        status: str,
        reason: str,
        current_task_id: Optional[str],
        next_action: str,
    ) -> AutonomousCheckpoint:
        checkpoint = AutonomousCheckpoint(
            status=status,
            reason=reason,
            current_task_id=current_task_id,
            next_action=next_action,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path.write_text(
            json.dumps(asdict(checkpoint), ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
        return checkpoint

    def load_checkpoint(self) -> Optional[AutonomousCheckpoint]:
        if not self.checkpoint_path.exists():
            return None
        payload = json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
        return AutonomousCheckpoint(**payload)


def requires_codex(request: TaskRequest) -> bool:
    candidates = [
        request.tool_name,
        str(request.metadata.get("tool_id", "")),
        str(request.metadata.get("engine", "")),
        str(request.metadata.get("model", "")),
    ]
    normalized = " ".join(candidates).casefold()
    return any(marker in normalized for marker in CODEX_TOOL_MARKERS)
