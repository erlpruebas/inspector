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

## 2026-06-09: Step 1 Complete

### Implemented

- Added versioned `RequestContract` models.
- Separated preparation actions from execution requirements.
- Defined operational file formats and independent read, extract, create,
  modify, preserve and verify operations.
- Defined cognitive level, cognitive requirements, instrumental capabilities
  and result guarantees.
- Added cross-field validation for web freshness, research, ambiguity and
  format preservation.
- Documented the selection boundary: the router describes requirements and
  deterministic code selects the tool.

### Verification

- Full Agent 2.2 suite: `18 passed`.
- Covered a chained memory-to-web request.
- Covered XLSX modification with format preservation and artifact verification.

### Current roadmap position

- Step 1: `COMPLETE`.
- Step 2: `IN_PROGRESS`.

### Next action

Normalize every real tool from the v2.1 catalog into stable Agent 2.2 tool
records with invocation type, eligibility, access flags, file operations,
observed latency and evidence provenance.

## 2026-06-09: Step 2 Complete

### Implemented

- Registered all 13 routes from the v2.1 source catalog.
- Assigned stable IDs, display names, provider, model and invocation type.
- Preserved active, sampled, demonstrated, experimental and deferred states.
- Preserved selection eligibility separately from registration.
- Normalized instrumental capabilities and derived direct file operations by
  format.
- Preserved historical latency and global benchmark observations as evidence.
- Added an empty per-capability score map for the later normalized arena.

### Verification

- 13 unique tools registered.
- 10 currently selection-eligible.
- Gemini Pro and Codex CLI expose their demonstrated file operations.
- Full Agent 2.2 suite: `18 passed`.

### Current roadmap position

- Step 2: `COMPLETE`.
- Step 3: `IN_PROGRESS`.

### Next action

Build one real vertical application flow around the proven old behavior:
Telegram input, attachment/voice preparation, relevant memory retrieval,
contract generation, deterministic selection, execution, verification,
response delivery and experience persistence.

## 2026-06-09: Step 3 Vertical Core

### Implemented

- Replaced keyword routing with hard compatibility filtering over the canonical
  contract and normalized tool catalog.
- Selection now filters mandatory access, file operations and cognitive level
  before considering latency.
- Added `AgentApplication` as the shared vertical request flow.
- The flow records the user message, retrieves only relevant memory, selects a
  compatible tool, executes, records timings, performs a basic objective check,
  stores a router experience and records the assistant result.
- Added a voice entry point that transcribes before entering the same flow.

### Verification

- XLSX requirements select Gemini Pro before Codex because both are compatible
  and Gemini has lower demonstrated median latency.
- A complete local request records memory, result, timings and one experience.
- Full Agent 2.2 suite: `20 passed`.

## 2026-06-09: Step 3 Complete

### Implemented

- Added a `TelegramAgentRuntime` that binds Telegram updates to the canonical
  contract builder and `AgentApplication`.
- Restored Telegram text/file/voice handling, including attachment download
  and voice transcription before routing.
- Added a canonical `ContractBuilder` that infers preparation actions,
  required access, file requirements, cognitive level and guarantees from the
  user request.
- Wired `agent_v2_2/cli.py start` to launch the operational runtime instead of
  a smoke message.
- Extended `AgentApplication` with progress callbacks so the Telegram flow can
  surface routing and execution progress.

### Verification

- Telegram transport kwargs test passes.
- Canonical contract builder test passes.
- Runtime voice routing and local status tests pass.
- Full Agent 2.2 suite: `24 passed`.

### Current roadmap position

- Step 3: `COMPLETE`.
- Step 4: `IN_PROGRESS`.

### Next action

Begin Step 4 by normalizing the task/evaluation schema and auditing the task
battery against the 17 operational capabilities so the benchmark arena can be
made representative instead of merely large.

## 2026-06-09: Step 4 Normalization Started

### Implemented

- Extended `TaskRecord` to preserve prompts, user requests, expected outputs,
  expected keys and existing rubrics from benchmark batteries.
- Added a deterministic `TaskNormalizer` that turns raw benchmark tasks into a
  canonical record with primary capability, secondary capabilities, compatible
  tools, objective checks, judge rubric and generated request contract.
- Added a normalized task report that summarizes primary capability coverage,
  compatible-tool coverage, missing rubrics and network-heavy tasks.
- Added `audit normalize` to the CLI for quick inspection of the normalized
  task model.
- Documented the normalized task model and the new CLI command.

### Verification

- Full Agent 2.2 suite: `25 passed`.
- `TaskNormalizer` preserves per-task rubrics and produces compatible tools
  for a simple spreadsheet comparison task.
- `audit normalize` is available as a new CLI entry point.
- CLI normalization report over the benchmark battery: `356` tasks, `0`
  missing rubrics, `28` network tasks, and a stable primary-capability
  distribution across the existing benchmark set.

### Current roadmap position

- Step 3: `COMPLETE`.
- Step 4: `IN_PROGRESS`.

### Next action

Expand the normalized model so it covers the full benchmark battery and then
use it to drive per-capability judge scoring and a more rigorous evaluation
arena.
