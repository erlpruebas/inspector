import json
import uuid
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Callable
import logging

from ..config import load_config

logger = logging.getLogger("agent_v2_2.scheduling.alarms")

class Alarm:
    def __init__(self, chat_id: int, message: str, trigger_at: float, 
                 recurrence: str = "none", alarm_id: Optional[str] = None):
        self.alarm_id = alarm_id or str(uuid.uuid4())
        self.chat_id = chat_id
        self.message = message
        self.trigger_at = trigger_at
        self.recurrence = recurrence # "none", "daily", "weekly", "monthly"

    def to_dict(self) -> Dict:
        return {
            "alarm_id": self.alarm_id,
            "chat_id": self.chat_id,
            "message": self.message,
            "trigger_at": self.trigger_at,
            "recurrence": self.recurrence
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Alarm':
        return cls(
            alarm_id=data["alarm_id"],
            chat_id=data["chat_id"],
            message=data["message"],
            trigger_at=data["trigger_at"],
            recurrence=data.get("recurrence", "none")
        )

class AlarmScheduler:
    def __init__(self, callback: Callable[[int, str], None]):
        config = load_config()
        self.store_path = config.workspace_root / "alarms.json"
        self.alarms: List[Alarm] = []
        self.callback = callback
        self.load()

    def load(self):
        if self.store_path.exists():
            try:
                data = json.loads(self.store_path.read_text("utf-8"))
                self.alarms = [Alarm.from_dict(item) for item in data]
            except Exception as e:
                logger.error(f"Error loading alarms: {e}")
                self.alarms = []

    def save(self):
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        data = [alarm.to_dict() for alarm in self.alarms]
        self.store_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")

    def add_alarm_relative(self, chat_id: int, message: str, seconds: int, recurrence: str = "none") -> str:
        trigger_at = time.time() + seconds
        return self.add_alarm_absolute(chat_id, message, trigger_at, recurrence)

    def add_alarm_absolute(self, chat_id: int, message: str, trigger_at: float, recurrence: str = "none") -> str:
        alarm = Alarm(chat_id, message, trigger_at, recurrence)
        self.alarms.append(alarm)
        self.save()
        return alarm.alarm_id

    def list_alarms(self, chat_id: int) -> List[Alarm]:
        return [a for a in self.alarms if a.chat_id == chat_id]

    def cancel_alarm(self, alarm_id: str) -> bool:
        initial_len = len(self.alarms)
        self.alarms = [a for a in self.alarms if a.alarm_id != alarm_id]
        if len(self.alarms) < initial_len:
            self.save()
            return True
        return False

    def tick(self):
        now = time.time()
        triggered = [a for a in self.alarms if a.trigger_at <= now]
        if not triggered:
            return

        for alarm in triggered:
            try:
                self.callback(alarm.chat_id, alarm.message)
            except Exception as e:
                logger.error(f"Failed to deliver alarm {alarm.alarm_id}: {e}")

            if alarm.recurrence == "daily":
                alarm.trigger_at += 86400
            elif alarm.recurrence == "weekly":
                alarm.trigger_at += 86400 * 7
            elif alarm.recurrence == "monthly":
                alarm.trigger_at += 86400 * 30 # Aprox
            else:
                self.alarms.remove(alarm)
        
        self.save()
