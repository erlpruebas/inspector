from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ..config import load_config
from .experience import ExperienceStore
from .normalization import NormalizedTask, TaskNormalizer


@dataclass
class HITLTrial:
    trial_id: str
    chat_id: str
    task_id: str
    prompt: str
    experience_id: str = ""
    tool_id: str = ""
    started_at: str = ""
    completed_at: str = ""
    elapsed_seconds: float = 0.0
    usefulness: str = ""
    friction: str = ""
    correction: str = ""


class HITLController:
    """Persistent synthetic battery and human-feedback controller."""

    def __init__(
        self,
        *,
        tasks_path: Optional[Path] = None,
        state_path: Optional[Path] = None,
        trials_path: Optional[Path] = None,
        experience_store: Optional[ExperienceStore] = None,
    ) -> None:
        config = load_config()
        root = config.workspace_root / "evolution" / "hitl"
        root.mkdir(parents=True, exist_ok=True)
        self.tasks_path = tasks_path or (
            Path.cwd()
            / "benchmarks"
            / "tasks"
            / "telegram_hitl_business_battery_20260607.json"
        )
        self.state_path = state_path or (root / "state.json")
        self.trials_path = trials_path or (root / "trials.jsonl")
        self.experience_store = experience_store or ExperienceStore()
        self.normalizer = TaskNormalizer()

    def start(self, chat_id: int | str) -> NormalizedTask:
        state = self._load_state()
        state[str(chat_id)] = {"cursor": 0, "last_trial_id": ""}
        self._save_state(state)
        return self._tasks()[0]

    def current(self, chat_id: int | str) -> NormalizedTask:
        tasks = self._tasks()
        cursor = int(self._chat_state(chat_id).get("cursor", 0)) % len(tasks)
        return tasks[cursor]

    def next(self, chat_id: int | str) -> NormalizedTask:
        tasks = self._tasks()
        state = self._load_state()
        chat = dict(state.get(str(chat_id)) or {})
        chat["cursor"] = (int(chat.get("cursor", 0)) + 1) % len(tasks)
        chat["last_trial_id"] = ""
        state[str(chat_id)] = chat
        self._save_state(state)
        return tasks[int(chat["cursor"])]

    def repeat(self, chat_id: int | str) -> NormalizedTask:
        return self.current(chat_id)

    def begin_trial(self, chat_id: int | str, task: NormalizedTask) -> HITLTrial:
        now = datetime.now(timezone.utc)
        trial = HITLTrial(
            trial_id=f"{chat_id}-{task.task_id}-{int(now.timestamp() * 1000)}",
            chat_id=str(chat_id),
            task_id=task.task_id,
            prompt=task.prompt,
            started_at=now.isoformat(),
        )
        self._append_trial(trial)
        state = self._load_state()
        chat = dict(state.get(str(chat_id)) or {})
        chat["last_trial_id"] = trial.trial_id
        state[str(chat_id)] = chat
        self._save_state(state)
        return trial

    def link_result(
        self,
        trial_id: str,
        *,
        experience_id: str,
        tool_id: str,
        elapsed_seconds: float,
    ) -> None:
        self._update_trial(
            trial_id,
            experience_id=experience_id,
            tool_id=tool_id,
            elapsed_seconds=elapsed_seconds,
            completed_at=datetime.now(timezone.utc).isoformat(),
        )

    def record_feedback(
        self,
        chat_id: int | str,
        usefulness: str,
        *,
        friction: str = "",
        correction: str = "",
    ) -> bool:
        trial_id = str(self._chat_state(chat_id).get("last_trial_id") or "")
        if not trial_id:
            return False
        trial = self._find_trial(trial_id)
        if trial is None:
            return False
        self._update_trial(
            trial_id,
            usefulness=usefulness,
            friction=friction,
            correction=correction,
        )
        if trial.experience_id:
            self.experience_store.record_feedback(
                trial.experience_id,
                usefulness,
                metadata={
                    "hitl_trial_id": trial_id,
                    "hitl_friction": friction,
                    "hitl_correction": correction,
                },
            )
        return True

    def record_annotation(
        self,
        chat_id: int | str,
        *,
        friction: str = "",
        correction: str = "",
    ) -> bool:
        trial_id = str(self._chat_state(chat_id).get("last_trial_id") or "")
        if not trial_id:
            return False
        trial = self._find_trial(trial_id)
        if trial is None:
            return False
        updates = {}
        if friction.strip():
            updates["friction"] = friction.strip()
        if correction.strip():
            updates["correction"] = correction.strip()
        if not updates:
            return False
        self._update_trial(trial_id, **updates)
        if trial.experience_id:
            self.experience_store.record_feedback(
                trial.experience_id,
                trial.usefulness or "unrated",
                metadata={
                    "hitl_trial_id": trial_id,
                    "hitl_friction": updates.get("friction", trial.friction),
                    "hitl_correction": updates.get(
                        "correction",
                        trial.correction,
                    ),
                },
            )
        return True

    def report(self) -> dict[str, float]:
        trials = self._load_trials()
        rated = [trial for trial in trials if trial.usefulness]
        useful = sum(trial.usefulness == "yes" for trial in rated)
        partial = sum(trial.usefulness == "partial" for trial in rated)
        rejected = sum(trial.usefulness == "no" for trial in rated)
        return {
            "trials": float(len(trials)),
            "rated": float(len(rated)),
            "useful": float(useful),
            "partial": float(partial),
            "rejected": float(rejected),
            "average_seconds": (
                sum(trial.elapsed_seconds for trial in trials) / len(trials)
                if trials
                else 0.0
            ),
        }

    def _tasks(self) -> list[NormalizedTask]:
        report = self.normalizer.normalize_path(self.tasks_path)
        if not report.records:
            raise RuntimeError(f"HITL battery is empty: {self.tasks_path}")
        return report.records

    def _chat_state(self, chat_id: int | str) -> dict:
        return dict(self._load_state().get(str(chat_id)) or {})

    def _load_state(self) -> dict:
        if not self.state_path.exists():
            return {}
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return payload if isinstance(payload, dict) else {}

    def _save_state(self, payload: dict) -> None:
        self.state_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _append_trial(self, trial: HITLTrial) -> None:
        with self.trials_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(trial), ensure_ascii=False) + "\n")

    def _load_trials(self) -> list[HITLTrial]:
        if not self.trials_path.exists():
            return []
        trials: list[HITLTrial] = []
        for line in self.trials_path.read_text(encoding="utf-8").splitlines():
            try:
                payload = json.loads(line)
                trials.append(HITLTrial(**payload))
            except Exception:
                continue
        return trials

    def _find_trial(self, trial_id: str) -> HITLTrial | None:
        return next(
            (trial for trial in self._load_trials() if trial.trial_id == trial_id),
            None,
        )

    def _update_trial(self, trial_id: str, **updates) -> None:
        trials = self._load_trials()
        for trial in trials:
            if trial.trial_id != trial_id:
                continue
            for key, value in updates.items():
                setattr(trial, key, value)
            break
        temporary = self.trials_path.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            for trial in trials:
                handle.write(json.dumps(asdict(trial), ensure_ascii=False) + "\n")
        temporary.replace(self.trials_path)
