from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class TaskRecord:
    task_id: str
    title: str
    source_path: Path
    category: str = ""
    block: str = ""
    skills: List[str] = field(default_factory=list)
    required_files: List[str] = field(default_factory=list)
    requires_network: bool = False
    expected_operation: str = ""
    route_hypothesis: str = ""


@dataclass
class TaskAuditReport:
    total_tasks: int
    categories: Dict[str, int]
    skills: Dict[str, int]
    files: Dict[str, int]
    network_tasks: int
    records: List[TaskRecord] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = [f"# Task audit ({self.total_tasks} tasks)", ""]
        lines.append("## Categories")
        for key, count in sorted(self.categories.items()):
            lines.append(f"- {key}: {count}")
        lines.append("")
        lines.append("## Skills")
        for key, count in sorted(self.skills.items()):
            lines.append(f"- {key}: {count}")
        lines.append("")
        lines.append(f"- network tasks: {self.network_tasks}")
        return "\n".join(lines)


class TaskAuditor:
    def __init__(self, task_paths: Optional[Iterable[Path]] = None) -> None:
        self.task_paths = [Path(path) for path in (task_paths or [])]

    def collect_paths(self, root: Path) -> List[Path]:
        if self.task_paths:
            return [path for path in self.task_paths if path.exists()]
        if root.is_file():
            return [root]
        return sorted(root.rglob("*.json"))

    def load_records(self, paths: Iterable[Path]) -> List[TaskRecord]:
        records: List[TaskRecord] = []
        for path in paths:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(payload, list):
                continue
            for index, item in enumerate(payload):
                if not isinstance(item, dict):
                    continue
                task_id = str(item.get("id") or item.get("task_id") or f"{path.stem}-{index+1}")
                title = str(item.get("title") or item.get("name") or item.get("prompt") or task_id)
                records.append(
                    TaskRecord(
                        task_id=task_id,
                        title=title,
                        source_path=path,
                        category=str(item.get("category") or ""),
                        block=str(item.get("block") or ""),
                        skills=[str(skill) for skill in item.get("skills", []) if skill],
                        required_files=[str(file) for file in item.get("required_files", []) if file],
                        requires_network=bool(item.get("requires_network", False)),
                        expected_operation=str(item.get("expected_operation") or ""),
                        route_hypothesis=str(item.get("route_hypothesis") or ""),
                    )
                )
        return records

    def audit(self, root: Path) -> TaskAuditReport:
        records = self.load_records(self.collect_paths(root))
        return self._build_report(records)

    def audit_paths(self, paths: Iterable[Path]) -> TaskAuditReport:
        records = self.load_records([Path(path) for path in paths if Path(path).exists()])
        return self._build_report(records)

    def _build_report(self, records: List[TaskRecord]) -> TaskAuditReport:
        categories = Counter(record.category or record.block or "uncategorized" for record in records)
        skills = Counter(skill for record in records for skill in record.skills)
        files = Counter(file for record in records for file in record.required_files)
        network_tasks = sum(1 for record in records if record.requires_network)
        return TaskAuditReport(
            total_tasks=len(records),
            categories=dict(categories),
            skills=dict(skills),
            files=dict(files),
            network_tasks=network_tasks,
            records=records,
        )
