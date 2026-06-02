# Voice STT benchmark

Date: 2026-06-02

This note records the current transcription choice for the Telegram orchestrator.

## What we tested

Sample audio:

- `telegram_codex_orchestrator/runtime/voice/tts/gemini_20260602_105634_889594.wav`

That sample was generated locally with Gemini TTS so we could test transcription against a known clean file.

## Results

- Gemini STT: worked, about 2.16s on the direct call.
- Gemini via the generic `SpeechIO.transcribe()` path: worked, about 4.70s total.
- Groq STT: failed with `HTTP 403` / `error code: 1010` in this runtime.

## Decision

The orchestrator now prefers:

1. Gemini STT
2. Groq STT as fallback

That keeps the live path on the fastest working API-based transcription provider we have right now.

## Reproduce

The relevant code lives in:

- `telegram_codex_orchestrator/speech_io.py`

The transcription entrypoint is `SpeechIO.transcribe()`. It now tries Gemini first and only falls back to Groq if Gemini is unavailable or fails.

## Notes

If Groq access is fixed later, rerun the same sample and update this note with the new timings before changing the order again.
