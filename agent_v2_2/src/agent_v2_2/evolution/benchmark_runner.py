from __future__ import annotations

import logging
import json
import os
import shutil
import tempfile
import time
from dataclasses import dataclass
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

    def run_task(self, task: NormalizedTask, tool_id: str, contract: RequestContract) -> OrchestratorResult:
        tool = self.catalog.get_tool(tool_id)
        if tool is None:
            return self._fallback_result(task, tool_id, contract)

        spec = self._tool_spec(tool_id, tool.provider, tool.model)
        if spec is None:
            return self._fallback_result(task, tool_id, contract)

        from benchmarks.engines.engine_factory import create_engine

        workdir = self._prepare_workdir(task)
        expected_outputs = list(task.expected_outputs) or ["resultado.md"]
        try:
            engine = create_engine(spec)
            result = engine.run(task.task_id, task.prompt, workdir, expected_outputs)
            return self._convert_result(tool_id, contract, result.output_files, result.elapsed_seconds, result.returncode, result.stdout, result.stderr, result.timed_out, result.model, workdir, engine.name)
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
        if self.judge_model:
            try:
                from benchmarks.engines.engine_factory import create_engine

                judge_engine = create_engine(f"gemini={self.judge_model}")

                def external_judge(task: NormalizedTask, result: OrchestratorResult) -> Dict[str, object]:
                    prompt = self._judge_prompt(task, result)
                    workdir = Path(tempfile.mkdtemp(prefix=f"judge-{task.task_id}-", dir=self.workspace_root))
                    expected_outputs = ["judge.json"]
                    judge_result = judge_engine.run(f"judge-{task.task_id}", prompt, workdir, expected_outputs)
                    payload = self._parse_judge_payload(workdir, judge_result.stdout)
                    if payload:
                        return payload
                    return {
                        "judge": self.judge_model,
                        "score": 0.0 if not judge_result.ok else 5.0,
                        "passed": bool(judge_result.ok),
                        "comment": judge_result.stderr or "blank judge output",
                    }

                return external_judge
            except Exception as exc:
                logger.warning("Falling back to local judge: %s", exc)

        def judge(task: NormalizedTask, result: OrchestratorResult) -> Dict[str, object]:
            score = 10.0 if result.ok and result.output.strip() else 0.0
            passed = bool(result.ok and result.output.strip())
            if task.objective_checks:
                output = result.output.casefold()
                contains_checks = [item for item in task.objective_checks if item.startswith("contains:")]
                if contains_checks:
                    hits = sum(1 for item in contains_checks if item.split(":", 1)[1].casefold() in output)
                    score = max(score, 4.0 + (hits / max(1, len(contains_checks))) * 6.0)
                    passed = passed and hits == len(contains_checks)
            return {
                "judge": "gemini-blind-local",
                "score": round(score, 2),
                "passed": passed,
                "comment": "objective checks only",
                }

        return judge

    def _judge_prompt(self, task: NormalizedTask, result: OrchestratorResult) -> str:
        objective = json.dumps(task.objective_checks, ensure_ascii=False, indent=2)
        return f"""
You are a blind benchmark judge for Inspector Agent 2.2.
Do not mention tool identities in your rationale unless the output already exposes them.
Score only from the task contract and the result text.

Task title:
{task.title}

Primary capability:
{task.primary_capability}

Objective checks:
{objective}

Tool output:
{result.output}

Error:
{result.error or ""}

Return a JSON object with these keys:
- judge: string
- score: number from 0 to 10
- passed: boolean
- comment: short string
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
                return {
                    "judge": str(payload.get("judge") or "unknown"),
                    "score": float(payload.get("score") or 0.0),
                    "passed": bool(payload.get("passed", False)),
                    "comment": str(payload.get("comment") or ""),
                }
        try:
            payload = json.loads(stdout.strip())
        except Exception:
            return {}
        if not isinstance(payload, dict):
            return {}
        return {
            "judge": str(payload.get("judge") or "unknown"),
            "score": float(payload.get("score") or 0.0),
            "passed": bool(payload.get("passed", False)),
            "comment": str(payload.get("comment") or ""),
        }

    def run_arena(self, path: Path, *, limit: Optional[int] = None):
        arena = BenchmarkArena()
        return arena.run_path(
            path,
            executor=self.build_executor(),
            judge=self.build_judge(),
            limit=limit,
        )

    def _tool_spec(self, tool_id: str, provider: str, model: str) -> Optional[str]:
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
            return f"gemini={model or 'gemini-2.5-flash-lite'}"
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

    def _fallback_result(
        self,
        task: NormalizedTask,
        tool_id: str,
        contract: RequestContract,
    ) -> OrchestratorResult:
        del contract
        workdir = self._prepare_workdir(task)
        output = workdir / (task.expected_outputs[0] if task.expected_outputs else "resultado.md")
        content = (
            f"# {task.title}\n\n"
            f"Primary capability: {task.primary_capability}\n\n"
            f"Tool: {tool_id}\n"
        )
        output.write_text(content, encoding="utf-8")
        return OrchestratorResult(
            ok=True,
            tool_id=tool_id,
            tier="general",
            output=content,
            elapsed_seconds=0.05,
            privacy_mode="clear",
            workdir=workdir,
            timings=OperationTimings(execution_seconds=0.05, total_seconds=0.05),
            metadata={"mode": "fallback"},
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
    ) -> OrchestratorResult:
        del contract, output_files
        ok = returncode == 0 and not timed_out
        output = stdout.strip()
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
            metadata={"engine": engine_name, "model": model},
        )
