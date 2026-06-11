from __future__ import annotations

import calendar
import json
import logging
import re
import threading
import time
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, List, Optional

from ..config import load_config


logger = logging.getLogger("agent_v2_2.scheduling.alarms")


@dataclass
class Alarm:
    chat_id: int
    message: str
    trigger_at: float
    recurrence: str = "none"
    alarm_id: str = ""

    def __post_init__(self) -> None:
        if not self.alarm_id:
            self.alarm_id = str(uuid.uuid4())

    def to_dict(self) -> dict:
        return {
            "alarm_id": self.alarm_id,
            "chat_id": self.chat_id,
            "message": self.message,
            "trigger_at": self.trigger_at,
            "recurrence": self.recurrence,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Alarm":
        return cls(
            alarm_id=str(data["alarm_id"]),
            chat_id=int(data["chat_id"]),
            message=str(data["message"]),
            trigger_at=float(data["trigger_at"]),
            recurrence=str(data.get("recurrence", "none")),
        )


@dataclass(frozen=True)
class AlarmRequest:
    message: str
    trigger_at: float
    recurrence: str = "none"


class AlarmScheduler:
    def __init__(
        self,
        callback: Callable[[int, str], None],
        *,
        store_path: Optional[Path] = None,
        poll_seconds: float = 1.0,
    ) -> None:
        config = load_config()
        self.store_path = store_path or (config.workspace_root / "alarms.json")
        self.callback = callback
        self.poll_seconds = poll_seconds
        self.alarms: List[Alarm] = []
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.load()

    def load(self) -> None:
        with self._lock:
            if not self.store_path.exists():
                self.alarms = []
                return
            try:
                payload = json.loads(self.store_path.read_text(encoding="utf-8"))
                self.alarms = [
                    Alarm.from_dict(item)
                    for item in payload
                    if isinstance(item, dict)
                ]
            except Exception as exc:
                logger.error("Could not load alarms: %s", exc)
                self.alarms = []

    def save(self) -> None:
        with self._lock:
            self.store_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.store_path.with_suffix(".tmp")
            temporary.write_text(
                json.dumps(
                    [alarm.to_dict() for alarm in self.alarms],
                    ensure_ascii=True,
                    indent=2,
                ),
                encoding="utf-8",
            )
            temporary.replace(self.store_path)

    def add(self, chat_id: int, request: AlarmRequest) -> Alarm:
        alarm = Alarm(
            chat_id=chat_id,
            message=request.message,
            trigger_at=request.trigger_at,
            recurrence=request.recurrence,
        )
        with self._lock:
            self.alarms.append(alarm)
            self.alarms.sort(key=lambda item: item.trigger_at)
            self.save()
        return alarm

    def add_alarm_relative(
        self,
        chat_id: int,
        message: str,
        seconds: int,
        recurrence: str = "none",
    ) -> str:
        return self.add(
            chat_id,
            AlarmRequest(message, time.time() + seconds, recurrence),
        ).alarm_id

    def add_alarm_absolute(
        self,
        chat_id: int,
        message: str,
        trigger_at: float,
        recurrence: str = "none",
    ) -> str:
        return self.add(
            chat_id,
            AlarmRequest(message, trigger_at, recurrence),
        ).alarm_id

    def list_alarms(self, chat_id: int) -> List[Alarm]:
        with self._lock:
            return sorted(
                (alarm for alarm in self.alarms if alarm.chat_id == chat_id),
                key=lambda item: item.trigger_at,
            )

    def cancel_alarm(self, alarm_id_or_prefix: str, chat_id: Optional[int] = None) -> bool:
        identifier = alarm_id_or_prefix.strip().casefold()
        with self._lock:
            before = len(self.alarms)
            self.alarms = [
                alarm
                for alarm in self.alarms
                if not (
                    alarm.alarm_id.casefold().startswith(identifier)
                    and (chat_id is None or alarm.chat_id == chat_id)
                )
            ]
            changed = len(self.alarms) != before
            if changed:
                self.save()
            return changed

    def tick(self, *, now: Optional[float] = None) -> int:
        current = time.time() if now is None else now
        with self._lock:
            triggered = [alarm for alarm in self.alarms if alarm.trigger_at <= current]
        delivered = 0
        for alarm in triggered:
            try:
                self.callback(alarm.chat_id, alarm.message)
                delivered += 1
            except Exception as exc:
                logger.error("Could not deliver alarm %s: %s", alarm.alarm_id, exc)
                continue
            with self._lock:
                if alarm.recurrence == "none":
                    self.alarms = [
                        item for item in self.alarms if item.alarm_id != alarm.alarm_id
                    ]
                else:
                    alarm.trigger_at = _next_recurrence(
                        alarm.trigger_at,
                        alarm.recurrence,
                    )
        if triggered:
            self.save()
        return delivered

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
            name="agent22-alarm-scheduler",
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=max(1.0, self.poll_seconds * 2))

    def _run(self) -> None:
        while not self._stop_event.wait(self.poll_seconds):
            self.tick()


def parse_alarm_request(
    text: str,
    *,
    now: Optional[datetime] = None,
) -> Optional[AlarmRequest]:
    current = now or datetime.now().astimezone()
    normalized = _normalize(text)

    relative = re.match(
        r"^(?:recuerdame|avisame)(?:\s+dentro\s+de|\s+en)\s+"
        r"(\d+)\s*(segundos?|minutos?|horas?|dias?)\s+(?:que\s+)?(.+)$",
        normalized,
    )
    if relative:
        amount = int(relative.group(1))
        unit = relative.group(2)
        message = relative.group(3).strip()
        multipliers = {
            "segundo": 1,
            "segundos": 1,
            "minuto": 60,
            "minutos": 60,
            "hora": 3600,
            "horas": 3600,
            "dia": 86400,
            "dias": 86400,
        }
        return AlarmRequest(
            message=message,
            trigger_at=current.timestamp() + amount * multipliers[unit],
        )

    tomorrow = re.match(
        r"^(?:recuerdame|avisame)\s+manana\s+a\s+las\s+"
        r"(\d{1,2}):(\d{2})\s+(?:que\s+)?(.+)$",
        normalized,
    )
    if tomorrow:
        trigger = (current + timedelta(days=1)).replace(
            hour=int(tomorrow.group(1)),
            minute=int(tomorrow.group(2)),
            second=0,
            microsecond=0,
        )
        return AlarmRequest(tomorrow.group(3).strip(), trigger.timestamp())

    absolute = re.match(
        r"^(?:recuerdame|avisame)\s+el\s+(\d{1,2})/(\d{1,2})/(\d{4})"
        r"\s+a\s+las\s+(\d{1,2}):(\d{2})\s+(?:que\s+)?(.+)$",
        normalized,
    )
    if absolute:
        trigger = current.replace(
            year=int(absolute.group(3)),
            month=int(absolute.group(2)),
            day=int(absolute.group(1)),
            hour=int(absolute.group(4)),
            minute=int(absolute.group(5)),
            second=0,
            microsecond=0,
        )
        if trigger.timestamp() <= current.timestamp():
            return None
        return AlarmRequest(absolute.group(6).strip(), trigger.timestamp())

    recurring = re.match(
        r"^(?:recuerdame|avisame)\s+cada\s+(dia|semana|mes)"
        r"\s+a\s+las\s+(\d{1,2}):(\d{2})\s+(?:que\s+)?(.+)$",
        normalized,
    )
    if recurring:
        recurrence = {
            "dia": "daily",
            "semana": "weekly",
            "mes": "monthly",
        }[recurring.group(1)]
        trigger = current.replace(
            hour=int(recurring.group(2)),
            minute=int(recurring.group(3)),
            second=0,
            microsecond=0,
        )
        if trigger <= current:
            trigger = datetime.fromtimestamp(
                _next_recurrence(trigger.timestamp(), recurrence),
                tz=current.tzinfo,
            )
        return AlarmRequest(
            recurring.group(4).strip(),
            trigger.timestamp(),
            recurrence,
        )
    return None


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", (text or "").casefold())
    without_accents = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return " ".join(without_accents.strip().split()).strip(" .,!¡?¿")


def _next_recurrence(timestamp: float, recurrence: str) -> float:
    current = datetime.fromtimestamp(timestamp).astimezone()
    if recurrence == "daily":
        return (current + timedelta(days=1)).timestamp()
    if recurrence == "weekly":
        return (current + timedelta(days=7)).timestamp()
    if recurrence == "monthly":
        month = 1 if current.month == 12 else current.month + 1
        year = current.year + 1 if current.month == 12 else current.year
        day = min(current.day, calendar.monthrange(year, month)[1])
        return current.replace(year=year, month=month, day=day).timestamp()
    return timestamp
