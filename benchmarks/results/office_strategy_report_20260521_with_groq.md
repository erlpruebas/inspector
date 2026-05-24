# Office Strategy Benchmark Report - 2026-05-21 - With Groq

## Runs

- `benchmarks/results/20260521_113731_842340`: Codex, Gemini CLI, OpenCode.
- `benchmarks/results/20260521_134906_680642`: OpenRouter con clave valida.
- `benchmarks/results/20260521_145118_807909`: complemento OpenRouter.
- `benchmarks/results/20260521_154346_380586`: Groq con clave valida.
- `benchmarks/results/20260521_155000_771851`: complemento Groq.

## Executive Read

Ya hay comparativa real con Codex, Gemini CLI, OpenCode, OpenRouter y Groq sobre la misma muestra de 12 tareas de ofimatica. Todas las salidas utiles se juzgaron con `codex:gpt-5.5`.

`codex:gpt-5.5` sigue liderando calidad. `codex:gpt-5.4-mini` queda como mejor motor operativo diario. Entre proveedores API, destacan `openrouter:openai/gpt-5.4-mini`, `groq:qwen/qwen3-32b`, `openrouter:deepseek-r1` y `groq:openai/gpt-oss-120b`.

## Quality Ranking

| Engine | Outputs judged | Avg score | Pass rate |
|---|---:|---:|---:|
| `codex:gpt-5.5` | 11 | 7.91 | 91% |
| `codex:gpt-5.4-mini` | 12 | 7.42 | 83% |
| `openrouter:openai/gpt-5.4-mini` | 12 | 6.83 | 67% |
| `groq:qwen/qwen3-32b` | 9 | 6.78 | 67% |
| `openrouter:deepseek/deepseek-r1` | 12 | 6.75 | 58% |
| `groq:openai/gpt-oss-120b` | 12 | 6.58 | 58% |
| `gemini:gemini-2.5-flash` | 11 | 6.36 | 55% |
| `opencode:google/gemini-2.5-flash` | 9 | 6.33 | 56% |
| `openrouter:qwen/qwen3.6-plus` | 12 | 6.33 | 58% |
| `groq:meta-llama/llama-4-scout-17b-16e-instruct` | 12 | 6.08 | 50% |
| `openrouter:deepseek/deepseek-v4-flash` | 12 | 6.08 | 42% |
| `groq:openai/gpt-oss-20b` | 12 | 6.00 | 42% |
| `openrouter:meta-llama/llama-3.3-70b-instruct` | 12 | 5.92 | 42% |
| `groq:llama-3.3-70b-versatile` | 12 | 5.75 | 33% |
| `groq:llama-3.1-8b-instant` | 11 | 5.55 | 27% |
| `openrouter:openai/gpt-5.5` | 12 | 5.50 | 33% |

## Strategic Direction

1. `codex:gpt-5.5`: referencia premium y juez.
2. `codex:gpt-5.4-mini`: mejor candidato para asistente diario con archivos.
3. `openrouter:openai/gpt-5.4-mini`: mejor API externa de pago en esta muestra.
4. `groq:qwen/qwen3-32b`: sorpresa positiva; merece segunda ronda con mas tareas.
5. `openrouter:deepseek/deepseek-r1`: razonador solido por API.
6. `groq:openai/gpt-oss-120b`: buen candidato Groq para tareas razonadas.
7. `groq:openai/gpt-oss-20b`: util pero por debajo del 120b.
8. `opencode:google/gemini-2.5-flash`: runtime validado, pero aun no supera a CLI/API directa.

## Operational Notes

- Groq ya quedo habilitado y probado.
- OpenRouter ya quedo habilitado y probado.
- Los 429 de Groq se resolvieron con una pasada complementaria.
- `groq:qwen/qwen3-32b` tuvo algunos fallos tecnicos en tareas largas, pero las salidas validas puntuaron bien.
- Las respuestas de `openrouter:openai/gpt-5.5` por wrapper API quedaron por debajo de `codex:gpt-5.5`; esto confirma que no estamos midiendo solo el modelo, sino tambien el runtime y el contrato de ejecucion.

## Next Run

La siguiente ronda deberia concentrarse en los seis finalistas: `codex:gpt-5.5`, `codex:gpt-5.4-mini`, `openrouter:openai/gpt-5.4-mini`, `openrouter:deepseek/deepseek-r1`, `groq:qwen/qwen3-32b` y `groq:openai/gpt-oss-120b`.

