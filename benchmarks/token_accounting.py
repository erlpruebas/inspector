from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import re
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TokenUsageRecord:
    timestamp: str
    source: str
    component: str
    provider: str
    model: str
    operation: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated: bool = False
    prompt_chars: int = 0
    completion_chars: int = 0
    task_id: str = ""
    user_id: str = ""
    thread_id: str = ""
    run_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def record_usage(
    path: Path,
    *,
    source: str,
    component: str,
    provider: str,
    model: str,
    operation: str = "",
    usage: dict[str, Any] | None = None,
    prompt_text: str = "",
    completion_text: str = "",
    task_id: str = "",
    user_id: str = "",
    thread_id: str = "",
    run_id: str = "",
    metadata: dict[str, Any] | None = None,
) -> TokenUsageRecord:
    prompt_tokens, completion_tokens, total_tokens, estimated = normalize_usage(usage or {}, prompt_text, completion_text)
    record = TokenUsageRecord(
        timestamp=datetime.now(timezone.utc).isoformat(),
        source=source,
        component=component,
        provider=provider,
        model=model,
        operation=operation,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated=estimated,
        prompt_chars=len(prompt_text or ""),
        completion_chars=len(completion_text or ""),
        task_id=task_id,
        user_id=user_id,
        thread_id=thread_id,
        run_id=run_id,
        metadata=metadata or {},
    )
    append_record(path, record)
    return record


def append_record(path: Path, record: TokenUsageRecord) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")


def normalize_usage(
    usage: dict[str, Any],
    prompt_text: str = "",
    completion_text: str = "",
) -> tuple[int, int, int, bool]:
    if not isinstance(usage, dict):
        usage = {}
    payload = unwrap_usage(usage)
    prompt_tokens = as_int(
        payload.get("prompt_tokens"),
        payload.get("input_tokens"),
        payload.get("promptTokenCount"),
        payload.get("inputTokenCount"),
    )
    completion_tokens = as_int(
        payload.get("completion_tokens"),
        payload.get("output_tokens"),
        payload.get("candidates_tokens"),
        payload.get("candidatesTokenCount"),
        payload.get("outputTokenCount"),
    )
    total_tokens = as_int(
        payload.get("total_tokens"),
        payload.get("totalTokenCount"),
    )
    estimated = False
    if prompt_tokens == completion_tokens == total_tokens == 0:
        prompt_tokens = estimate_tokens(prompt_text)
        completion_tokens = estimate_tokens(completion_text)
        total_tokens = prompt_tokens + completion_tokens
        estimated = True
    else:
        if total_tokens == 0:
            total_tokens = prompt_tokens + completion_tokens
        if prompt_tokens == 0 and prompt_text:
            prompt_tokens = estimate_tokens(prompt_text)
            estimated = True
        if completion_tokens == 0 and completion_text:
            completion_tokens = estimate_tokens(completion_text)
            estimated = True
    return prompt_tokens, completion_tokens, total_tokens, estimated


def unwrap_usage(usage: dict[str, Any]) -> dict[str, Any]:
    if "usage" in usage and isinstance(usage["usage"], dict):
        return usage["usage"]
    if "usageMetadata" in usage and isinstance(usage["usageMetadata"], dict):
        return usage["usageMetadata"]
    return usage


def estimate_tokens(text: str) -> int:
    clean = re.sub(r"\s+", " ", (text or "").strip())
    if not clean:
        return 0
    return max(1, round(len(clean) / 4.0))


def as_int(*values: Any) -> int:
    for value in values:
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return 0


def summarize_usage(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"records": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "by_model": {}, "by_source": {}}
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    summary = {
        "records": len(rows),
        "prompt_tokens": sum(int(row.get("prompt_tokens", 0)) for row in rows),
        "completion_tokens": sum(int(row.get("completion_tokens", 0)) for row in rows),
        "total_tokens": sum(int(row.get("total_tokens", 0)) for row in rows),
        "by_model": {},
        "by_source": {},
    }
    for row in rows:
        model_key = f"{row.get('provider', '')}:{row.get('model', '')}".strip(":")
        model_bucket = summary["by_model"].setdefault(model_key, {"records": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
        model_bucket["records"] += 1
        model_bucket["prompt_tokens"] += int(row.get("prompt_tokens", 0))
        model_bucket["completion_tokens"] += int(row.get("completion_tokens", 0))
        model_bucket["total_tokens"] += int(row.get("total_tokens", 0))
        source_key = str(row.get("source", "unknown"))
        source_bucket = summary["by_source"].setdefault(source_key, {"records": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
        source_bucket["records"] += 1
        source_bucket["prompt_tokens"] += int(row.get("prompt_tokens", 0))
        source_bucket["completion_tokens"] += int(row.get("completion_tokens", 0))
        source_bucket["total_tokens"] += int(row.get("total_tokens", 0))
    return summary
