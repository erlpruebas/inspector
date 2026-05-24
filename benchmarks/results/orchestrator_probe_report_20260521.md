# Orchestrator Probe Report - 2026-05-21

## Purpose

This run answers one practical question: what still needs testing before designing
the final Telegram orchestrator/router.

The important correction is that `codex:gpt-5.4-mini` is not a fixed operational
baseline. It is a strong candidate/reference, but the actual production router
must be chosen by latency, reliability, cost, and routing quality.

## Live Provider Health

Run: `benchmarks/results/provider_health_current.json`

| Provider/runtime | Status | Notes |
| --- | --- | --- |
| Codex CLI | OK | Installed, `codex-cli 0.131.0-alpha.9`. |
| Gemini CLI | OK | Installed, `0.42.0`. |
| OpenCode | OK | Installed, `1.15.6`. |
| Groq API | OK | API key works. |
| OpenRouter API | OK | API key works. |
| Gemini API | FAIL | Configured key is invalid for Google API. |
| Viking/MiniNano | FAIL | Local/tunnel endpoint is not reachable now. |
| LM Studio | FAIL | Local server not running. |

## New Matrices

| File | Purpose |
| --- | --- |
| `benchmarks/engine_matrix_groq_router_compound_20260521.json` | Test Groq fast router candidates and Groq Compound systems. |
| `benchmarks/engine_matrix_openrouter_free_cheap_20260521.json` | Test OpenRouter free and cheap candidates discovered from the live model catalog. |

## Groq Router And Compound Probe

Run: `benchmarks/results/20260521_163310_358778`

Tasks: `test-01`, `test-03`, `test-05`, `test-10`.

| Engine | OK/jobs | Avg elapsed OK | Heuristic avg | Reading |
| --- | ---: | ---: | ---: | --- |
| `groq:qwen/qwen3-32b` | 4/4 | 2.34s | 8.75 | Best current Groq candidate for useful routing/worker tasks. |
| `groq:llama-3.3-70b-versatile` | 4/4 | 1.18s | 7.50 | Fast and stable in this small probe. |
| `groq:meta-llama/llama-4-scout-17b-16e-instruct` | 4/4 | 2.07s | 7.50 | Stable candidate, not clearly better than Qwen. |
| `groq:openai/gpt-oss-120b` | 4/4 | 2.92s | 7.50 | Stronger worker candidate, slower than smaller models. |
| `groq:llama-3.1-8b-instant` | 4/4 | 1.08s | 6.88 | Very fast router candidate, quality lower. |
| `groq:openai/gpt-oss-20b` | 4/4 | 1.55s | 5.62 | Fast, but weaker in this probe. |
| `groq:groq/compound-mini` | 2/4 | 4.52s | 3.12 | Works partially, but hit TPM/rate limits. |
| `groq:groq/compound` | 1/4 | 5.92s | 0.62 | Not ready with current wrapper/context; hit 413 and 429. |

Conclusion: Groq API direct is ready for router/worker trials. Groq Compound is
worth keeping, but it needs a compact-context wrapper before serious testing.

## OpenRouter Free/Cheap Probe

Run: `benchmarks/results/20260521_163605_061577`

Tasks: `test-01`, `test-03`, `test-05`, `test-10`.

| Engine | OK/jobs | Avg elapsed OK | Heuristic avg | Reading |
| --- | ---: | ---: | ---: | --- |
| `openrouter:deepseek/deepseek-v3.2` | 4/4 | 6.43s | 7.50 | Best cheap OpenRouter candidate in this probe. |
| `openrouter:qwen/qwen3.5-flash-02-23` | 4/4 | 27.34s | 7.50 | Quality signal OK, but slow. |
| `openrouter:minimax/minimax-m2.7` | 4/4 | 13.65s | 6.25 | Usable, not leading. |
| `openrouter:nvidia/nemotron-3-super-120b-a12b:free` | 4/4 | 27.49s | 6.25 | Free and works, but slow. |
| `openrouter:baidu/cobuddy:free` | 4/4 | 14.29s | 3.12 | Works, weak task quality. |
| `openrouter:deepseek/deepseek-v4-flash:free` | 1/4 | 33.22s | 2.50 | Rate-limited upstream; unreliable free tier. |
| `openrouter:z-ai/glm-5.1` | 4/4 | 14.67s | 1.88 | Works technically, poor task fit here. |
| `openrouter:deepseek/deepseek-v3.2-speciale` | 0/4 | n/a | 0.00 | Provider returned 400. |
| `openrouter:minimax/minimax-m2.5:free` | 0/4 | n/a | 0.00 | Rate-limited upstream. |
| `openrouter:qwen/qwen3-next-80b-a3b-instruct:free` | 0/4 | n/a | 0.00 | Rate-limited upstream. |
| `openrouter:qwen/qwen3.5-9b` | 4/4 | 19.92s | 0.00 | Technically OK, output missed expected keys. |
| `openrouter:z-ai/glm-4.7-flash` | 4/4 | 7.18s | 0.00 | Technically OK, output missed expected keys. |

Conclusion: the free OpenRouter tier remains useful for opportunistic tests, not
for a stable production route. `deepseek-v3.2` is the current practical cheap
OpenRouter worker.

## OpenCode Provider Probe

Run: `benchmarks/results/20260521_164649_623710`

| Engine | Result | Reading |
| --- | --- | --- |
| `opencode:openrouter/deepseek/deepseek-v3.2` | OK on `test-01`, 92.20s | OpenCode + OpenRouter can work, but it is slow. |
| `opencode:groq/openai/gpt-oss-20b` | FAIL | OpenCode sent too much context for Groq TPM. |
| `opencode:groq/llama-3.1-8b-instant` | FAIL | Same context/TPM issue. |

Conclusion: OpenCode is worth keeping as an external runtime for OpenRouter, but
Groq through OpenCode needs prompt/context compaction before it is meaningful.

## Current Decisions

1. Router candidates to test next:
   `groq:llama-3.1-8b-instant`, `groq:qwen/qwen3-32b`,
   `groq:llama-3.3-70b-versatile`.
2. Worker candidates to keep:
   `groq:qwen/qwen3-32b`, `groq:openai/gpt-oss-120b`,
   `openrouter:deepseek/deepseek-v3.2`, `openrouter:openai/gpt-5.4-mini`,
   `openrouter:deepseek/deepseek-r1`.
3. Premium judge/escalation:
   `codex:gpt-5.5`.
4. External agentic runtime candidates:
   Codex CLI, OpenCode + OpenRouter, and later Groq Compound after context
   compaction.
5. Do not use OpenCode to evaluate GPT/Gemini when native CLI/API routes exist;
   use OpenCode to evaluate OpenRouter/Groq/other providers as a runtime.

## Before Building The Final Orchestrator

1. Add a compact-context mode for Groq Compound and OpenCode+Groq.
2. Run a final reduced benchmark with judge `codex:gpt-5.5` over:
   - router classification tasks
   - simple office tasks
   - file extraction tasks
   - CSV/accounting tasks
   - one multi-step task
3. Freeze the role map:
   - fast router
   - cheap worker
   - reasoning worker
   - agentic runtime
   - premium judge/escalation
4. Only then design the final Telegram orchestrator.

