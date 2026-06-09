# Autonomous Roadmap: Agent 2.2 to HITL

Last updated: 2026-06-09

## Objective

Reach a real HITL validation phase with an integrated Agent 2.2 and an
evidence-based router. A phase is complete only when its exit criteria are
verified. Creating a module or marking a checklist is not sufficient evidence.

## Status Vocabulary

- `PENDING`: work has not started or the current implementation is not usable.
- `IN_PROGRESS`: implementation or validation is underway.
- `BLOCKED`: external input or a quota reset is strictly required.
- `COMPLETE`: exit criteria have passed and evidence is recorded below.

## Roadmap

| Step | Status | Deliverable | Exit criteria |
| ---: | --- | --- | --- |
| 0 | COMPLETE | Reliable autonomous-work controls | Real Codex five-hour and weekly quota reader in Agent 2.2; persistent checkpoint; 25% five-hour reserve; graceful weekly stop |
| 1 | COMPLETE | Canonical capability contract | One versioned schema for preparation, required access, formats, operation, cognitive requirement and guarantees; validation tests |
| 2 | COMPLETE | Normalized tool catalog | Every real tool has a stable ID, invocation path, binary access flags, supported file operations, eligibility and measured evidence |
| 3 | IN_PROGRESS | End-to-end vertical flow | Telegram text/file/voice request reaches preparation, routing, execution, verification, response and experience storage |
| 4 | PENDING | Normalized task and evaluation model | Tasks identify primary/secondary capabilities, compatible tools, objective checks and per-capability judge rubrics |
| 5 | PENDING | Valid benchmark arena | Compatible tools run against representative tasks; latency, objective checks and blind Gemini judgments are persisted; Codex arbitrates selected cases |
| 6 | PENDING | Learned capability matrix | Tool x capability x task-shape statistics include samples, mean, dispersion, pass rate, confidence and latency |
| 7 | PENDING | Real evolutionary router | Hard compatibility filtering, confidence-aware fastest-sufficient selection, safe exploration and rollback are tested |
| 8 | PENDING | HITL readiness | Real Telegram tests can start with documented prompts, feedback capture, friction metrics and recovery procedures |

## Execution Order

Steps are completed in order. Work from a later step is allowed only when it
directly removes a blocker for the current step.

## Step 0: Autonomous-Work Controls

Current finding:

- `orchestrator_v2_1/codex_rate_limits.py` reads the real Codex five-hour and
  weekly windows through `account/rateLimits/read`.
- `agent_v2_2/scheduling/codex_quota.py` does not. It currently models a local
  one-million-token monthly allowance and cannot enforce the requested policy.

Resolution:

- Agent 2.2 now reads `account/rateLimits/read` directly through the Codex
  app-server.
- Snapshots are persisted with five-hour and weekly reset timestamps.
- `QuotaAwareScheduler` pauses only Codex work at the five-hour reserve and
  continues eligible non-Codex work.
- Paused Codex work is restored to pending after a fresh eligible snapshot.
- Missing or stale snapshots block new Codex work conservatively.

Required work:

1. Port the real rate-limit reader into Agent 2.2 without importing v2.1.
2. Persist the latest valid snapshot and reset timestamps.
3. Stop scheduling new Codex/GPT work at 25% five-hour remaining.
4. Continue Gemini, Groq, local and documentation work while Codex is paused.
5. Resume Codex work after a verified five-hour reset.
6. Stop autonomous work when the weekly allowance reaches the configured
   reserve and write a final checkpoint.
7. Treat missing or stale quota data conservatively: do not start expensive
   Codex jobs until quota can be verified.

## Completion Evidence

Evidence is added here when each step closes:

| Step | Completion date | Tests/evidence | Commit |
| ---: | --- | --- | --- |
| 0 | 2026-06-09 | `16 passed`; live snapshot read; pause/continue/resume tests | pending commit |
| 1 | 2026-06-09 | `18 passed`; memory-to-web and XLSX preservation contract tests | pending commit |
| 2 | 2026-06-09 | 13 stable routes; 10 eligible; access-method validation; `18 passed` | pending commit |
| 3 | - | - | - |
| 4 | - | - | - |
| 5 | - | - | - |
| 6 | - | - | - |
| 7 | - | - | - |
| 8 | - | - | - |

## Autonomous Stop Conditions

Autonomous development stops only when one of these conditions is true:

1. Step 8 is complete and the next action requires real human HITL interaction.
2. The Codex weekly allowance reaches its reserve and remaining useful work
   cannot be completed without Codex.
3. A decision with irreversible, security-sensitive or product-defining
   consequences cannot be derived safely from repository evidence.
4. Required credentials, hardware or external service access are unavailable.

Every stop must update `DEVELOPMENT_JOURNAL.md` with the exact blocker, current
test state, changed files and the first command or action for resumption.

## Functional Source Of Truth

When Agent 2.2 disagrees with an older implementation, the older proven
behavior is the functional source of truth unless a documented product decision
explicitly changes it. Agent 2.2 must reproduce that behavior through clean,
self-contained code and stronger tests; it must not import the old modules.
