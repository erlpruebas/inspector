from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

from ..config import load_config


@dataclass
class ObjectiveCheck:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class JudgeScore:
    judge: str
    score: float
    passed: bool
    comment: str = ""


@dataclass
class RouterExperience:
    experience_id: str
    timestamp: str
    catalog_version: int
    task_id: str
    task_shape: str
    tool_id: str
    required_capabilities: List[str] = field(default_factory=list)
    cognitive_requirements: List[str] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    objective_checks: Dict[str, Any] = field(default_factory=dict)
    judge_scores: List[Dict[str, Any]] = field(default_factory=list)
    user_feedback: Optional[str] = None
    outcome: str = "insufficient"
    failure_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experience_id": self.experience_id,
            "timestamp": self.timestamp,
            "catalog_version": self.catalog_version,
            "task_id": self.task_id,
            "task_shape": self.task_shape,
            "tool_id": self.tool_id,
            "required_capabilities": list(self.required_capabilities),
            "cognitive_requirements": list(self.cognitive_requirements),
            "elapsed_seconds": self.elapsed_seconds,
            "objective_checks": self.objective_checks,
            "judge_scores": self.judge_scores,
            "user_feedback": self.user_feedback,
            "outcome": self.outcome,
            "failure_reason": self.failure_reason,
            "metadata": self.metadata,
        }


class ExperienceStore:
    """Almacena experiencias del router con el esquema versionado."""

    def __init__(
        self,
        path: Optional[Path] = None,
        *,
        bootstrap_seed: bool = False,
    ) -> None:
        config = load_config()
        using_default_path = path is None
        self.path = path or (config.workspace_root / "evolution" / "experiences.jsonl")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if (using_default_path or bootstrap_seed) and not self.path.exists():
            seed = (
                Path(__file__).resolve().parents[3]
                / "data"
                / "router_seed_experiences.jsonl"
            )
            if seed.exists():
                shutil.copy2(seed, self.path)

    def append(self, experience: RouterExperience) -> RouterExperience:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(experience.to_dict(), ensure_ascii=False) + "\n")
        return experience

    def append_many(self, experiences: Iterable[RouterExperience]) -> int:
        items = list(experiences)
        if not items:
            return 0
        with self.path.open("a", encoding="utf-8") as handle:
            for experience in items:
                handle.write(json.dumps(experience.to_dict(), ensure_ascii=False) + "\n")
        return len(items)

    def load(self) -> List[RouterExperience]:
        if not self.path.exists():
            return []
        records: List[RouterExperience] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except Exception:
                continue
            records.append(
                RouterExperience(
                    experience_id=str(payload.get("experience_id") or uuid4()),
                    timestamp=str(payload.get("timestamp") or datetime.now(timezone.utc).isoformat()),
                    catalog_version=int(payload.get("catalog_version") or 1),
                    task_id=str(payload.get("task_id") or ""),
                    task_shape=str(payload.get("task_shape") or ""),
                    tool_id=str(payload.get("tool_id") or ""),
                    required_capabilities=list(payload.get("required_capabilities") or []),
                    cognitive_requirements=list(payload.get("cognitive_requirements") or []),
                    elapsed_seconds=float(payload.get("elapsed_seconds") or 0.0),
                    objective_checks=dict(payload.get("objective_checks") or {}),
                    judge_scores=list(payload.get("judge_scores") or []),
                    user_feedback=payload.get("user_feedback"),
                    outcome=str(payload.get("outcome") or "insufficient"),
                    failure_reason=payload.get("failure_reason"),
                    metadata=dict(payload.get("metadata") or {}),
                )
            )
        return records

    def count(self) -> int:
        return sum(1 for _ in self.load())

    def by_tool(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for experience in self.load():
            counts[experience.tool_id] = counts.get(experience.tool_id, 0) + 1
        return counts

    def existing_keys(self) -> set[tuple[str, str, str]]:
        keys: set[tuple[str, str, str]] = set()
        for experience in self.load():
            keys.add(
                (
                    experience.task_id,
                    experience.tool_id,
                    str(experience.metadata.get("source_summary", "")),
                )
            )
        return keys

    def record_feedback(
        self,
        experience_id: str,
        feedback: str,
        *,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        records = self.load()
        updated = False
        for record in records:
            if record.experience_id != experience_id:
                continue
            record.user_feedback = feedback
            if metadata:
                record.metadata.update(metadata)
            updated = True
            break
        if not updated:
            return False
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
        temporary.replace(self.path)
        return True

    def invalidate(
        self,
        experience_ids: Iterable[str],
        reason: str,
    ) -> int:
        targets = {str(item) for item in experience_ids if str(item)}
        if not targets:
            return 0
        records = self.load()
        updated = 0
        timestamp = datetime.now(timezone.utc).isoformat()
        for record in records:
            if record.experience_id not in targets:
                continue
            record.metadata["evidence_invalidated"] = True
            record.metadata["invalidation_reason"] = reason
            record.metadata["invalidated_at"] = timestamp
            updated += 1
        if not updated:
            return 0
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
        temporary.replace(self.path)
        return updated

    def restore(self, experience_ids: Iterable[str]) -> int:
        targets = {str(item) for item in experience_ids if str(item)}
        if not targets:
            return 0
        records = self.load()
        updated = 0
        for record in records:
            if record.experience_id not in targets:
                continue
            if not bool(record.metadata.get("evidence_invalidated")):
                continue
            record.metadata.pop("evidence_invalidated", None)
            record.metadata.pop("invalidation_reason", None)
            record.metadata.pop("invalidated_at", None)
            updated += 1
        if not updated:
            return 0
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
        temporary.replace(self.path)
        return updated

    def export_portable_seed(self, destination: Path) -> int:
        records = []
        for record in self.load():
            if str(record.metadata.get("evidence_kind", "")).casefold() != "live":
                continue
            if bool(record.metadata.get("evidence_invalidated")):
                continue
            judgements = [
                {
                    "judge": "gemini-blind",
                    "score": float(judgement["score"]),
                    "passed": bool(judgement["passed"]),
                    "comment": "",
                    "capability_scores": dict(
                        judgement["capability_scores"]
                    ),
                }
                for judgement in record.judge_scores
                if isinstance(judgement, dict)
                and isinstance(judgement.get("score"), (int, float))
                and isinstance(judgement.get("passed"), bool)
                and isinstance(judgement.get("capability_scores"), dict)
                and bool(judgement.get("capability_scores"))
            ]
            if not judgements:
                continue
            portable = RouterExperience(
                experience_id=record.experience_id,
                timestamp=record.timestamp,
                catalog_version=record.catalog_version,
                task_id=record.task_id,
                task_shape=record.task_shape,
                tool_id=record.tool_id,
                required_capabilities=list(record.required_capabilities),
                cognitive_requirements=list(record.cognitive_requirements),
                elapsed_seconds=record.elapsed_seconds,
                objective_checks={
                    "passed": bool(record.objective_checks.get("passed")),
                    "hard_passed": bool(
                        record.objective_checks.get(
                            "hard_passed",
                            record.objective_checks.get("passed"),
                        )
                    ),
                    "checks": [
                        {
                            "name": str(check.get("name") or ""),
                            "passed": bool(check.get("passed")),
                            "detail": "",
                        }
                        for check in record.objective_checks.get("checks", [])
                        if isinstance(check, dict)
                    ],
                },
                judge_scores=judgements,
                user_feedback=None,
                outcome=record.outcome,
                failure_reason=None,
                metadata={
                    "evidence_kind": "live",
                    "primary_capability": record.metadata.get(
                        "primary_capability",
                        "",
                    ),
                    "secondary_capabilities": list(
                        record.metadata.get("secondary_capabilities") or []
                    ),
                    "portable_seed": True,
                },
            )
            records.append(portable)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(
                    json.dumps(record.to_dict(), ensure_ascii=False) + "\n"
                )
        temporary.replace(destination)
        return len(records)


class BenchmarkExperienceImporter:
    """Importa experiencias desde carpetas de benchmarks ya corridos."""

    def __init__(self, results_root: Optional[Path] = None, tasks_root: Optional[Path] = None) -> None:
        self.results_root = (results_root or (Path.cwd() / "benchmarks" / "results")).resolve()
        self.tasks_root = (tasks_root or (Path.cwd() / "benchmarks" / "tasks")).resolve()

    def _task_index(self) -> Dict[str, Dict[str, Any]]:
        index: Dict[str, Dict[str, Any]] = {}
        for path in sorted(self.tasks_root.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(payload, list):
                continue
            for item in payload:
                if not isinstance(item, dict):
                    continue
                task_id = str(item.get("id") or item.get("task_id") or "")
                if task_id:
                    index[task_id] = item
        return index

    def _competitive_index(self, run_dir: Path) -> Dict[str, Dict[str, Any]]:
        index: Dict[str, Dict[str, Any]] = {}
        for path in run_dir.glob("*competitive.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(payload, list):
                continue
            for item in payload:
                if isinstance(item, dict):
                    index[str(item.get("task_id") or "")] = item
        return index

    def import_all(self, store: ExperienceStore) -> int:
        imported = 0
        task_index = self._task_index()
        existing_keys = store.existing_keys()
        to_append: List[RouterExperience] = []
        for run_dir in sorted(self.results_root.iterdir()):
            summary_path = run_dir / "summary.json"
            if not summary_path.exists():
                continue
            try:
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(summary, list):
                continue
            competitive_index = self._competitive_index(run_dir)
            for row in summary:
                if not isinstance(row, dict):
                    continue
                task_id = str(row.get("task_id") or "")
                if not task_id:
                    continue
                task_meta = task_index.get(task_id, {})
                comp = competitive_index.get(task_id, {})
                candidate_engine = str(
                    comp.get("fastest_sufficient")
                    or comp.get("quality_winner")
                    or row.get("engine")
                    or row.get("model")
                    or "unknown"
                )
                output_files = [Path(p) for p in row.get("output_files", []) if p]
                objective_pass = bool(row.get("returncode") == 0 and not row.get("timed_out") and output_files)
                judges = []
                if comp:
                    for candidate in comp.get("candidates", []):
                        if not isinstance(candidate, dict):
                            continue
                        judges.append(
                            {
                                "judge": comp.get("judge_model", "unknown"),
                                "score": float(candidate.get("score", 0)),
                                "passed": bool(candidate.get("passed", False)),
                                "comment": str(candidate.get("comment", "")),
                            }
                        )
                experience = RouterExperience(
                    experience_id=str(uuid4()),
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    catalog_version=2,
                    task_id=task_id,
                    task_shape=str(task_meta.get("block") or task_meta.get("category") or task_meta.get("level") or "unknown"),
                    tool_id=candidate_engine,
                    required_capabilities=list(task_meta.get("skills") or []),
                    cognitive_requirements=list(task_meta.get("cognitive_requirements") or task_meta.get("skills") or []),
                    elapsed_seconds=float(row.get("elapsed_seconds") or 0.0),
                    objective_checks={
                        "passed": objective_pass,
                        "checks": [
                            {
                                "name": "output_exists",
                                "passed": bool(output_files),
                                "detail": ", ".join(str(path) for path in output_files[:3]),
                            },
                            {
                                "name": "returncode_zero",
                                "passed": row.get("returncode") == 0,
                                "detail": str(row.get("returncode")),
                            },
                        ],
                    },
                    judge_scores=judges,
                    user_feedback=None,
                    outcome="sufficient" if objective_pass else ("timeout" if row.get("timed_out") else "insufficient"),
                    failure_reason=str(row.get("error_type") or row.get("stderr") or "")[:500] or None,
                    metadata={
                        "engine": row.get("engine"),
                        "model": row.get("model"),
                        "run_dir": str(run_dir),
                        "source_summary": str(summary_path),
                    },
                )
                key = (experience.task_id, experience.tool_id, str(summary_path))
                if key in existing_keys:
                    continue
                existing_keys.add(key)
                to_append.append(experience)
        imported += store.append_many(to_append)
        return imported
