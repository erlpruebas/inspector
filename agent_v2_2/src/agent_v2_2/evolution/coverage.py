from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from .audit import TaskAuditor, TaskRecord


FORMAT_BUCKETS = {
    "text",
    "markdown",
    "csv",
    "json",
    "jsonl",
    "pdf",
    "image",
    "office",
    "audio",
    "zip",
    "code",
    "email",
    "web",
}


def _bucket_from_file(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in {".md", ".markdown"}:
        return "markdown"
    if suffix in {".txt", ".log", ".rst"}:
        return "text"
    if suffix in {".csv", ".tsv"}:
        return "csv"
    if suffix in {".json"}:
        return "json"
    if suffix in {".jsonl"}:
        return "jsonl"
    if suffix in {".pdf"}:
        return "pdf"
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".tiff", ".heic"}:
        return "image"
    if suffix in {".doc", ".docx", ".odt", ".rtf", ".xls", ".xlsx", ".ods", ".ppt", ".pptx"}:
        return "office"
    if suffix in {".mp3", ".wav", ".ogg", ".m4a"}:
        return "audio"
    if suffix in {".zip", ".rar", ".7z", ".tar", ".gz"}:
        return "zip"
    if suffix in {".py", ".js", ".ts", ".html", ".css", ".sh", ".ps1", ".bat"}:
        return "code"
    if suffix in {".eml", ".msg", ".mbox"}:
        return "email"
    return "text"


@dataclass
class CoverageReport:
    total_tasks: int
    categories: Dict[str, int] = field(default_factory=dict)
    levels: Dict[str, int] = field(default_factory=dict)
    skills: Dict[str, int] = field(default_factory=dict)
    dimensions: Dict[str, Dict[str, int]] = field(default_factory=dict)
    file_buckets: Dict[str, int] = field(default_factory=dict)
    network_tasks: int = 0

    def missing_buckets(self) -> List[str]:
        return sorted(bucket for bucket in FORMAT_BUCKETS if bucket not in self.file_buckets)

    def to_markdown(self) -> str:
        lines = [f"# Task coverage report ({self.total_tasks} tasks)", ""]
        lines.append("## Categories")
        for key, count in sorted(self.categories.items()):
            lines.append(f"- {key}: {count}")
        lines.append("")
        lines.append("## Levels")
        for key, count in sorted(self.levels.items()):
            lines.append(f"- {key}: {count}")
        lines.append("")
        lines.append("## Skills")
        for key, count in sorted(self.skills.items()):
            lines.append(f"- {key}: {count}")
        lines.append("")
        lines.append("## Dimensions")
        for dim, counts in sorted(self.dimensions.items()):
            lines.append(f"- {dim}:")
            for key, count in sorted(counts.items()):
                lines.append(f"  - {key}: {count}")
        lines.append("")
        lines.append("## File buckets")
        for key, count in sorted(self.file_buckets.items()):
            lines.append(f"- {key}: {count}")
        lines.append("")
        lines.append(f"- network tasks: {self.network_tasks}")
        lines.append("")
        lines.append("## Missing buckets")
        missing = self.missing_buckets()
        if missing:
            for bucket in missing:
                lines.append(f"- {bucket}")
        else:
            lines.append("- none")
        return "\n".join(lines)


class TaskCoverageAnalyzer:
    def __init__(self) -> None:
        self.auditor = TaskAuditor()

    def analyze(self, root: Path) -> CoverageReport:
        records = self.auditor.load_records(self.auditor.collect_paths(root))
        return self._build_report(records)

    def _build_report(self, records: List[TaskRecord]) -> CoverageReport:
        categories = Counter(record.category or record.block or "uncategorized" for record in records)
        levels = Counter(record.level or "unknown" for record in records)
        skills = Counter(skill for record in records for skill in record.skills)
        file_buckets = Counter(_bucket_from_file(file) for record in records for file in record.required_files)
        dimensions: Dict[str, Counter] = {}
        for record in records:
            if record.requires_network:
                file_buckets["web"] += 1
            for key, value in record.dimensions.items():
                if not value:
                    continue
                dim_name = str(key)
                dimensions.setdefault(dim_name, Counter())
                dimensions[dim_name][str(value)] += 1
                bucket = str(value).casefold()
                if dim_name in {"tool_need", "output_form"} and bucket in FORMAT_BUCKETS:
                    file_buckets[bucket] += 1
        return CoverageReport(
            total_tasks=len(records),
            categories=dict(categories),
            levels=dict(levels),
            skills=dict(skills),
            dimensions={key: dict(counter) for key, counter in dimensions.items()},
            file_buckets=dict(file_buckets),
            network_tasks=sum(1 for record in records if record.requires_network),
        )
