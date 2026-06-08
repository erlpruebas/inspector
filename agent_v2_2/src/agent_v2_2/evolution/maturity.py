from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class MaturityReport:
    total_items: int
    completed_items: int
    pending_items: int
    completion_ratio: float
    critical_pending: List[str] = field(default_factory=list)

    @property
    def mature(self) -> bool:
        return self.pending_items == 0 or (self.completion_ratio >= 0.9 and not self.critical_pending)


class MaturityGate:
    """Evalúa si el sistema ya está lo bastante maduro para activar la fase evolutiva."""

    CRITICAL_HINTS = (
        "inbox y outbox",
        "progreso visible",
        "tiempos de transcripción",
        "recarga y reinicio",
        "degradación limpia",
    )

    def __init__(self, parity_matrix_path: Path) -> None:
        self.parity_matrix_path = parity_matrix_path

    def evaluate(self) -> MaturityReport:
        lines = self.parity_matrix_path.read_text(encoding="utf-8").splitlines()
        items = []
        for line in lines:
            if not line.startswith("|"):
                continue
            parts = [part.strip() for part in line.split("|") if part.strip()]
            if len(parts) < 5:
                continue
            status_cell = parts[-1].casefold()
            if any(token in status_cell for token in ("[x]", "completado", "[ ]", "pendiente")):
                items.append((line, status_cell))
        completed = [line for line, status in items if "[x]" in status or "completado" in status]
        pending = [line for line, status in items if "[ ]" in status or "pendiente" in status]
        critical_pending = [
            line for line in pending if any(hint in line.casefold() for hint in self.CRITICAL_HINTS)
        ]
        total = len(items)
        ratio = (len(completed) / total) if total else 0.0
        return MaturityReport(
            total_items=total,
            completed_items=len(completed),
            pending_items=len(pending),
            completion_ratio=ratio,
            critical_pending=critical_pending,
        )
