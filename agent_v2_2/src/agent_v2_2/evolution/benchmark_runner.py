from __future__ import annotations

import logging
import json
import os
import shutil
import tempfile
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Optional

from ..capabilities.catalog import create_default_catalog
from ..models import OperationTimings, OrchestratorResult, RouteDecision
from ..routing.contract import RequestContract
from .arena import ArenaJudge, ArenaExecutor, BenchmarkArena
from .normalization import NormalizedTask


logger = logging.getLogger("agent_v2_2.evolution.benchmark_runner")


@dataclass
class BenchmarkRunSummary:
    task_id: str
    tool_id: str
    engine: str
    output_path: str
    elapsed_seconds: float
    returncode: int
    ok: bool


class BenchmarkRunner:
    """Runs normalized tasks using benchmark engines when available."""

    def __init__(self, *, workspace_root: Optional[Path] = None) -> None:
        self.workspace_root = (workspace_root or (Path.cwd() / "runtime" / "arena")).resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.catalog = create_default_catalog()
        self.judge_model = os.getenv("BENCH_GEMINI_JUDGE_MODEL", "").strip()
        self.judge_engine_spec = os.getenv("BENCH_JUDGE_ENGINE", "").strip()

    def run_task(self, task: NormalizedTask, tool_id: str, contract: RequestContract) -> OrchestratorResult:
        tool = self.catalog.get_tool(tool_id)
        if tool is None:
            return self._unavailable_result(task, tool_id, "Tool is not present in the catalog")

        spec = self._tool_spec(
            tool_id,
            tool.provider,
            tool.model,
            tool.invocation_type,
        )
        if spec is None:
            return self._unavailable_result(task, tool_id, "No live benchmark engine adapter")

        from benchmarks.engines.engine_factory import create_engine

        workdir = self._prepare_workdir(task)
        expected_outputs = list(task.expected_outputs) or ["resultado.md"]
        try:
            engine = create_engine(spec)
            result = engine.run(task.task_id, task.prompt, workdir, expected_outputs)
            return self._convert_result(
                tool_id,
                contract,
                result.output_files,
                result.elapsed_seconds,
                result.returncode,
                result.stdout,
                result.stderr,
                result.timed_out,
                result.model,
                workdir,
                engine.name,
                result.error_type,
            )
        except Exception as exc:
            return OrchestratorResult(
                ok=False,
                tool_id=tool_id,
                tier=tool.cognitive_max,
                output="",
                error=str(exc),
                elapsed_seconds=0.0,
                privacy_mode="clear",
                workdir=workdir,
            )

    def build_executor(self) -> ArenaExecutor:
        def executor(task: NormalizedTask, tool_id: str, contract: RequestContract) -> OrchestratorResult:
            return self.run_task(task, tool_id, contract)

        return executor

    def build_judge(self) -> ArenaJudge:
        if self.judge_engine_spec or self.judge_model:
            try:
                from benchmarks.engines.engine_factory import create_engine

                judge_spec = self.judge_engine_spec or f"gemini_api={self.judge_model}"
                judge_engine = create_engine(judge_spec)

                def external_judge(task: NormalizedTask, result: OrchestratorResult) -> Dict[str, object]:
                    prompt = self._judge_prompt(task, result)
                    for attempt in range(2):
                        workdir = Path(
                            tempfile.mkdtemp(
                                prefix=f"judge-{task.task_id}-",
                                dir=self.workspace_root,
                            )
                        )
                        expected_outputs = ["judge.json"]
                        attempt_prompt = prompt
                        if attempt:
                            attempt_prompt += (
                                "\n\nYour previous response was invalid. Return a complete "
                                "JSON object, never `{}` and never omit score, passed, "
                                "comment or capability_scores."
                            )
                        judge_result = judge_engine.run(
                            f"judge-{task.task_id}-{attempt + 1}",
                            attempt_prompt,
                            workdir,
                            expected_outputs,
                        )
                        payload = self._parse_judge_payload(
                            workdir,
                            judge_result.stdout,
                        )
                        if payload:
                            return payload
                    logger.warning(
                        "Blind judge returned no valid payload for task %s",
                        task.task_id,
                    )
                    return {}

                return external_judge
            except Exception as exc:
                logger.warning("Falling back to local judge: %s", exc)

        def judge(task: NormalizedTask, result: OrchestratorResult) -> Dict[str, object]:
            del task, result
            logger.warning(
                "Arena run has no external blind judge configured; "
                "the result will not count as judged evidence."
            )
            return {}

        return judge

    def _judge_prompt(self, task: NormalizedTask, result: OrchestratorResult) -> str:
        objective = json.dumps(task.objective_checks, ensure_ascii=False, indent=2)
        return f"""
You are a blind benchmark judge for Inspector Agent 2.2.
Do not mention tool identities in your rationale unless the output already exposes them.
Score only from the task contract and the result text.
The current date is {date.today().isoformat()}. Treat dates relative to that
date and do not classify a 2026 date as future merely because of model
training data.

Task title:
{task.title}

Primary capability:
{task.primary_capability}

Objective checks:
{objective}

Tool output:
{result.output}

Generated artifacts:
{json.dumps(result.metadata.get("output_files", []), ensure_ascii=False)}

Error:
{result.error or ""}

Return a JSON object with these keys:
- judge: string
- score: number from 0 to 10
- passed: boolean
- comment: short string
- capability_scores: object mapping every listed capability to a 0-10 score
""".strip()

    def _parse_judge_payload(self, workdir: Path, stdout: str) -> Dict[str, object]:
        candidates = [workdir / "judge.json"]
        for candidate in candidates:
            if not candidate.exists():
                continue
            try:
                payload = json.loads(candidate.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(payload, dict):
                normalized = self._normalize_judge_payload(payload)
                if normalized:
                    return normalized
        try:
            payload = json.loads(stdout.strip())
        except Exception:
            return {}
        return self._normalize_judge_payload(payload)

    def _normalize_judge_payload(self, payload: object) -> Dict[str, object]:
        if not isinstance(payload, dict):
            return {}
        if (
            not isinstance(payload.get("score"), (int, float))
            or not isinstance(payload.get("passed"), bool)
            or not isinstance(payload.get("capability_scores"), dict)
        ):
            return {}
        return {
            "judge": str(payload.get("judge") or "unknown"),
            "score": float(payload["score"]),
            "passed": bool(payload["passed"]),
            "comment": str(payload.get("comment") or ""),
            "capability_scores": dict(payload["capability_scores"]),
        }

    def run_arena(
        self,
        path: Path,
        *,
        limit: Optional[int] = None,
        tool_ids: Optional[list[str]] = None,
        all_compatible_tools: bool = False,
        task_ids: Optional[list[str]] = None,
    ):
        arena = BenchmarkArena()
        return arena.run_path(
            path,
            executor=self.build_executor(),
            judge=self.build_judge(),
            limit=limit,
            tool_ids=tool_ids,
            all_compatible_tools=all_compatible_tools,
            task_ids=task_ids,
        )

    def _tool_spec(
        self,
        tool_id: str,
        provider: str,
        model: str,
        invocation_type: str = "api",
    ) -> Optional[str]:
        normalized_tool = tool_id.casefold()
        provider = provider.casefold()
        model = model.strip()
        if normalized_tool == "local_direct":
            return None
        if provider == "openai" and "gpt-5.5" in model:
            return "codex=gpt-5.5"
        if provider == "google":
            if "grounded" in normalized_tool:
                return f"gemini_grounded={model or 'gemini-2.5-flash'}"
            if invocation_type == "cli":
                return f"gemini={model or 'gemini-2.5-flash-lite'}"
            return f"gemini_api={model or 'gemini-2.5-flash-lite'}"
        if provider == "groq":
            if "compound-mini" in model:
                return f"groq={model}"
            if "compound" in model:
                return f"groq={model}"
            return f"groq={model or 'qwen/qwen3-32b'}"
        if provider == "openrouter":
            return f"openrouter={model}"
        if provider == "opencode":
            return f"opencode={model}"
        if provider == "local":
            return "command"
        return None

    def _prepare_workdir(self, task: NormalizedTask) -> Path:
        workdir = Path(tempfile.mkdtemp(prefix=f"{task.task_id}-", dir=self.workspace_root))
        for relative in task.required_files:
            source = self._resolve_source(relative)
            if source is None:
                continue
            destination = workdir / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        return workdir

    def _resolve_source(self, relative: str) -> Optional[Path]:
        candidates = [
            Path.cwd() / relative,
            Path.cwd() / "benchmarks" / "assets" / relative,
            Path.cwd() / "benchmarks" / "tasks" / relative,
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def _unavailable_result(
        self,
        task: NormalizedTask,
        tool_id: str,
        reason: str,
    ) -> OrchestratorResult:
        workdir = self._prepare_workdir(task)
        return OrchestratorResult(
            ok=False,
            tool_id=tool_id,
            tier="general",
            output="",
            error=reason,
            elapsed_seconds=0.0,
            privacy_mode="clear",
            workdir=workdir,
            timings=OperationTimings(),
            metadata={"evidence_kind": "unavailable"},
        )

    def _convert_result(
        self,
        tool_id: str,
        contract: RequestContract,
        output_files: list[str],
        elapsed_seconds: float,
        returncode: int,
        stdout: str,
        stderr: str,
        timed_out: bool,
        model: str,
        workdir: Path,
        engine_name: str,
        error_type: str,
    ) -> OrchestratorResult:
        del contract
        ok = returncode == 0 and not timed_out
        output = self._read_output_files(output_files) or stdout.strip()
        error = None if ok else (stderr.strip() or f"Code {returncode}")
        return OrchestratorResult(
            ok=ok,
            tool_id=tool_id,
            tier="general",
            output=output,
            error=error,
            elapsed_seconds=elapsed_seconds,
            privacy_mode="clear",
            workdir=workdir,
            timings=OperationTimings(execution_seconds=elapsed_seconds, total_seconds=elapsed_seconds),
            metadata={
                "engine": engine_name,
                "model": model,
                "evidence_kind": (
                    "unavailable" if error_type == "usage_limit" else "live"
                ),
                "error_type": error_type,
                "output_files": list(output_files),
            },
        )

    def _read_output_files(self, output_files: list[str]) -> str:
        chunks: list[str] = []
        for raw_path in output_files:
            path = Path(raw_path)
            if not path.exists() or not path.is_file():
                continue
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
        return "\n\n".join(chunks).strip()
