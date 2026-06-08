# Handoff Report — Telegram Codex Orchestrator

This document summarizes the current status, architecture, and next steps for the development of the **Telegram Codex Orchestrator** in this environment. It is designed to allow another AI agent or developer to quickly resume the project without missing critical context.

If you are resuming from a fresh conversation, start with [LEEME_PRIMERO.md](LEEME_PRIMERO.md), then read [docs/ROUTER_CAPABILITY_MASTER_20260608.md](docs/ROUTER_CAPABILITY_MASTER_20260608.md), the project README, and the remaining router capability docs.

The next clean implementation is specified in
[docs/ANTIGRAVITY_REFACTOR_HANDOFF_20260608.md](docs/ANTIGRAVITY_REFACTOR_HANDOFF_20260608.md).
The ready-to-paste Gemini prompt is
[docs/ANTIGRAVITY_MASTER_PROMPT_20260608.md](docs/ANTIGRAVITY_MASTER_PROMPT_20260608.md).
The target is a self-contained `agent_v2_2/` with functional parity across the
current and historical orchestrators before it replaces either one.

---

## 1. Project Overview & Architecture

The Telegram Codex Orchestrator (`inspector`) is an autonomous agent designed to receive instructions in natural language via Telegram, determine the user's intent, and execute corresponding actions either via local modules (alarm management, memory persistence, context switching) or via the **Codex CLI**.

### System Components

*   **Orchestrator Hub (`orchestrator.py`):** The central hub that integrates Telegram, manages message threads, handles incoming files (saving them in the inbox first), controls task execution queues, and integrates Text-to-Speech (TTS) / Speech-to-Text (STT).
    *   File: [orchestrator.py](file:///d:/inspector/telegram_codex_orchestrator/orchestrator.py)
*   **Intent Classifier (`intent.py`):** Translates natural language messages into internal actions. It contains local regular expression fallback patterns for actions in Spanish and English (useful when LLMs are offline) and queries Gemini/Groq APIs.
    *   File: [intent.py](file:///d:/inspector/telegram_codex_orchestrator/intent.py)
*   **Codex Runner (`codex_runner.py`):** Interacts with the Codex command line interface (`codex.exe`) in a sandbox context with configurable permissions.
    *   File: [codex_runner.py](file:///d:/inspector/telegram_codex_orchestrator/codex_runner.py)
*   **Alarms Engine (`alarms.py`):** Handles scheduled and relative alarms based on natural language expressions.
    *   File: [alarms.py](file:///d:/inspector/telegram_codex_orchestrator/alarms.py)
*   **Thread Store (`thread_store.py`):** Saves and restores the context threads for different sessions, isolating tasks.
    *   File: [thread_store.py](file:///d:/inspector/telegram_codex_orchestrator/thread_store.py)
*   **Speech I/O (`speech_io.py`):** Dictation transcription and narrative summaries spoken aloud using TTS/STT APIs.
    *   File: [speech_io.py](file:///d:/inspector/telegram_codex_orchestrator/speech_io.py)
*   **Test Bench Runner (`test_bench_runner.py`):** The validation framework which executes 30 synthetic tests verifying the intent classification, context switching, memory recall, and Codex command execution.
    *   File: [test_bench_runner.py](file:///d:/inspector/telegram_codex_orchestrator/test_bench_runner.py)

---

## 2. Current Progress & Milestones

A comprehensive evaluation run (Round 3) of the synthetic test bench was successfully executed on **2026-06-02**.

*   **Test Results:** **29/30 PASS (96.7% success rate)**
*   **Validation Report:** Check the full test log at [test_bench_report.md](file:///d:/inspector/test_bench_report.md).
*   **Key Fixes Implemented:**
    1.  **Spanish NLP Fallback:** Enhanced regular expressions in `intent.py` to correctly map common Spanish commands (e.g., "calcula", "traduce", "escribe") directly to the `codex` action without failing when external LLM APIs are unreachable.
    2.  **Thread-based Watchdog:** Implemented a `threading.Thread` watchdog with a 200-second hard limit in `test_bench_runner.py` to prevent Codex from hanging indefinitely when executing problematic scripts.
    3.  **Inbox-to-Workdir Semicontinuous Sinc:** Files received sequentially are placed into the `inbox` subdirectory and automatically synchronized to the active working directory before Codex runs, matching real-world Telegram behavior.

---

## 3. Critical Known Issues & Workarounds

### A. Codex Python Syntax Hangs (Task #20 Fail)
*   **Problem:** Task #20 ("Fix python program" on [programa_roto.py](file:///d:/inspector/temp_bench_workdir/programa_roto.py)) fails because the Codex CLI hangs indefinitely (becoming a zombie subprocess) when processing Python scripts with critical syntax errors. It does not overwrite the output file correctly.
*   **Mitigation:** The active runner now forces a watchdog timeout of 200s to abort the process and log a failure instead of locking the entire system.
*   **Next Steps:** Investigate how the `openai.chatgpt` extension processes stdin/stdout on syntax errors, or implement a validation script wrapper that validates python syntax *before* feeding it to Codex.

### B. Groq/External LLM API 401/403 Errors
*   **Problem:** Groq credentials available in the environment are returning authentication errors (`HTTP 403 / 1010` / `401 Unauthorized`).
*   **Mitigation:** The system relies entirely on `intent.py` local NLP regex parsing and the Gemini API fallback if a valid `GOOGLE_API_KEY` is loaded.
*   **Next Steps:** Update `.env` or `D:\credenciales` with valid API keys.

---

## 4. Next Steps for Development

1.  **Configure API Keys:** Ensure valid `GOOGLE_API_KEY` or `GROQ_API_KEY` are placed in the environment loading chains (check [README.md](file:///d:/inspector/telegram_codex_orchestrator/README.md#L65-L73) for exact lookup locations).
2.  **Resolve Python Subprocess Zombification:** Debug why `codex.exe` hangs on syntax errors. Check if it requires specific flags or if we can run a local linter/verifier step.
3.  **Real telegram integration testing:** Run the server using [arrancar_orquestador.bat](file:///d:/inspector/arrancar_orquestador.bat) and send voice messages + files to verify end-to-end user experience (including Text-To-Speech generation).
4.  **Inbox cleanups:** Ensure the inbox directory doesn't accumulate garbage over long sessions by establishing a session TTL or cleanup commands.
