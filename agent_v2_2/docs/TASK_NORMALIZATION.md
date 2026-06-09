# Task Normalization Model

Last updated: 2026-06-09

## Purpose

Agent 2.2 now normalizes every benchmark task into a stable operational
record. The goal is not to keep a larger pile of heterogeneous JSON files, but
to make every task expose the same evaluation contract:

- primary capability
- secondary capabilities
- compatible tools
- objective checks
- per-capability judge rubric

This is the bridge between the raw task batteries and the learned router
matrix.

## Source Inputs

Normalization reads the existing benchmark task JSON files and preserves the
native fields when present:

- `id`
- `title`
- `prompt` or `user_request`
- `skills`
- `required_files`
- `requires_network`
- `expected_operation`
- `route_hypothesis`
- `expected_outputs`
- `expected_keys`
- `rubric`
- `dimensions`

## Normalized Fields

Each normalized task contains:

- `primary_capability`: the main operational capability being tested.
- `secondary_capabilities`: additional operational capabilities touched by the
  task.
- `compatible_tools`: tools that satisfy the task contract.
- `objective_checks`: stable checks extracted from keys, artifacts and route
  hints.
- `judge_rubric`: the scoring rubric to use for the task.
- `task_shape`: the selected execution shape from the canonical contract.
- `contract`: the generated canonical request contract.

## Heuristic Rules

The normalizer uses the contract builder and the catalog selector, then applies
task-specific heuristics:

- file extensions become file-format requirements;
- skill labels map to the 17 operational capabilities;
- explicit `expected_operation` values can override the default capability;
- existing rubrics are preserved when available;
- otherwise a default rubric emphasizes correctness, traceability, format and
  actionability.

## CLI

Use:

```bash
python -m agent_v2_2.cli audit normalize
```

The command prints a markdown summary with:

- primary-capability counts
- compatible-tool counts
- tasks missing rubrics
- network-task counts
- a sample of normalized tasks

## Design Notes

- This model is intentionally deterministic.
- It keeps the old benchmark content intact.
- It is compatible with later judge scoring and learned capability matrices.
- It is meant to be expanded, not replaced, by later HITL telemetry.

