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

## 2026-06-09: Step 4 Complete

### Implemented

- Reworked task normalization so the benchmark battery now classifies tasks
  by primary and secondary operational capability, not just by file type.
- Added explicit coverage for all 17 operational capabilities in the real
  benchmark battery.
- Added normalized coverage reporting for missing capabilities, compatible
  tools and network-heavy tasks.
- Added regression tests that verify the real benchmark battery has complete
  capability coverage and no missing rubrics.

### Verification

- Full Agent 2.2 suite: `27 passed`.
- Real benchmark normalization reports `356` tasks, `0` missing rubrics and
  `0` missing capabilities.
- The normalized battery now covers all 17 operational capabilities.

### Current roadmap position

- Step 4: `COMPLETE`.
- Step 5: `IN_PROGRESS`.

### Next action

Build the valid benchmark arena: run compatible tools over representative
tasks, persist latency and objective checks, and add blind judgment results so
the learned capability matrix can be computed from evidence rather than from
labels alone.

### Current roadmap position

- Step 3: `COMPLETE`.
- Step 4: `IN_PROGRESS`.

### Next action

Expand the normalized model so it covers the full benchmark battery and then
use it to drive per-capability judge scoring and a more rigorous evaluation
arena.

## 2026-06-09: Step 5 Benchmark Arena Started

### Implemented

- Added a reusable `BenchmarkArena` layer that executes normalized tasks
  against a selected tool, evaluates objective checks and stores router
  experiences.
- Added `ArenaRunResult` and `ArenaReport` for per-run and aggregate evidence.
- Added a pluggable `ArenaExecutor` and `ArenaJudge` interface so real tool
  runners and blind judges can be wired in later without changing the arena
  contract.
- Added a `BenchmarkRunner` that maps normalized tools to benchmark engine
  specs, copies benchmark assets into isolated workdirs, and exposes the arena
  through `audit arena --limit N`.
- Added an optional blind Gemini judge path via `BENCH_GEMINI_JUDGE_MODEL`,
  with a local objective-check fallback when no judge model is configured.
- Documented the benchmark arena and exposed it through the evolution package.

### Verification

- Full Agent 2.2 suite: `28 passed`.
- Arena smoke test persists runs, objective checks and judge scores.
- The benchmark runner now emits usable arena reports from the CLI, including
  limited sample runs.

### Current roadmap position

- Step 4: `COMPLETE`.
- Step 5: `IN_PROGRESS`.

### Next action

Wire the arena to representative real executions and blind judgments so the
experience store begins to reflect latency and quality evidence from actual
compatible tools instead of only simulated runs.

## 2026-06-09: Step 6 Matrix Started

### Implemented

- Added a learned capability matrix builder that aggregates experiences into
  tool/capability/task-shape cells.
- Each cell now carries samples, pass rate, mean judge score, mean latency,
  latency dispersion, confidence and judge sample count.
- Added CLI support for `audit matrix` and documented the matrix contract.

### Verification

- Full Agent 2.2 suite: `30 passed`.
- `audit matrix` reports `1,769` experiences and `1,024` learned cells.
- The matrix report is persisted as markdown-friendly CLI output.
- The matrix continues to absorb arena experiences through the shared store.

### Current roadmap position

- Step 5: `IN_PROGRESS`.
- Step 6: `IN_PROGRESS`.

### Next action

Begin using the arena runner against representative task slices so the matrix
starts to incorporate fresh benchmark evidence from actual runs, not only from
imported history.

## 2026-06-09: Arena Sample Run Verified

### Implemented

- Executed `python -m agent_v2_2.cli audit arena --limit 1` against the
  normalized battery.
- Verified that the benchmark runner reaches the full path from normalized task
  selection through execution, objective checks, blind judgment and experience
  persistence.
- Confirmed the CLI prints a usable arena summary with pass count, timing,
  judge scores and tool distribution.

### Verification

- Arena sample report: `1` run, `1` passed, `1.172s` average, `1` judge score
  recorded.
- Sample tool path: `router_groq_qwen32`.
- The command completed without manual intervention and produced a persisted
  run record in the shared experience store.

### Current roadmap position

- Step 5: `IN_PROGRESS`.
- Step 6: `IN_PROGRESS`.

### Next action

Use additional representative slices to expand the arena evidence before
promoting the router to the next evolutionary stage.

## 2026-06-11: Slice-Oriented Audit Support

### Implemented

- Added explicit `--path` support to `audit arena` and `audit normalize` so
  individual batteries can be audited without running the entire benchmark
  corpus.
- Verified the new slice flow with `reasoning_latency_tasks_20260607.json`,
  which produced one successful arena run and a live judge score.
- Confirmed that some batteries normalize cleanly but still have no compatible
  tools for execution, which is a coverage gap in the task/tool matrix rather
  than a failure in the normalizer or arena.

### Verification

- Full Agent 2.2 suite: `32 passed`.
- `audit normalize --path benchmarks/tasks/assistant_tasks.json` shows
  33 normalized tasks with `gemini_pro_long_context` and `premium_codex_55`
  as the compatible tools on that slice.
- `audit normalize --path benchmarks/tasks/reasoning_latency_tasks_20260607.json`
  shows `3` normalized tasks with a narrower compatibility set.
- `audit arena --path benchmarks/tasks/reasoning_latency_tasks_20260607.json --limit 1`
  yields `1` run, `1` passed, `3.312s` average and one judge score.

### Current roadmap position

- Step 5: `IN_PROGRESS`.
- Step 6: `IN_PROGRESS`.

### Next action

Keep slicing the benchmark batteries by task family so we can add more real
executions, identify remaining compatibility gaps, and feed the learned matrix
with fresh evidence instead of only broad corpus scans.

## 2026-06-11: Parity Closed Except Codex Arena

### Implemented

- Connected Telegram reload and restart to a lifecycle supervisor that rebuilds
  the runtime.
- Added persistent allowed-directory commands and provider diagnostics without
  exposing secrets.
- Added concurrent Telegram dispatch and concrete cancellation for running
  command and Codex processes.
- Verified voice preferences, Telegram audio delivery and local speaker
  playback.
- Verified threads, alarms, persistent queue controls, privacy confirmation and
  the complete development proposal-to-publication state machine.
- Restricted evolutionary exploration to reproducible benchmark tasks.
- Made evolutionary activation depend on the strict HITL readiness gate.
- Added `READ_FIRST.md` and a dated task audit.

### Verification

- Full Agent 2.2 suite: `59 passed`.
- Task audit: `362` tasks and `0` invalid fixtures.
- Readiness: `1,879` valid experiences, `149` judged, `17/17` capabilities,
  `44/56` tool-capability pairs demonstrated.
- Functional parity: `34/35`; only the live Codex arena row remains pending.

### Quota checkpoint

- Five-hour Codex remaining: `0%`.
- Five-hour reset: `2026-06-11 16:21` Europe/Madrid.
- Weekly remaining at checkpoint: `64%`.
- No Codex run may start until the five-hour window is refreshed above the
  configured 25% reserve.

### Exact next action

Run the 12 planned `premium_codex_55` first-demonstration tasks with the Gemini
API blind judge, in small groups while refreshing quota. Then regenerate
training coverage and readiness, complete the final parity row, activate the
evolutionary system and stop for real Telegram HITL.

## 2026-06-11: Roadmap Complete, Ready For Human HITL

### Completed

- Ran the 12 missing `premium_codex_55` capability demonstrations with live
  execution and Gemini 3.1 Pro blind judging.
- Reached 56 of 56 demonstrated compatible tool-capability pairs.
- Added a sanitized portable seed containing 111 judged experiences; it
  contains no prompts, outputs, local paths, credentials or user data.
- Verified a fresh empty workspace bootstraps from the seed and passes the
  strict readiness gate.
- Activated the evolutionary router. Runtime construction now selects
  `EvolutionarySelector` only when the persisted activation state is valid.
- Added HITL correction and friction capture through `correccion: ...` and
  `friccion: baja|media|alta`.

### Final verification

- Agent 2.2 tests: `63 passed`.
- Task audit: `362` tasks, `0` invalid fixtures and all format buckets covered.
- Readiness: `1,891` valid experiences, `161` judged, `17/17` capabilities,
  `9/9` selectable tools, `31` task shapes and `56/56` demonstrated pairs.
- Evolution status: active, maturity `35/35`.
- Current Codex quota at verification: five-hour `77%`, weekly `57%`.

### Stop condition reached

All autonomous roadmap steps are complete. The next meaningful evidence
requires a real person interacting through Telegram. Start with:

1. `estado`
2. `iniciar bateria`
3. `prueba siguiente` or `repetir prueba`
4. `correccion: <what should change>` when the result is wrong or incomplete
5. `friccion: baja|media|alta` after each representative task
