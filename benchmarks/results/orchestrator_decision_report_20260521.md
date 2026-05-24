# Orchestrator Decision Report - 2026-05-21

## Context

Groq and OpenRouter now have paid/credited access, so the final probe focuses on
system reliability instead of free-tier availability.

Terminology:

- **Herramienta**: any way to solve a task.
- Tool kinds:
  - `api_directa`
  - `cli_agentico`
  - `runtime_agentico`

Main run:

- Partial broad run: `benchmarks/results/20260521_171122_417657`
- Final hard-task run: `benchmarks/results/20260521_174516_442823`
- Judge: `codex:gpt-5.5`

## Final Hard-Task Results

Tasks: `test-17`, `test-20`, `test-21`, `test-23`, `test-26`, `test-30`.

| Herramienta | Jobs OK | Nota juez | Pass | Latencia media OK |
| --- | ---: | ---: | ---: | ---: |
| `openrouter:openai/gpt-5.4-mini` | 6/6 | 6.67 | 3/6 | 5.82s |
| `groq:groq/compound-mini` | 6/6 | 6.17 | 2/6 | 6.23s |
| `openrouter:deepseek/deepseek-v3.2` | 6/6 | 6.00 | 2/6 | 20.74s |
| `groq:llama-3.3-70b-versatile` | 6/6 | 5.17 | 1/6 | 2.26s |
| `groq:openai/gpt-oss-120b` | 6/6 | 5.17 | 0/6 | 2.68s |
| `opencode:openrouter/deepseek/deepseek-v3.2` | 5/6 | 5.17 | 2/6 | 170.03s |
| `groq:llama-3.1-8b-instant` | 6/6 | 5.00 | 2/6 | 1.45s |
| `groq:qwen/qwen3-32b` | 6/6 | 5.00 | 1/6 | 2.98s |

## Reading

The hard-task run is stricter than the earlier office benchmark. Scores are lower
because these tasks emphasize multi-file synthesis, research, audit, and executive
judgement under compact context.

The most reliable tool in this final probe is `openrouter:openai/gpt-5.4-mini`.
It is not the judge and not a fixed baseline; it is the strongest direct API worker
candidate in this final hard-task slice.

Groq remains the best place for speed. The strongest router candidates are:

- `groq:llama-3.1-8b-instant`: fastest, lower quality.
- `groq:qwen/qwen3-32b`: better balance in earlier router probe, but weaker in the hard slice.
- `groq:llama-3.3-70b-versatile`: fast and stable, worth keeping.

`groq:groq/compound-mini` improved once context was compact. It is now a real
candidate for cloud agentic runtime, but not yet the default.

OpenCode with OpenRouter works, but it is too slow to be the default. It should
remain a runtime tool for cases that truly need an external CLI agent.

## First Role Map

| Role | Primary | Fallback |
| --- | --- | --- |
| Fast router | `groq:qwen/qwen3-32b` | `groq:llama-3.1-8b-instant` |
| Ultra-fast classifier | `groq:llama-3.1-8b-instant` | `groq:llama-3.3-70b-versatile` |
| Reliable direct API worker | `openrouter:openai/gpt-5.4-mini` | `openrouter:deepseek/deepseek-v3.2` |
| Cheap direct API worker | `openrouter:deepseek/deepseek-v3.2` | `groq:qwen/qwen3-32b` |
| Cloud agentic runtime | `groq:groq/compound-mini` | `openrouter:openai/gpt-5.4-mini` |
| CLI/runtime agent | `opencode:openrouter/deepseek/deepseek-v3.2` | `codex:gpt-5.5` for escalation |
| Judge/escalation | `codex:gpt-5.5` | none |

## Implementation Created

New orchestrator core:

- `orchestrator_v2/`

Main modules:

- `models.py`: contracts for task, route, tool and result.
- `tool_registry.py`: selected tools and roles.
- `router.py`: rule-based router with privacy detection.
- `privacy.py`: input file copy and optional privacy guard integration.
- `executor.py`: executes selected tool through existing benchmark engines.
- `orchestrator.py`: minimal gestor facade.
- `cli.py`: local test CLI.

Verification:

- `python -m orchestrator_v2.cli --list-tools`
- `python -m orchestrator_v2.cli --route-only "..."`
- `python -m orchestrator_v2.cli "Di en una frase que el orquestador v2 funciona" --tool router_groq_qwen32 --privacy clear`
- `python -m compileall orchestrator_v2`

## Next Step

Connect `orchestrator_v2` to Telegram and move confirmation logic there:

1. If privacy is `ask` and PII is detected, ask user to choose `redacted`,
   `mixed`, or `clear`.
2. Route task to a herramienta.
3. Execute and store the trail: request, route decision, privacy report, tool
   result, cost/latency.
4. Build the blind lab as a Telegram client that talks to this completed gestor.

