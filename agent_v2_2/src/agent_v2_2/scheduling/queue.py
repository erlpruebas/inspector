import json
import uuid
from typing import Dict, List, Optional
from pathlib import Path
import logging
from datetime import datetime, timezone

from ..config import load_config
from ..models import TaskRequest

logger = logging.getLogger("agent_v2_2.scheduling.queue")

class PendingTask:
    def __init__(
        self,
        request: TaskRequest,
        status: str = "pending",
        task_id: Optional[str] = None,
        pause_reason: Optional[str] = None,
        updated_at: Optional[str] = None,
    ):
        self.task_id = task_id or str(uuid.uuid4())
        self.request = request
        self.status = status
        self.pause_reason = pause_reason
        self.updated_at = updated_at or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "request": self.request.model_dump(mode="json"),
            "status": self.status,
            "pause_reason": self.pause_reason,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'PendingTask':
        return cls(
            task_id=data["task_id"],
            request=TaskRequest.model_validate(data["request"]),
            status=data["status"],
            pause_reason=data.get("pause_reason"),
            updated_at=data.get("updated_at"),
        )

class TaskQueue:
    def __init__(self, store_path: Optional[Path] = None):
        config = load_config()
        self.store_path = store_path or (config.workspace_root / "task_queue.json")
        self.tasks: List[PendingTask] = []
        self.load()

    def load(self):
        if self.store_path.exists():
            try:
                data = json.loads(self.store_path.read_text("utf-8"))
                self.tasks = [PendingTask.from_dict(item) for item in data]
                # Reanudar tareas running a pending tras reinicio
                for t in self.tasks:
                    if t.status == "running":
                        t.status = "pending"
                        t.pause_reason = None
            except Exception as e:
                logger.error(f"Error loading tasks: {e}")
                self.tasks = []

    def save(self):
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        data = [task.to_dict() for task in self.tasks]
        self.store_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")

    def enqueue(self, request: TaskRequest) -> str:
        task = PendingTask(request=request)
        self.tasks.append(task)
        self.save()
        return task.task_id

    def list_tasks(self) -> List[PendingTask]:
        return self.tasks

    def get_next_pending(self) -> Optional[PendingTask]:
        for task in self.tasks:
            if task.status == "pending":
                return task
        return None

    def mark_running(self, task_id: str):
        for task in self.tasks:
            if task.task_id == task_id:
                task.status = "running"
                task.pause_reason = None
                task.updated_at = datetime.now(timezone.utc).isoformat()
                self.save()
                break

    def mark_completed(self, task_id: str):
        self.tasks = [t for t in self.tasks if t.task_id != task_id]
        self.save()

    def mark_paused(self, task_id: str, reason: str = "", status: str = "paused"):
        for task in self.tasks:
            if task.task_id == task_id:
                task.status = status
                task.pause_reason = reason or None
                task.updated_at = datetime.now(timezone.utc).isoformat()
                self.save()
                break

    def resume(self, task_id: str):
        for task in self.tasks:
            if task.task_id == task_id:
                task.status = "pending"
                task.pause_reason = None
                task.updated_at = datetime.now(timezone.utc).isoformat()
                self.save()
                break

    def clear(self):
        self.tasks = []
        self.save()
