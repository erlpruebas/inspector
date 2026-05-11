from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from threading import Lock

from memory import MemoryLog


DEFAULT_THREADS = {
    "alarmas": {
        "title": "Alarmas y recordatorios temporales",
        "kind": "alarms",
        "summary": "Hilo algorítmico para crear, listar y disparar alarmas.",
        "tags": ["alarmas", "recordatorios"],
    },
    "recuerdos": {
        "title": "Recuerdos persistentes",
        "kind": "memories",
        "summary": "Hilo algorítmico para guardar y consultar recuerdos.",
        "tags": ["memoria", "recuerdos"],
    },
    "busquedas": {
        "title": "Búsquedas e informes",
        "kind": "codex",
        "summary": "Hilo Codex para investigar, compilar datos y preparar informes.",
        "tags": ["investigacion", "informes"],
    },
    "desarrollo": {
        "title": "Desarrollo y herramientas",
        "kind": "codex",
        "summary": "Hilo Codex para tocar código, crear herramientas y modificar proyectos.",
        "tags": ["codigo", "herramientas"],
    },
}


@dataclass
class ThreadRecord:
    name: str
    title: str
    kind: str = "codex"
    codex_thread_id: str = ""
    workdir: str = ""
    extra_dirs: list[str] = field(default_factory=list)
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


class ThreadStore:
    def __init__(self, path: Path, default_workdir: Path, default_extra_dirs: list[Path]) -> None:
        self.path = path
        self.default_workdir = default_workdir
        self.default_extra_dirs = default_extra_dirs
        self._lock = Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_file()

    def active_name(self) -> str:
        data = self._read_data()
        return str(data.get("active_thread") or "desarrollo")

    def active(self) -> ThreadRecord:
        return self.get(self.active_name())

    def get(self, name: str) -> ThreadRecord:
        safe = normalize_thread_name(name)
        with self._lock:
            data = self._read_data()
            threads = data.setdefault("threads", {})
            if safe not in threads:
                threads[safe] = asdict(self._new_record(safe, title=safe.replace("_", " ").title()))
                self._write_data(data)
            return ThreadRecord(**threads[safe])

    def list(self) -> list[ThreadRecord]:
        data = self._read_data()
        threads = data.get("threads", {})
        return [ThreadRecord(**value) for _, value in sorted(threads.items())]

    def set_active(self, name: str) -> ThreadRecord:
        record = self.get(name)
        with self._lock:
            data = self._read_data()
            data["active_thread"] = record.name
            self._write_data(data)
        return record

    def create(self, name: str, title: str | None = None, kind: str = "codex") -> ThreadRecord:
        safe = normalize_thread_name(name)
        with self._lock:
            data = self._read_data()
            threads = data.setdefault("threads", {})
            if safe not in threads:
                threads[safe] = asdict(self._new_record(safe, title=title or safe.replace("_", " ").title(), kind=kind))
            data["active_thread"] = safe
            self._write_data(data)
            return ThreadRecord(**threads[safe])

    def update_codex_thread_id(self, name: str, codex_thread_id: str) -> ThreadRecord:
        safe = normalize_thread_name(name)
        with self._lock:
            data = self._read_data()
            threads = data.setdefault("threads", {})
            record = threads.get(safe) or asdict(self._new_record(safe, title=safe.replace("_", " ").title()))
            record["codex_thread_id"] = codex_thread_id
            record["updated_at"] = MemoryLog.stamp()
            threads[safe] = record
            self._write_data(data)
            return ThreadRecord(**record)

    def choose_for_codex(self, instruction: str, suggested: str | None = None) -> ThreadRecord:
        if suggested:
            return self.get(suggested)
        lower = instruction.lower()
        research_words = ("busca", "buscar", "investiga", "informe", "noticias", "compila", "recopila", "resume informacion")
        dev_words = ("codigo", "código", "programa", "implementa", "modifica", "archivo", "herramienta", "visual studio", "proyecto")
        if any(word in lower for word in research_words):
            return self.get("busquedas")
        if any(word in lower for word in dev_words):
            return self.get("desarrollo")
        return self.active()

    def _new_record(self, name: str, title: str, kind: str = "codex") -> ThreadRecord:
        stamp = MemoryLog.stamp()
        return ThreadRecord(
            name=name,
            title=title,
            kind=kind,
            workdir=str(self.default_workdir),
            extra_dirs=[str(path) for path in self.default_extra_dirs],
            created_at=stamp,
            updated_at=stamp,
        )

    def _ensure_file(self) -> None:
        if self.path.exists():
            data = self._read_data()
        else:
            data = {"active_thread": "desarrollo", "threads": {}}
        changed = False
        threads = data.setdefault("threads", {})
        for name, meta in DEFAULT_THREADS.items():
            if name in threads:
                continue
            record = self._new_record(name, meta["title"], kind=meta["kind"])
            record.summary = meta["summary"]
            record.tags = list(meta["tags"])
            threads[name] = asdict(record)
            changed = True
        data.setdefault("active_thread", "desarrollo")
        if changed or not self.path.exists():
            self._write_data(data)

    def _read_data(self) -> dict:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8") or "{}")
        except (OSError, json.JSONDecodeError):
            raw = {}
        if not isinstance(raw, dict):
            raw = {}
        raw.setdefault("active_thread", "desarrollo")
        raw.setdefault("threads", {})
        return raw

    def _write_data(self, data: dict) -> None:
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_thread_name(value: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ_-]+", "_", (value or "").strip().lower())
    safe = safe.strip("_")
    return safe or "desarrollo"
