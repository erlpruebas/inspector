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
    prompt: str = ""
    user_request: str = ""
    category: str = ""
    block: str = ""
    level: str = ""
    skills: List[str] = field(default_factory=list)
    required_files: List[str] = field(default_factory=list)
    requires_network: bool = False
    expected_operation: str = ""
    route_hypothesis: str = ""
    expected_outputs: List[str] = field(default_factory=list)
    expected_keys: List[str] = field(default_factory=list)
    rubric: Dict[str, Any] = field(default_factory=dict)
    dimensions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskAuditReport:
    total_tasks: int
    categories: Dict[str, int]
    skills: Dict[str, int]
    files: Dict[str, int]
    network_tasks: int
    invalid_files: Dict[str, str] = field(default_factory=dict)
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
        lines.append(f"- invalid or missing fixtures: {len(self.invalid_files)}")
        for name, reason in sorted(self.invalid_files.items()):
            lines.append(f"  - {name}: {reason}")
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
                item = self._enrich_suite_item(path, task_id, item)
                title = str(item.get("title") or item.get("name") or item.get("prompt") or task_id)
                records.append(
                    TaskRecord(
                        task_id=task_id,
                        title=title,
                    source_path=path,
                    prompt=str(item.get("prompt") or ""),
                    user_request=str(item.get("user_request") or ""),
                    category=str(item.get("category") or ""),
                    block=str(item.get("block") or ""),
                    level=str(item.get("level") or ""),
                    skills=[str(skill) for skill in item.get("skills", []) if skill],
                    required_files=[str(file) for file in item.get("required_files", []) if file],
                    requires_network=bool(item.get("requires_network", False)),
                    expected_operation=str(item.get("expected_operation") or ""),
                    route_hypothesis=str(item.get("route_hypothesis") or ""),
                    expected_outputs=[str(output) for output in item.get("expected_outputs", []) if output],
                    expected_keys=[str(key) for key in item.get("expected_keys", []) if key],
                    rubric=dict(item.get("rubric") or {}),
                    dimensions=dict(item.get("dimensions") or {}),
                )
            )
        return records

    def _enrich_suite_item(
        self,
        index_path: Path,
        task_id: str,
        item: Dict[str, Any],
    ) -> Dict[str, Any]:
        task_dir = index_path.parent / task_id
        task_markdown = task_dir / "task.md"
        metadata_path = task_dir / "metadata.json"
        if not task_markdown.exists() and not metadata_path.exists():
            return item

        enriched = dict(item)
        if metadata_path.exists():
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            except Exception:
                metadata = {}
            if isinstance(metadata, dict):
                enriched.update(metadata)
        if task_markdown.exists():
            prompt = task_markdown.read_text(
                encoding="utf-8",
                errors="replace",
            ).strip()
            if prompt:
                enriched["prompt"] = prompt
        return enriched

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
        invalid_files: Dict[str, str] = {}
        for file_name in files:
            path = resolve_fixture_file(file_name)
            if path is None:
                invalid_files[file_name] = "missing"
                continue
            reason = fixture_validation_error(path)
            if reason:
                invalid_files[file_name] = reason
        return TaskAuditReport(
            total_tasks=len(records),
            categories=dict(categories),
            skills=dict(skills),
            files=dict(files),
            network_tasks=network_tasks,
            invalid_files=invalid_files,
            records=records,
        )


def resolve_fixture_file(relative: str) -> Path | None:
    candidates = (
        Path.cwd() / relative,
        Path.cwd() / "benchmarks" / "assets" / relative,
        Path.cwd() / "benchmarks" / "tasks" / relative,
    )
    return next((path for path in candidates if path.is_file()), None)


def fixture_validation_error(path: Path) -> str:
    suffix = path.suffix.casefold()
    try:
        header = path.read_bytes()[:16]
    except OSError:
        return "unreadable"
    if suffix == ".pdf" and not header.startswith(b"%PDF-"):
        return "extension is PDF but content has no PDF signature"
    if suffix in {".docx", ".xlsx", ".pptx", ".zip"} and not header.startswith(b"PK"):
        return f"extension is {suffix[1:]} but content has no ZIP signature"
    if suffix in {".png"} and not header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "extension is PNG but content has no PNG signature"
    if suffix in {".jpg", ".jpeg"} and not header.startswith(b"\xff\xd8\xff"):
        return "extension is JPEG but content has no JPEG signature"
    if suffix == ".wav" and not (
        header.startswith(b"RIFF") and header[8:12] == b"WAVE"
    ):
        return "extension is WAV but content has no WAV signature"
    return ""
