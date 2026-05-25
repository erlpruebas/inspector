# Resumen del laboratorio de modelos

Este documento conserva la lectura operativa del laboratorio antes del cambio a modo `Codex one-shot`.

## Voz a texto

Decision actual:

- Principal: Groq `whisper-large-v3-turbo`.
- Fallback: transcripcion local con `faster-whisper`.

Motivo:

- Groq dio la mejor relacion entre velocidad, calidad y simplicidad operativa.
- El fallback local permite seguir trabajando si falla la API.

## Texto a voz

Decision actual:

- Principal: ElevenLabs `eleven_flash_v2_5`.
- Fallback/local: Kokoro ONNX.

Lectura:

- ElevenLabs Flash fue el mas rapido en las pruebas internas, con latencias cercanas a medio segundo en frases cortas.
- Kokoro funciona localmente, pero fue mucho mas lento en esta maquina.
- Para respuestas largas, el sistema envia texto completo y genera voz sobre un resumen de maximo dos parrafos. El usuario puede pedir `leeme la respuesta completa`.

## Modelos y runtime de trabajo

Resultados documentados:

- `benchmarks/results/office_strategy_report_20260521_with_groq.md`
- `benchmarks/results/orchestrator_decision_report_20260521.md`

Lectura principal:

| Rol | Candidato observado | Uso recomendado |
| --- | --- | --- |
| Mejor calidad | `codex:gpt-5.5` | Juez, escalado, tareas criticas |
| Trabajo diario con archivos | `codex:gpt-5.4-mini` | Base operativa del gestor |
| API directa fuerte | `openrouter:openai/gpt-5.4-mini` | Worker API si no hace falta terminal |
| Router rapido | `groq:qwen/qwen3-32b` | Clasificacion/decisiones si volvemos a cascadas |
| Clasificador ultrarrapido | `groq:llama-3.1-8b-instant` | Rutas muy simples |
| Runtime cloud candidato | `groq:groq/compound-mini` | Explorar, no default |
| Desktop visual | Codex Desktop | Solo si el usuario lo pide explicitamente |

## Conclusion estrategica

El laboratorio mostro que los wrappers API son utiles, pero no sustituyen al runtime agentico cuando hay archivos, comandos, verificacion y escritura en disco. Por eso el gestor se simplifica:

- default: Codex CLI en peticion unica
- excepcion explicita: Codex Desktop
- Telegram/Tkinter quedan como entradas y salidas, no como cerebros de decision complejos

