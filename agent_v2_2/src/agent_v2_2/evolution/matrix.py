from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from math import sqrt
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .experience import ExperienceStore, RouterExperience


TOOL_ALIASES = {
    "groq_qwen_qwen3_32b": "router_groq_qwen32",
    "openrouter_qwen_qwen3_32b": "router_groq_qwen32",
    "openrouter_deepseek_deepseek_v3_2": "worker_openrouter_deepseek32",
    "groq_groq_compound_mini": "worker_groq_compound_mini",
    "groq_groq_compound": "worker_groq_compound",
    "codex_gpt_5_5": "premium_codex_55",
}

CAPABILITY_ALIASES = {
    "agenda": "cap_extract_short",
    "contacts": "cap_extract_short",
    "data_extraction": "cap_extract_long",
    "task_extraction": "cap_extract_long",
    "summarization": "cap_synth_long",
    "synthesis": "cap_synth_multi",
    "reporting": "cap_synth_multi",
    "multi_file_analysis": "cap_extract_cross",
    "comparison": "cap_compare",
    "crosscheck": "cap_compare",
    "calculation": "cap_calc_filter",
    "data_filtering": "cap_calc_filter",
    "structured_calculation": "cap_calc_filter",
    "email_drafting": "cap_transform_redact",
    "tone_control": "cap_transform_redact",
    "web_search": "cap_web_punctual",
    "company_research": "cap_investigate",
    "technical_report": "cap_exec_tech",
    "diagnosis": "cap_exec_tech",
    "code_execution": "cap_exec_tech",
    "write_file": "cap_create_modify",
}


@dataclass
class CapabilityCell:
    tool_id: str
    capability: str
    task_shape: str
    samples: int
    pass_rate: float
    mean_score: float
    mean_seconds: float
    stdev_seconds: float
    confidence: float
    judge_samples: int
    live_samples: int
    live_judge_samples: int
    live_pass_rate: float
    live_mean_score: float


@dataclass
class CapabilityMatrixReport:
    total_experiences: int
    total_cells: int
    cells: List[CapabilityCell] = field(default_factory=list)
    by_tool: Dict[str, int] = field(default_factory=dict)
    by_capability: Dict[str, int] = field(default_factory=dict)
    by_shape: Dict[str, int] = field(default_factory=dict)

    def to_markdown(self) -> str:
        lines = [f"# Learned capability matrix ({self.total_cells} cells)", ""]
        lines.append(f"- experiences: {self.total_experiences}")
        lines.append("")
        lines.append("## Tool coverage")
        for key, count in sorted(self.by_tool.items()):
            lines.append(f"- {key}: {count}")
        lines.append("")
        lines.append("## Capability coverage")
        for key, count in sorted(self.by_capability.items()):
            lines.append(f"- {key}: {count}")
        lines.append("")
        lines.append("## Task shapes")
        for key, count in sorted(self.by_shape.items()):
            lines.append(f"- {key}: {count}")
        lines.append("")
        lines.append("## Sample cells")
        for cell in sorted(self.cells, key=lambda item: (-item.samples, item.tool_id, item.capability, item.task_shape))[:20]:
            lines.append(
                f"- {cell.tool_id} | {cell.capability} | {cell.task_shape}: "
                f"samples={cell.samples}, pass={cell.pass_rate:.2f}, "
                f"score={cell.mean_score:.2f}, latency={cell.mean_seconds:.2f}s, "
                f"stdev={cell.stdev_seconds:.2f}s, confidence={cell.confidence:.2f}, "
                f"live={cell.live_samples}, live_judged={cell.live_judge_samples}, "
                f"live_pass={cell.live_pass_rate:.2f}, "
                f"live_score={cell.live_mean_score:.2f}"
            )
        return "\n".join(lines)


class CapabilityMatrixBuilder:
    """Aggregates router experiences into a learned capability matrix."""

    def __init__(self, experience_store: Optional[ExperienceStore] = None) -> None:
        self.experience_store = experience_store or ExperienceStore()

    def build(self, experiences: Optional[Iterable[RouterExperience]] = None) -> CapabilityMatrixReport:
        records = list(experiences) if experiences is not None else self.experience_store.load()
        cells = self._aggregate_cells(records)
        by_tool = Counter(cell.tool_id for cell in cells)
        by_capability = Counter(cell.capability for cell in cells)
        by_shape = Counter(cell.task_shape for cell in cells)
        return CapabilityMatrixReport(
            total_experiences=len(records),
            total_cells=len(cells),
            cells=cells,
            by_tool=dict(by_tool),
            by_capability=dict(by_capability),
            by_shape=dict(by_shape),
        )

    def _aggregate_cells(self, experiences: List[RouterExperience]) -> List[CapabilityCell]:
        groups: Dict[Tuple[str, str, str], List[RouterExperience]] = defaultdict(list)
        for experience in experiences:
            if bool(experience.metadata.get("evidence_invalidated")):
                continue
            if str(experience.metadata.get("evidence_kind", "historical")) in {
                "simulated",
                "unavailable",
                "queued",
            }:
                continue
            tool_id = TOOL_ALIASES.get(experience.tool_id, experience.tool_id)
            capabilities = self._capabilities_for_experience(experience)
            for capability in capabilities:
                groups[(tool_id, capability, experience.task_shape)].append(experience)

        cells: List[CapabilityCell] = []
        for (tool_id, capability, task_shape), group in groups.items():
            scores = [
                self._score_from_experience(experience, capability)
                for experience in group
            ]
            seconds = [experience.elapsed_seconds for experience in group]
            pass_rate = sum(1 for experience in group if self._passed(experience)) / len(group)
            score_values = [score for score in scores if score is not None]
            judge_samples = len(score_values)
            live_samples = sum(
                1
                for experience in group
                if str(experience.metadata.get("evidence_kind", "historical"))
                == "live"
            )
            live_group = [
                experience
                for experience in group
                if str(experience.metadata.get("evidence_kind", "historical"))
                == "live"
            ]
            live_scores = [
                self._score_from_experience(experience, capability)
                for experience in live_group
            ]
            live_score_values = [
                score for score in live_scores if score is not None
            ]
            live_judge_samples = len(live_score_values)
            live_pass_rate = (
                sum(1 for experience in live_group if self._passed(experience))
                / len(live_group)
                if live_group
                else 0.0
            )
            live_mean_score = (
                mean(live_score_values) if live_score_values else 0.0
            )
            mean_score = mean(score_values) if score_values else 0.0
            mean_seconds = mean(seconds) if seconds else 0.0
            stdev_seconds = self._stdev(seconds)
            evidence_factor = min(1.0, live_samples / 10.0)
            judge_factor = min(1.0, judge_samples / 5.0)
            confidence = evidence_factor * (0.5 + 0.5 * judge_factor)
            cells.append(
                CapabilityCell(
                    tool_id=tool_id,
                    capability=capability,
                    task_shape=task_shape,
                    samples=len(group),
                    pass_rate=pass_rate,
                    mean_score=mean_score,
                    mean_seconds=mean_seconds,
                    stdev_seconds=stdev_seconds,
                    confidence=confidence,
                    judge_samples=judge_samples,
                    live_samples=live_samples,
                    live_judge_samples=live_judge_samples,
                    live_pass_rate=live_pass_rate,
                    live_mean_score=live_mean_score,
                )
            )
        return cells

    def _capabilities_for_experience(self, experience: RouterExperience) -> List[str]:
        capabilities: List[str] = []
        metadata_primary = str(experience.metadata.get("primary_capability") or "").strip()
        if metadata_primary:
            capabilities.append(CAPABILITY_ALIASES.get(metadata_primary, metadata_primary))
        for item in experience.required_capabilities:
            if item:
                value = str(item)
                capabilities.append(CAPABILITY_ALIASES.get(value, value))
        if not capabilities and experience.objective_checks.get("capability"):
            capabilities.append(str(experience.objective_checks["capability"]))
        return self._unique(capabilities)

    def _score_from_experience(
        self,
        experience: RouterExperience,
        capability: str,
    ) -> Optional[float]:
        if not experience.judge_scores:
            return None
        scores = []
        for item in experience.judge_scores:
            if isinstance(item, dict):
                capability_scores = item.get("capability_scores")
                if isinstance(capability_scores, dict):
                    if not capability_scores:
                        continue
                    value = capability_scores.get(capability)
                    if value is None:
                        for raw_name, raw_score in capability_scores.items():
                            if CAPABILITY_ALIASES.get(str(raw_name), str(raw_name)) == capability:
                                value = raw_score
                                break
                    primary = CAPABILITY_ALIASES.get(
                        str(experience.metadata.get("primary_capability") or ""),
                        str(experience.metadata.get("primary_capability") or ""),
                    )
                    if value is None and capability == primary:
                        value = item.get("score")
                else:
                    primary = CAPABILITY_ALIASES.get(
                        str(experience.metadata.get("primary_capability") or ""),
                        str(experience.metadata.get("primary_capability") or ""),
                    )
                    value = item.get("score") if capability == primary else None
            else:
                value = getattr(item, "score", None)
            if isinstance(value, (int, float)):
                scores.append(float(value))
        if not scores:
            return None
        return mean(scores)

    def _passed(self, experience: RouterExperience) -> bool:
        if any(
            self._judgement_is_valid(item)
            for item in experience.judge_scores
            if isinstance(item, dict)
        ):
            return experience.outcome == "sufficient"
        passed = experience.objective_checks.get("passed")
        return bool(passed) or experience.outcome == "sufficient"

    def _judgement_is_valid(self, judgement: dict) -> bool:
        capability_scores = judgement.get("capability_scores")
        if isinstance(capability_scores, dict) and capability_scores:
            return True
        return (
            isinstance(judgement.get("score"), (int, float))
            and (
                str(judgement.get("judge") or "").casefold() != "unknown"
                or bool(str(judgement.get("comment") or "").strip())
            )
        )

    def _stdev(self, values: List[float]) -> float:
        if len(values) < 2:
            return 0.0
        avg = mean(values)
        variance = sum((value - avg) ** 2 for value in values) / (len(values) - 1)
        return sqrt(variance)

    def _unique(self, values: List[str]) -> List[str]:
        seen: set[str] = set()
        result: List[str] = []
        for value in values:
            key = value.casefold()
            if key in seen:
                continue
            seen.add(key)
            result.append(value)
        return result
