# Functional Parity Matrix: Agent 2.2

This file is an executable maturity contract. A row is complete only when the
behavior is connected to the Agent 2.2 runtime and covered by a focused test.
The existence of an isolated class is not completion evidence.

| Area | Expected behavior | Agent 2.2 implementation | Evidence | Status |
| --- | --- | --- | --- | --- |
| Telegram | Authorized long polling, text, edits, voice and files | `transport/telegram.py`, `runtime.py` | transport and runtime tests | Completed |
| Telegram | Chunked text plus image, audio and file delivery | `transport/telegram.py` | transport tests | Completed |
| Telegram | Visible received, routed, executing, fallback and completion progress | `runtime.py`, `application.py` | runtime flow test | Completed |
| Runtime | Isolated inbox/outbox and workdirs | `transport/queue.py`, `engines/workspace.py` | smoke tests | Completed |
| Runtime | Controlled reload/restart connected to Telegram | `transport/lifecycle.py`, `runtime.py`, `cli.py` | runtime lifecycle test | Completed |
| Voice | Groq transcription with configured fallback behavior | `capabilities/voice.py`, `runtime.py` | transcription path test | Completed |
| Voice | Full text reply plus optional oral summary sent to Telegram | `capabilities/voice.py`, `runtime.py` | runtime audio delivery test | Completed |
| Voice | Optional local speaker playback | `capabilities/voice.py`, `runtime.py` | runtime speaker test | Completed |
| Voice | Persistent `voz on/off`, `altavoz on/off`, provider and voice commands from Telegram | `capabilities/preferences.py`, `runtime.py` | runtime preference command test | Completed |
| Memory | Persistent per-user/thread journal, facts, index and relevant retrieval | `capabilities/memory.py`, `application.py` | memory tests | Completed |
| Memory | Memory remains silent unless relevant or explicitly requested | `capabilities/memory.py`, `capabilities/status.py` | status and retrieval tests | Completed |
| Memory | Thread list/create/switch/current commands from Telegram | `capabilities/memory.py`, `runtime.py` | runtime thread test | Completed |
| Scheduling | Relative/absolute and recurring alarms | `scheduling/alarms.py` | parser, persistence and delivery tests | Completed |
| Scheduling | Alarm list/cancel and Telegram delivery after restart | `scheduling/alarms.py`, `runtime.py` | runtime alarm command test | Completed |
| Scheduling | Persistent pending queue with list/resume/clear/stop commands | `scheduling/queue.py`, `runtime.py` | runtime queue command test | Completed |
| Router | Canonical capability contract and hard compatibility | `routing/contract.py`, `routing/selector.py` | contract tests | Completed |
| Router | Evidence-aware fastest-sufficient selection, exploration and rollback | `routing/evolutionary.py`, `application.py` | evolutionary tests | Completed |
| Router | Real API, Gemini CLI and Codex CLI execution with isolated assets | `engines/execution.py` | arena tests and live runs | Completed |
| Router | Desktop automation remains isolated and deferred | `engines/codex_desktop.py` | explicit product decision | Completed |
| Safety | Clear/mixed/redacted privacy state applied to requests | `privacy/core.py`, `runtime.py` | request redaction test | Completed |
| Safety | Persistent yes/no confirmation for sensitive external or irreversible actions | `privacy/core.py`, `runtime.py` | runtime confirmation test | Completed |
| Safety | Cancellation of a running operation | `routing/cancellation.py`, `runtime.py`, benchmark engines | concurrent runtime and process cancellation tests | Completed |
| Safety | Secrets remain in environment/local ignored storage and are redacted from status | `config.py`, `capabilities/status.py` | status test | Completed |
| Status | `estado` reports APIs, CLIs, runtime and configuration without memory inventory | `capabilities/status.py`, `runtime.py` | status test | Completed |
| Introspection | Normal-mode questions explain capabilities, tools and tiers | `capabilities/introspection.py`, `runtime.py` | introspection tests | Completed |
| Development | Activation accepts `modo desarrollo`, `modo de desarrollo` and `modo desarrollador` | `capabilities/dev_mode.py`, `runtime.py` | alias and persistence test | Completed |
| Development | Persistent proposal, approval, isolated implementation, tests, commit and publication | `capabilities/dev_mode.py` | proposal-to-publication workflow test | Completed |
| Development | Immediate deactivation and cancellation | `capabilities/dev_mode.py` | controller cancellation path and alias test | Completed |
| Operations | Real Codex five-hour/weekly quota and autonomous checkpointing | `scheduling/codex_quota.py`, `scheduling/autonomy.py` | quota tests and live snapshot | Completed |
| Operations | Configurable workspace and additional allowed directories | `config.py` | parser tests | Completed |
| Operations | Add/remove directory and provider diagnostics commands | `capabilities/directories.py`, `capabilities/status.py`, `runtime.py` | persistence and runtime command test | Completed |
| Evolution | Audited normalized tasks with per-capability rubrics | `evolution/audit.py`, `normalization.py` | 362-task audit, zero invalid fixtures | Completed |
| Evolution | Valid live arena with blind judging for every compatible tool-capability pair | `evolution/arena.py`, `training_coverage.py` | 56/56 demonstrated with valid live blind judgments | Completed |
| Evolution | Learned matrix with samples, dispersion, quality, confidence and latency | `evolution/matrix.py` | matrix tests | Completed |
| Evolution | HITL battery, feedback and friction telemetry | `evolution/hitl.py`, `runtime.py` | controller, feedback and runtime command tests | Completed |
