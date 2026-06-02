I’ll verify Groq against its official docs first, then create local probe scripts that avoid logging secrets and capture timings/status/errors for each capability. After that I’ll run them from this directory and write the report artifacts here.

The official docs identify the OpenAI-compatible base URL as `https://api.groq.com/openai/v1`; for this intent the current relevant choices are `llama-3.1-8b-instant` for light chat, `whisper-large-v3-turbo` for low-cost/fast STT, and `canopylabs/orpheus-v1-english` for TTS. I’m going to encode those defaults in a small probe script, with overrides via environment variables.

The directory currently only has the prompt and request metadata. PowerShell is trying to load a disabled user profile in this sandbox, so I’ll run subsequent commands without login profile loading.

I’m adding a single stdlib Python probe now. It will call the official endpoints directly, choose documented defaults, write sanitized JSON results, and persist only non-secret artifacts like response metadata and generated audio.

The probe script is in place. I’m running it once with the environment keys already present; the console output will only include booleans, statuses, timings, and sizes.

All four requests failed before receiving HTTP responses, so this is looking like a local network/DNS/TLS path issue rather than a Groq API behavior issue. I’m reading the captured result details and will add a small connectivity preflight so the report can distinguish “API rejected request” from “machine cannot reach endpoint.”

The exact captured error is Windows socket permission denial: `[WinError 10013] Intento de acceso a un socket no permitido por sus permisos de acceso`. I’m going to run one non-secret TCP preflight to `api.groq.com:443` and include that as evidence for the local connectivity block.

The TCP preflight resolved `api.groq.com` but could not open port 443, confirming the machine/session cannot establish outbound HTTPS to Groq. I’m writing the local report with the tested endpoints, captured timings, and the retry configuration/fixes.

Verdict: **does not work from this machine/session**.

I created and ran the local probe:

- [probe_groq.py](D:/inspector/model_probe/runs/20260602_120006_groq/probe_groq.py)
- [report.md](D:/inspector/model_probe/runs/20260602_120006_groq/report.md)
- [artifacts/results.json](D:/inspector/model_probe/runs/20260602_120006_groq/artifacts/results.json)
- [artifacts/stt_tone_fixture.wav](D:/inspector/model_probe/runs/20260602_120006_groq/artifacts/stt_tone_fixture.wav)

All Groq API tests failed before receiving any HTTP status. Exact error for list models, chat, TTS, and STT:

`<urlopen error [WinError 10013] Intento de acceso a un socket no permitido por sus permisos de acceso>`

A TCP preflight to `api.groq.com:443` resolved DNS but failed:

`TcpTestSucceeded: false`, elapsed `6473.48 ms`.

Recommended config is documented in the report: base URL `https://api.groq.com/openai/v1`, chat `llama-3.1-8b-instant`, STT `whisper-large-v3-turbo`, TTS `canopylabs/orpheus-v1-english` with voice `austin`.

Official docs used:

- https://console.groq.com/docs/models
- https://console.groq.com/docs/text-chat
- https://console.groq.com/docs/speech-to-text
- https://console.groq.com/docs/text-to-speech/