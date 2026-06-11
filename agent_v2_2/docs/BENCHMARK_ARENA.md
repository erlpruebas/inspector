# Benchmark Arena

Last updated: 2026-06-09

## Purpose

The benchmark arena is the execution layer that sits on top of the normalized
task model. It turns a normalized benchmark task into a concrete run against a
compatible tool, measures latency, evaluates objective checks and stores the
result as a router experience.

The arena is the bridge between:

- task normalization
- tool selection
- objective verification
- blind judging
- learned capability statistics

## Core Objects

- `NormalizedTask`: the canonical task record produced by the task normalizer.
- `ArenaExecutor`: a callable that runs a task against a selected tool.
- `ArenaJudge`: a callable that scores the run without exposing tool identity
  unnecessarily.
- `ArenaRunResult`: the per-task execution record.
- `ArenaReport`: the summary report for a batch of runs.

## Execution Flow

1. Normalize the benchmark battery.
2. Select a compatible tool for each task.
3. Execute the task with the chosen tool.
4. Check objective evidence such as expected keys or artifacts.
5. Judge the result with a blind scorer.
6. Persist the run as a router experience.
7. Summarize tool counts, shape counts, latency and judge coverage.

## Runner

`agent_v2_2.evolution.BenchmarkRunner` provides the default bridge from a
normalized task to a runnable engine. It can:

- copy benchmark assets into a temp workdir;
- map normalized tools to benchmark engine specs when available;
- fall back to a local simulated result when a real engine is not available;
- emit a blind local judge result for the first pass;
- execute a whole arena through `audit arena --limit N`.

For focused evidence collection, the CLI can also target a specific battery or
task file:

```bash
python -m agent_v2_2.cli audit arena --path benchmarks/tasks/reasoning_latency_tasks_20260607.json --limit 1
```

If `BENCH_GEMINI_JUDGE_MODEL` is set, the runner can also request a blind
Gemini-based judge through the benchmark engine wrapper and persist that
judgment alongside the run.

## Intended Judges

The arena is designed to accept judges such as:

- Gemini CLI or API judges for blind quality scoring.
- Codex CLI in arbitration mode for selected difficult cases.
- Deterministic local validators for objective checks and smoke tests.

## Current State

The arena is implemented as a reusable Python layer and covered by tests with a
simulated executor and judge. The next step is to keep expanding representative
real-tool slices and recorded blind judgments so the stored experience matrix
comes from live evidence instead of synthetic placeholders.
