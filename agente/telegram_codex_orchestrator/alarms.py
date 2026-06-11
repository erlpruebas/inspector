from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock


WEEKDAYS = {
    "lunes": 0,
    "martes": 1,
    "miercoles": 2,
    "miércoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sabado": 5,
    "sábado": 5,
    "domingo": 6,
}

HOUR_WORDS = {
    "cero": 0,
    "una": 1,
    "uno": 1,
    "dos": 2,
    "tres": 3,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "nueve": 9,
    "diez": 10,
    "once": 11,
    "doce": 12,
}

AMOUNT_WORDS = {
    **HOUR_WORDS,
    "un": 1,
}


@dataclass
class Alarm:
    id: str
    chat_id: int
    text: str
    next_due: str
    recurrence: str = "once"
    weekday: int | None = None
    day_of_month: int | None = None
    hour: int | None = None
    minute: int = 0
    created_at: str = ""
    enabled: bool = True

    @property
    def due_datetime(self) -> datetime:
        return datetime.fromisoformat(self.next_due)


@dataclass(frozen=True)
class ParsedAlarm:
    text: str
    due_at: datetime
    recurrence: str = "once"
    weekday: int | None = None
    day_of_month: int | None = None
    hour: int | None = None
    minute: int = 0


class AlarmStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write([])

    def add(self, chat_id: int, parsed: ParsedAlarm) -> Alarm:
        alarm = Alarm(
            id=uuid.uuid4().hex[:8],
            chat_id=chat_id,
            text=parsed.text,
            next_due=parsed.due_at.isoformat(timespec="seconds"),
            recurrence=parsed.recurrence,
            weekday=parsed.weekday,
            day_of_month=parsed.day_of_month,
            hour=parsed.hour,
            minute=parsed.minute,
            created_at=datetime.now().isoformat(timespec="seconds"),
        )
        with self._lock:
            alarms = self._read()
            alarms.append(alarm)
            self._write(alarms)
        return alarm

    def list_enabled(self, chat_id: int) -> list[Alarm]:
        with self._lock:
            return [a for a in self._read() if a.enabled and a.chat_id == chat_id]

    def cancel(self, chat_id: int, alarm_id: str) -> bool:
        found = False
        with self._lock:
            alarms = self._read()
            for alarm in alarms:
                if alarm.chat_id == chat_id and alarm.id.lower() == alarm_id.lower() and alarm.enabled:
                    alarm.enabled = False
                    found = True
            self._write(alarms)
        return found

    def due(self, now: datetime) -> list[Alarm]:
        with self._lock:
            return [a for a in self._read() if a.enabled and a.due_datetime <= now]

    def mark_fired(self, alarm: Alarm, now: datetime) -> Alarm | None:
        with self._lock:
            alarms = self._read()
            updated: Alarm | None = None
            for item in alarms:
                if item.id != alarm.id:
                    continue
                if item.recurrence == "once":
                    item.enabled = False
                else:
                    item.next_due = _next_recurring_due(item, now).isoformat(timespec="seconds")
                    updated = item
            self._write(alarms)
            return updated

    def _read(self) -> list[Alarm]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8") or "[]")
        except (OSError, json.JSONDecodeError):
            raw = []
        return [Alarm(**item) for item in raw]

    def _write(self, alarms: list[Alarm]) -> None:
        data = [asdict(alarm) for alarm in alarms]
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_alarm_request(text: str, now: datetime | None = None) -> ParsedAlarm | None:
    now = now or datetime.now()
    normalized = _normalize(text)
    if not _looks_like_alarm(normalized):
        return None

    relative = _parse_relative(normalized, now)
    if relative:
        due_at, reminder = relative
        return ParsedAlarm(text=reminder, due_at=due_at)

    daily = _parse_daily(normalized, now)
    if daily:
        due_at, hour, minute, reminder = daily
        return ParsedAlarm(text=reminder, due_at=due_at, recurrence="daily", hour=hour, minute=minute)

    weekly = _parse_weekly(normalized, now)
    if weekly:
        due_at, weekday, hour, minute, reminder = weekly
        return ParsedAlarm(
            text=reminder,
            due_at=due_at,
            recurrence="weekly",
            weekday=weekday,
            hour=hour,
            minute=minute,
        )

    monthly = _parse_monthly(normalized, now)
    if monthly:
        due_at, day, hour, minute, reminder = monthly
        return ParsedAlarm(
            text=reminder,
            due_at=due_at,
            recurrence="monthly",
            day_of_month=day,
            hour=hour,
            minute=minute,
        )

    tomorrow = _parse_tomorrow(normalized, now)
    if tomorrow:
        due_at, reminder = tomorrow
        return ParsedAlarm(text=reminder, due_at=due_at)

    today = _parse_today_at(normalized, now)
    if today:
        due_at, reminder = today
        return ParsedAlarm(text=reminder, due_at=due_at)

    return None


def format_alarm(alarm: Alarm) -> str:
    due = alarm.due_datetime.strftime("%d/%m/%Y %H:%M")
    repeat = "" if alarm.recurrence == "once" else f" | {alarm.recurrence}"
    return f"{alarm.id} | {due}{repeat} | {alarm.text}"


def confirmation_text(alarm: Alarm) -> str:
    return "Alarma creada:\n" + format_alarm(alarm)


def _looks_like_alarm(text: str) -> bool:
    starts = (
        "avisame",
        "avísame",
        "recuerdame",
        "recuérdame",
        "recordame",
        "alarma",
        "ponme una alarma",
        "pon una alarma",
        "haz ",
    )
    temporal = ("dentro de", "mañana", "manana", "todos los", "cada ")
    return text.startswith(starts) or any(chunk in text for chunk in temporal)


def _parse_relative(text: str, now: datetime) -> tuple[datetime, str] | None:
    amount_pattern = r"\d+|" + "|".join(sorted(AMOUNT_WORDS, key=len, reverse=True))
    match = re.search(rf"(?:dentro de|en)\s+({amount_pattern})\s+(minutos|minuto|horas|hora|dias|dia|días|día)", text)
    if not match:
        return None
    amount = _amount_value(match.group(1))
    unit = match.group(2)
    if unit.startswith("minuto"):
        due_at = now + timedelta(minutes=amount)
    elif unit.startswith("hora"):
        due_at = now + timedelta(hours=amount)
    else:
        due_at = now + timedelta(days=amount)
    return due_at, _extract_reminder(text, match.end())


def _amount_value(value: str) -> int:
    if value.isdigit():
        return int(value)
    return AMOUNT_WORDS.get(value, 1)


def _parse_tomorrow(text: str, now: datetime) -> tuple[datetime, str] | None:
    if "mañana" not in text and "manana" not in text:
        return None
    time_match = _find_time(text)
    if not time_match:
        return None
    hour, minute, end = time_match
    due_at = (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
    return due_at, _extract_reminder(text, end)


def _parse_today_at(text: str, now: datetime) -> tuple[datetime, str] | None:
    if " a la" not in text and " a las " not in text and " hoy " not in text:
        return None
    time_match = _find_time(text)
    if not time_match:
        return None
    hour, minute, end = time_match
    due_at = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if due_at <= now:
        due_at += timedelta(days=1)
    return due_at, _extract_reminder(text, end)


def _parse_daily(text: str, now: datetime) -> tuple[datetime, int, int, str] | None:
    if "todos los dias" not in text and "todos los días" not in text and "cada dia" not in text and "cada día" not in text:
        return None
    time_match = _find_time(text)
    if not time_match:
        return None
    hour, minute, end = time_match
    due_at = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if due_at <= now:
        due_at += timedelta(days=1)
    return due_at, hour, minute, _extract_reminder(text, end)


def _parse_weekly(text: str, now: datetime) -> tuple[datetime, int, int, str] | None:
    weekday_match = re.search(r"(?:todos los|cada)\s+(lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)", text)
    if not weekday_match:
        return None
    time_match = _find_time(text)
    if not time_match:
        return None
    hour, minute, end = time_match
    weekday = WEEKDAYS[weekday_match.group(1)]
    due_at = _next_weekday(now, weekday, hour, minute)
    return due_at, weekday, hour, minute, _extract_reminder(text, end)


def _parse_monthly(text: str, now: datetime) -> tuple[datetime, int, int, str] | None:
    match = re.search(r"(?:todos los meses|cada mes).{0,30}?\b(?:dia|día)\s+(\d{1,2})", text)
    if not match:
        return None
    time_match = _find_time(text)
    if not time_match:
        return None
    day = int(match.group(1))
    if not 1 <= day <= 31:
        return None
    hour, minute, end = time_match
    due_at = _next_month_day(now, day, hour, minute)
    return due_at, day, hour, minute, _extract_reminder(text, end)


def _find_time(text: str) -> tuple[int, int, int] | None:
    match = re.search(r"(?:a\s+las|a\s+la|las|la)\s+(\d{1,2})(?::(\d{2}))?(?:\s*(?:h|horas))?(?:\s+de\s+la\s+(mañana|manana|tarde|noche))?", text)
    if not match:
        match = re.search(r"\b(\d{1,2}):(\d{2})\b", text)
        if not match:
            word_pattern = "|".join(HOUR_WORDS)
            match = re.search(rf"(?:a\s+las|a\s+la|las|la)?\s*\b({word_pattern})\b(?:\s+de\s+la\s+(mañana|manana|tarde|noche))?", text)
            if not match:
                return None
            hour = HOUR_WORDS[match.group(1)]
            minute = 0
            suffix = match.group(2)
            if suffix in {"tarde", "noche"} and hour < 12:
                hour += 12
            return hour, minute, match.end()
    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    suffix = match.group(3) if match.lastindex and match.lastindex >= 3 else None
    if suffix in {"tarde", "noche"} and hour < 12:
        hour += 12
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return hour, minute, match.end()


def _extract_reminder(text: str, start_at: int) -> str:
    tail = text[start_at:].strip(" .,:;-")
    for prefix in ("de ", "que ", "para ", "hacer ", "haz "):
        if tail.startswith(prefix):
            tail = tail[len(prefix) :].strip()
            break
    if tail:
        return tail
    cleaned = re.sub(r"^(avisame|avísame|recuerdame|recuérdame|recordame|alarma)\s+", "", text).strip()
    return cleaned or "recordatorio"


def _next_weekday(now: datetime, weekday: int, hour: int, minute: int) -> datetime:
    days = (weekday - now.weekday()) % 7
    due_at = (now + timedelta(days=days)).replace(hour=hour, minute=minute, second=0, microsecond=0)
    if due_at <= now:
        due_at += timedelta(days=7)
    return due_at


def _next_month_day(now: datetime, day: int, hour: int, minute: int) -> datetime:
    year = now.year
    month = now.month
    while True:
        try:
            due_at = datetime(year, month, day, hour, minute)
        except ValueError:
            month, year = _next_month(year, month)
            continue
        if due_at > now:
            return due_at
        month, year = _next_month(year, month)


def _next_month(year: int, month: int) -> tuple[int, int]:
    month += 1
    if month > 12:
        return 1, year + 1
    return month, year


def _next_recurring_due(alarm: Alarm, now: datetime) -> datetime:
    hour = alarm.hour if alarm.hour is not None else alarm.due_datetime.hour
    minute = alarm.minute
    if alarm.recurrence == "daily":
        due_at = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if due_at <= now:
            due_at += timedelta(days=1)
        return due_at
    if alarm.recurrence == "weekly" and alarm.weekday is not None:
        return _next_weekday(now, alarm.weekday, hour, minute)
    if alarm.recurrence == "monthly" and alarm.day_of_month is not None:
        return _next_month_day(now, alarm.day_of_month, hour, minute)
    return now + timedelta(days=1)


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())
