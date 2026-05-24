# Office Strategy Benchmark Report - 2026-05-21

## Runs

- `benchmarks/results/20260521_113731_842340`: Codex, Gemini CLI, OpenCode y primera comprobacion de disponibilidad.
- `benchmarks/results/20260521_134906_680642`: OpenRouter con clave nueva.
- `benchmarks/results/20260521_145118_807909`: complemento de trabajos OpenRouter pendientes.

## Executive Read

La ronda valida ya incluye OpenRouter con credito operativo. Se ejecutaron 12 tareas mixtas de ofimatica con archivos, texto, agregacion y busqueda preparada. Las salidas reales se evaluaron con `codex:gpt-5.5` como juez unico.

Lectura corta: `codex:gpt-5.5` sigue siendo la referencia de calidad; `codex:gpt-5.4-mini` queda muy cerca y es mejor candidato para uso diario; en OpenRouter, `openai/gpt-5.4-mini`, `deepseek/deepseek-r1` y `qwen/qwen3.6-plus` son los candidatos mas interesantes de esta muestra. Groq sigue pendiente porque falta `GROQ_API_KEY`.

## Quality Ranking

| Engine | Outputs judged | Avg score | Pass rate |
|---|---:|---:|---:|
| `codex:gpt-5.5` | 11 | 7.91 | 91% |
| `codex:gpt-5.4-mini` | 12 | 7.42 | 83% |
| `openrouter:openai/gpt-5.4-mini` | 12 | 6.83 | 67% |
| `openrouter:deepseek/deepseek-r1` | 12 | 6.75 | 58% |
| `openrouter:qwen/qwen3.6-flash` | 2 | 6.50 | 50% |
| `gemini:gemini-2.5-flash` | 11 | 6.36 | 55% |
| `opencode:google/gemini-2.5-flash` | 9 | 6.33 | 56% |
| `openrouter:qwen/qwen3.6-plus` | 12 | 6.33 | 58% |
| `openrouter:deepseek/deepseek-v4-flash` | 12 | 6.08 | 42% |
| `openrouter:meta-llama/llama-3.3-70b-instruct` | 12 | 5.92 | 42% |
| `openrouter:openai/gpt-5.5` | 12 | 5.50 | 33% |
| `openrouter:qwen/qwen3.6-35b-a3b` | 12 | 4.50 | 25% |
| `openrouter:arcee-ai/trinity-large-thinking` | 12 | 2.42 | 17% |
| `openrouter:moonshotai/kimi-k2.6` | 12 | 2.08 | 8% |
| `openrouter:x-ai/grok-4.3` | 12 | 0.00 | 0% |

## Notes

- `openrouter:qwen/qwen3.6-flash` quedo limitado por `429`, asi que solo hay 2 salidas juzgadas.
- `openrouter:x-ai/grok-4.3` ejecuto tecnicamente, pero sus respuestas no cumplieron el contrato de salida en esta muestra.
- `openrouter:openai/gpt-5.5` rindio peor que `codex:gpt-5.5`; probablemente aqui estamos midiendo un wrapper API simple, no el comportamiento agente de Codex.
- `opencode:google/gemini-2.5-flash` funciona como runtime, pero fallo en algunas tareas por no crear salida esperada.
- OpenRouter consumio aproximadamente `0.88` creditos de los `5` disponibles tras estas rondas.

## Strategic Direction

1. Usar `codex:gpt-5.5` como juez y referencia premium.
2. Usar `codex:gpt-5.4-mini` como primera opcion operativa para tareas reales con archivos.
3. Mantener `openrouter:openai/gpt-5.4-mini` y `openrouter:deepseek/deepseek-r1` como candidatos de pago a segunda ronda.
4. Probar `openrouter:qwen/qwen3.6-plus` con mas tareas: parece razonable, pero no supera a Codex en esta muestra.
5. No priorizar por ahora `arcee-ai/trinity-large-thinking`, `moonshotai/kimi-k2.6` ni `x-ai/grok-4.3` para ofimatica transversal con este wrapper.
6. Repetir Groq cuando exista `GROQ_API_KEY`.

