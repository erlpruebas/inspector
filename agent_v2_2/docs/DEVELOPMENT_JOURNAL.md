# Agent 2.2 Development Journal

This is the operational checkpoint for autonomous development. Read
`AUTONOMOUS_ROADMAP.md` first, then resume from the latest entry below.

## 2026-06-09: Pre-Autonomous Technical Review

### Current branch

- `gemini/agent-v2-2`
- Synchronized with `origin/gemini/agent-v2-2` at review time.

### Verified state

- Agent 2.2 unit/smoke suite: `12 passed`.
- Audited task records: `356`.
- Imported historical experiences: `1769`.
- Experiences containing judge data: `42`.
- Reported tool IDs in historical data: `72`.
- Reported task shapes: `21`.
- File-format buckets missing from the current audit: `0`.

### Important qualification

The current `ready=True` result is not sufficient evidence for real HITL:

- `agent-v2-2 start` is still a smoke message, not an operational loop.
- The routing selector uses three simple keyword branches.
- The Agent 2.2 capability catalog has no normalized tools.
- Historical completion often means that a process returned successfully and
  created output, not that every capability was scored correctly.
- The parity matrix marks modules as complete without requiring end-to-end
  evidence.

### Current roadmap position

- Step 0: `IN_PROGRESS`.
- First task: replace the simulated monthly token budget in
  `agent_v2_2/src/agent_v2_2/scheduling/codex_quota.py` with a real, tested
  five-hour and weekly Codex rate-limit monitor adapted from
  `orchestrator_v2_1/codex_rate_limits.py`.

### Resume procedure

1. Read `AUTONOMOUS_ROADMAP.md`.
2. Inspect the latest Git status without modifying unrelated files.
3. Implement Step 0 only inside Agent 2.2 and its tests.
4. Run `python -m pytest agent_v2_2/tests -q`.
5. Update the roadmap and this journal only after the exit criteria pass.

## 2026-06-09: Step 0 Complete

### Implemented

- Replaced the simulated monthly token counter with the real Codex app-server
  rate-limit reader.
- Persisted five-hour and weekly percentages and reset timestamps.
- Added stale-snapshot protection and a configurable 25% five-hour reserve.
- Added a quota-aware scheduler that pauses Codex tasks, continues non-Codex
  tasks and resumes paused Codex tasks after quota refresh.
- Added persistent autonomous checkpoints.
- Fixed queue serialization of Pydantic datetime values discovered by the new
  scheduler tests.

### Verification

- Full Agent 2.2 suite: `16 passed`.
- Live quota read succeeded.
- Snapshot observed during verification: five-hour window above reserve;
  weekly remaining `7%`, reset on 2026-06-11.

### Current roadmap position

- Step 0: `COMPLETE`.
- Step 1: `IN_PROGRESS`.

### Next action

Define the canonical, versioned request/capability contract. Use
`orchestrator_v2_1/capability_catalog.json` and the proven v2.1 preparation and
routing behavior as the functional source of truth, while keeping Agent 2.2
self-contained.
