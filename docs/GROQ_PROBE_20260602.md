# Groq probe 2026-06-02

Objetivo: comprobar desde esta maquina si Groq puede usarse para:

- listar modelos;
- chat ligero;
- transcripcion STT;
- generacion TTS.

## Resultado actualizado

Veredicto operativo: Groq funciona desde esta maquina si las llamadas HTTP incluyen un `User-Agent` explicito. El fallo no era la clave: era el cliente `urllib` con su cabecera por defecto.

El orquestador queda corregido para enviar `User-Agent: inspector-orchestrator/1.0` en las llamadas Groq de STT y TTS.

## Prueba directa

Archivo de resultados:

- `model_probe/runs/groq_direct_probe_20260602_115803.json`

Resultados:

- `GET /openai/v1/models`: `HTTP 403`, `error code: 1010`
- `POST /openai/v1/chat/completions`: `HTTP 403`, `error code: 1010`
- `POST /openai/v1/audio/transcriptions`: `HTTP 403`, `error code: 1010`
- `POST /openai/v1/audio/speech`: `HTTP 403`, `error code: 1010`

## Prueba con model_probe

Carpeta de ejecucion:

- `model_probe/runs/20260602_120006_groq/`

Codex CLI preparo y ejecuto una prueba contra endpoints oficiales. En ese entorno, el fallo fue de conectividad local:

- `[WinError 10013] Intento de acceso a un socket no permitido por sus permisos de acceso`
- preflight TCP a `api.groq.com:443`: fallido

## Configuracion recomendada mientras falla

- STT principal: Gemini
- TTS principal: Gemini
- TTS fallback: Kokoro, Piper, Groq
- Groq queda guardado como fallback, no como proveedor principal.

## Configuracion recomendada si Groq vuelve a funcionar

- Chat ligero: `llama-3.1-8b-instant`
- STT: `whisper-large-v3-turbo`
- TTS: `canopylabs/orpheus-v1-english`
- Base URL: `https://api.groq.com/openai/v1`

Antes de activarlo como principal, repetir:

```bat
probar_modelo.bat run --provider groq --api-key-env GROQ_API_KEY --intent "comprobar modelos, chat ligero, STT y TTS"
```

Y confirmar que modelos, chat, STT y TTS devuelven respuesta correcta.

## Actualizacion 2026-06-02

Prueba con cabecera corregida:

- `GET /openai/v1/models`: OK
- `POST /openai/v1/chat/completions`: OK con `llama-3.1-8b-instant`
- `POST /openai/v1/audio/transcriptions`: OK con `whisper-large-v3-turbo`

La voz del orquestador se mantiene estrictamente en Gemini por decision operativa:

- `tts_backend`: `gemini`
- `tts_allow_fallback`: `false`

La transcripcion queda:

- `stt_backend`: `groq`
- fallback: `gemini`
