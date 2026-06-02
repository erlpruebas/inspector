from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def record_usage(
    path: Path,
    *,
    source: str,
    component: str,
    provider: str,
    model: str,
    operation: str,
    prompt_text: str,
    completion_text: str,
    task_id: str = "",
    user_id: str = "",
    thread_id: str = "",
    metadata: dict[str, Any] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "source": source,
        "component": component,
        "provider": provider,
        "model": model,
        "operation": operation,
        "prompt_chars": len(prompt_text or ""),
        "completion_chars": len(completion_text or ""),
        "task_id": task_id,
        "user_id": user_id,
        "thread_id": thread_id,
        "metadata": metadata or {},
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
