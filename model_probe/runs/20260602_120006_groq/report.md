# Groq Provider Probe Report

Run directory: `D:\inspector\model_probe\runs\20260602_120006_groq`

Date: 2026-06-02

## Verdict

Does not work from this machine/session.

The provider key environment variables are present, but every Groq HTTPS request failed before an HTTP response was received. The exact local error was:

`<urlopen error [WinError 10013] Intento de acceso a un socket no permitido por sus permisos de acceso>`

This points to local sandbox/firewall/socket permissions blocking outbound HTTPS, not to an application-level Groq error.

## Official Docs Used

- Models endpoint and supported models: https://console.groq.com/docs/models
- Chat completions: https://console.groq.com/docs/text-chat
- Speech to text: https://console.groq.com/docs/speech-to-text
- Text to speech: https://console.groq.com/docs/text-to-speech/

## Recommended Configuration

- Base URL: `https://api.groq.com/openai/v1`
- API key env var priority: `GROQ_API_KEY`, fallback `PROVIDER_API_KEY`
- List models: `GET /models`
- Light chat model: `llama-3.1-8b-instant`
- Chat endpoint: `POST /chat/completions`
- STT model: `whisper-large-v3-turbo`
- STT endpoint: `POST /audio/transcriptions`
- TTS model: `canopylabs/orpheus-v1-english`
- TTS voice: `austin`
- TTS endpoint: `POST /audio/speech`

Optional overrides supported by the probe:

- `GROQ_BASE_URL`
- `GROQ_CHAT_MODEL`
- `GROQ_STT_MODEL`
- `GROQ_TTS_MODEL`
- `GROQ_TTS_VOICE`
- `GROQ_TIMEOUT_SECONDS`

## What Was Tested

Command:

```powershell
python probe_groq.py --out artifacts
```

The script creates a small local WAV fixture, then tests:

1. Model listing via official `GET /models`.
2. Lightweight chat via official `POST /chat/completions`.
3. TTS via official `POST /audio/speech`.
4. STT via official `POST /audio/transcriptions` using the local WAV fixture.
5. STT over generated TTS output only if TTS succeeds. This did not run because TTS failed before HTTP.

Artifacts:

- `probe_groq.py`
- `artifacts/results.json`
- `artifacts/stt_tone_fixture.wav`

## Exact Results

### Environment Preflight

- `GROQ_API_KEY`: present
- `PROVIDER_API_KEY`: present
- API key value: not printed or written

### TCP Connectivity Preflight

Command:

```powershell
$start=Get-Date; $r=Test-NetConnection api.groq.com -Port 443 -WarningAction SilentlyContinue; $elapsed=[math]::Round(((Get-Date)-$start).TotalMilliseconds,2); [pscustomobject]@{ComputerName=$r.ComputerName; RemotePort=$r.RemotePort; TcpTestSucceeded=$r.TcpTestSucceeded; ResolvedAddresses=($r.ResolvedAddresses -join ','); ElapsedMs=$elapsed} | ConvertTo-Json
```

Result:

```json
{
  "ComputerName": "api.groq.com",
  "RemotePort": 443,
  "TcpTestSucceeded": false,
  "ResolvedAddresses": "2606:4700:4405::6812:26ec,2606:4700:4409::ac40:9514,104.18.38.236,172.64.149.20",
  "ElapsedMs": 6473.48
}
```

### List Models

- Endpoint: `GET https://api.groq.com/openai/v1/models`
- HTTP status: none, no HTTP response received
- Timing: `124.86 ms`
- Body bytes: `0`
- Error type: `URLError`
- Error: `<urlopen error [WinError 10013] Intento de acceso a un socket no permitido por sus permisos de acceso>`

### Light Chat

- Endpoint: `POST https://api.groq.com/openai/v1/chat/completions`
- Model: `llama-3.1-8b-instant`
- HTTP status: none, no HTTP response received
- Timing: `3.16 ms`
- Body bytes: `0`
- Error type: `URLError`
- Error: `<urlopen error [WinError 10013] Intento de acceso a un socket no permitido por sus permisos de acceso>`

### TTS

- Endpoint: `POST https://api.groq.com/openai/v1/audio/speech`
- Model: `canopylabs/orpheus-v1-english`
- Voice: `austin`
- HTTP status: none, no HTTP response received
- Timing: `2.85 ms`
- Body bytes: `0`
- Error type: `URLError`
- Error: `<urlopen error [WinError 10013] Intento de acceso a un socket no permitido por sus permisos de acceso>`

### STT

- Endpoint: `POST https://api.groq.com/openai/v1/audio/transcriptions`
- Model: `whisper-large-v3-turbo`
- Input file: `artifacts/stt_tone_fixture.wav`
- HTTP status: none, no HTTP response received
- Timing: `13.87 ms`
- Body bytes: `0`
- Error type: `URLError`
- Error: `<urlopen error [WinError 10013] Intento de acceso a un socket no permitido por sus permisos de acceso>`

## Next Fixes If Blocked

1. Allow outbound TCP/HTTPS from this process/session to `api.groq.com:443`.
2. Verify connectivity first:

```powershell
Test-NetConnection api.groq.com -Port 443
```

Expected: `TcpTestSucceeded: True`.

3. Re-run:

```powershell
python probe_groq.py --out artifacts
```

4. If HTTP responses are then received but tests fail:

- `401` or `403`: verify the API key value and project/model permissions in GroqCloud.
- `404` or model-not-found errors: re-check current model IDs with `GET /models` and set `GROQ_CHAT_MODEL`, `GROQ_STT_MODEL`, or `GROQ_TTS_MODEL`.
- TTS-specific permission/billing errors: check Groq model permissions and spend limits because the Orpheus TTS models are listed as preview models.
- STT upload errors: retry with a normal spoken WAV/MP3 file and keep the file under the documented model file-size limit.
