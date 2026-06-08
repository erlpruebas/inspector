from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from ..models import OperationTimings


@dataclass
class FlowMetrics:
    request_id: str
    timings: OperationTimings = field(default_factory=OperationTimings)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = None
    stages: Dict[str, float] = field(default_factory=dict)

    def mark_stage(self, name: str, seconds: float) -> None:
        self.stages[name] = max(0.0, float(seconds))
        setattr(self.timings, f"{name}_seconds", max(0.0, float(seconds)))
        self.timings.total_seconds = sum(self.stages.values())

    def finish(self) -> None:
        self.finished_at = datetime.now(timezone.utc)
        if not self.timings.total_seconds:
            self.timings.total_seconds = sum(self.stages.values())

    def to_dict(self) -> Dict[str, object]:
        return {
            "request_id": self.request_id,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "stages": dict(self.stages),
            "timings": self.timings.model_dump(),
        }

    def to_markdown(self) -> str:
        lines = [f"# Metrics for {self.request_id}", ""]
        for stage, seconds in self.stages.items():
            lines.append(f"- {stage}: {seconds:.3f}s")
        lines.append(f"- total: {self.timings.total_seconds:.3f}s")
        return "\n".join(lines)


class MetricsRecorder:
    def __init__(self) -> None:
        self._metrics: Dict[str, FlowMetrics] = {}

    def start(self, request_id: str) -> FlowMetrics:
        metrics = FlowMetrics(request_id=request_id)
        self._metrics[request_id] = metrics
        return metrics

    def get(self, request_id: str) -> Optional[FlowMetrics]:
        return self._metrics.get(request_id)

    def record_stage(self, request_id: str, stage: str, seconds: float) -> FlowMetrics:
        metrics = self._metrics.setdefault(request_id, FlowMetrics(request_id=request_id))
        metrics.mark_stage(stage, seconds)
        return metrics

    def finish(self, request_id: str) -> Optional[FlowMetrics]:
        metrics = self._metrics.get(request_id)
        if metrics:
            metrics.finish()
        return metrics

    def save_markdown(self, request_id: str, path: Path) -> Path:
        metrics = self._metrics[request_id]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(metrics.to_markdown(), encoding="utf-8")
        return path
