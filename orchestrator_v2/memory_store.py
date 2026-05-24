from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any

from .workspace import UserWorkspace, workspace_for


STOPWORDS = {
    "para",
    "como",
    "con",
    "que",
    "los",
    "las",
    "una",
    "uno",
    "del",
    "por",
    "este",
    "esta",
    "the",
    "and",
    "you",
}


@dataclass(frozen=True)
class MemoryEvent:
    stamp: str
    user_id: str
    thread_id: str
    kind: str
    request: str
    response: str = ""
    source: str = "orchestrator"
    metadata: dict[str, Any] | None = None


class MemoryStore:
    def __init__(self, workspace: UserWorkspace):
        self.workspace = workspace.ensure()

    @classmethod
    def for_user(cls, user_id: str, thread_id: str = "default") -> "MemoryStore":
        return cls(workspace_for(user_id, thread_id))

    def append_interaction(
        self,
        *,
        request: str,
        response: str,
        kind: str = "interaction",
        source: str = "orchestrator",
        metadata: dict[str, Any] | None = None,
    ) -> MemoryEvent:
        event = MemoryEvent(
            stamp=datetime.now().strftime("%Y%m%d_%H%M%S_%f"),
            user_id=self.workspace.user_id,
            thread_id=self.workspace.thread_id,
            kind=kind,
            request=request,
            response=response,
            source=source,
            metadata=metadata or {},
        )
        self._append_jsonl(self.workspace.memory / "events.jsonl", asdict(event))
        self._update_keyword_index(event)
        return event

    def append_procedure_note(self, *, title: str, method: str, outcome: str) -> None:
        note = {
            "stamp": datetime.now().strftime("%Y%m%d_%H%M%S_%f"),
            "title": title,
            "method": method,
            "outcome": outcome,
        }
        self._append_jsonl(self.workspace.memory / "procedure_notes.jsonl", note)

    def load_keyword_index(self) -> dict[str, list[str]]:
        path = self.workspace.memory / "keyword_index.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _update_keyword_index(self, event: MemoryEvent) -> None:
        index = self.load_keyword_index()
        for keyword in extract_keywords(f"{event.request}\n{event.response}"):
            stamps = index.setdefault(keyword, [])
            if event.stamp not in stamps:
                stamps.append(event.stamp)
        path = self.workspace.memory / "keyword_index.json"
        path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def extract_keywords(text: str) -> list[str]:
    raw = re.findall(r"[A-Za-z0-9_@.+-]{4,}", text.casefold())
    seen: set[str] = set()
    keywords: list[str] = []
    for item in raw:
        if item in STOPWORDS or item in seen:
            continue
        seen.add(item)
        keywords.append(item)
    return keywords[:80]
