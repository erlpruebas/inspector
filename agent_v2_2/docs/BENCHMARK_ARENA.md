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

## Intended Judges

The arena is designed to accept judges such as:

- Gemini CLI or API judges for blind quality scoring.
- Codex CLI in arbitration mode for selected difficult cases.
- Deterministic local validators for objective checks and smoke tests.

## Current State

The arena is implemented as a reusable Python layer and covered by tests with a
simulated executor and judge. The next step is to plug in representative
real-tool runners and recorded blind judgments so the stored experience matrix
comes from live evidence instead of synthetic placeholders.

