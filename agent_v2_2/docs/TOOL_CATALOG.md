# Normalized Tool Catalog

Implementation:
`agent_v2_2/src/agent_v2_2/capabilities/catalog.py`

Functional source:
`orchestrator_v2_1/capability_catalog.json`

## Registered Routes

| Stable ID | Invocation | Status | Selection |
| --- | --- | --- | --- |
| `local_direct` | local | active | eligible |
| `router_groq_qwen32` | Groq API | active | eligible |
| `worker_openrouter_deepseek32` | OpenRouter API | active | eligible |
| `worker_openrouter_gpt54mini` | OpenRouter API | experimental | disabled |
| `worker_groq_compound_mini` | Groq API | active | eligible |
| `worker_groq_compound` | Groq API | active | eligible |
| `gemini_grounded_search` | Google API | active | eligible |
| `gemini_flash_files` | Google API | active | eligible |
| `gemini_flash_35` | Google API | sampled | eligible |
| `gemini_pro_long_context` | Gemini CLI | demonstrated | eligible |
| `runtime_opencode_deepseek32` | OpenCode | experimental | disabled |
| `premium_codex_55` | Codex CLI | demonstrated | eligible |
| `desktop_codex_operator` | Codex Desktop | deferred | disabled |

## Normalized Fields

Each route records:

- stable ID and display name;
- invocation type, provider and model;
- operational status and selection eligibility;
- maximum demonstrated cognitive level;
- instrumental capabilities;
- cognitive strengths and best-fit operations;
- known limits;
- direct file operations by format;
- observed latency;
- provenance and historical evidence;
- per-capability scores.

Per-capability scores intentionally remain empty until the normalized arena
produces comparable evidence. Historical global scores are retained only in the
general evidence field.

## Compatibility Rule

A route is compatible only when all required instrumental capabilities and
file operations in the canonical request contract are present. Cognitive
ranking and latency are considered only after this hard filter.

