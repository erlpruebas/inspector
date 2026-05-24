# Office Strategy Benchmark Report

## Runs

- `D:\inspector\benchmarks\results\20260521_113731_842340`
- `D:\inspector\benchmarks\results\20260521_134906_680642`
- `D:\inspector\benchmarks\results\20260521_145118_807909`

## Executive Read

La prueba evaluo la capacidad de resolver tareas transversales de ofimatica con archivos, texto, agregacion y busqueda preparada. Las notas de calidad se fusionaron desde `codex:gpt-5.5` cuando hubo salida real.

Resultado practico: Codex CLI y Gemini CLI fueron los motores utiles en esta maquina; OpenCode funciona pero queda por debajo en esta muestra; OpenRouter quedo bloqueado casi por completo por credito insuficiente, aunque el canario con `max_tokens=128` dejo senal de DeepSeek V4 Flash y Llama 3.3 70B; Groq no pudo evaluarse porque falta `GROQ_API_KEY`.

## Quality On Successful Outputs

| Engine | Outputs judged | Avg score | Pass rate | Avg seconds | Notes |
|---|---:|---:|---:|---:|---|
| `codex_gpt_5_5` | 11 | 7.91 | 91% | 60.7 | strong file/task execution |
| `codex_gpt_5_4_mini` | 12 | 7.42 | 83% | 71.9 | strong file/task execution |
| `openrouter_openai_gpt_5_4_mini` | 12 | 6.83 | 67% | 5.4 | limited by current credits |
| `openrouter_deepseek_deepseek_r1` | 12 | 6.75 | 58% | 82.2 | limited by current credits |
| `openrouter_qwen_qwen3_6_flash` | 2 | 6.50 | 50% | 15.8 | limited by current credits |
| `gemini_gemini_2_5_flash` | 11 | 6.36 | 55% | 52.3 | good CLI baseline |
| `openrouter_qwen_qwen3_6_plus` | 12 | 6.33 | 58% | 63.2 | limited by current credits |
| `opencode_google_gemini_2_5_flash` | 9 | 6.33 | 56% | 30.2 | runtime works, needs tuning |
| `openrouter_deepseek_deepseek_v4_flash_free` | 3 | 6.33 | 67% | 15.6 | limited by current credits |
| `openrouter_deepseek_deepseek_v4_flash` | 12 | 6.08 | 42% | 12.0 | limited by current credits |
| `openrouter_meta_llama_llama_3_3_70b_instruct` | 12 | 5.92 | 42% | 38.1 | limited by current credits |
| `openrouter_openai_gpt_5_5` | 12 | 5.50 | 33% | 16.7 | limited by current credits |
| `openrouter_qwen_qwen3_6_35b_a3b` | 12 | 4.50 | 25% | 14.0 | limited by current credits |
| `openrouter_arcee_ai_trinity_large_thinking_free` | 12 | 4.00 | 17% | 10.4 | limited by current credits |
| `openrouter_arcee_ai_trinity_large_thinking` | 12 | 2.42 | 17% | 8.5 | limited by current credits |
| `openrouter_moonshotai_kimi_k2_6` | 12 | 2.08 | 8% | 35.3 | limited by current credits |
| `openrouter_x_ai_grok_4_3` | 12 | 0.00 | 0% | 12.5 | limited by current credits |

## Technical Availability

| Engine | Jobs | Success | Failed | Deferred | Main blocker |
|---|---:|---:|---:|---:|---|
| `codex_gpt_5_4_mini` | 12 | 12 | 0 | 0 | ok |
| `openrouter_arcee_ai_trinity_large_thinking` | 24 | 12 | 12 | 0 | OpenRouter credits/max_tokens |
| `openrouter_arcee_ai_trinity_large_thinking_free` | 12 | 12 | 0 | 0 | ok |
| `openrouter_deepseek_deepseek_r1` | 24 | 12 | 12 | 0 | OpenRouter credits/max_tokens |
| `openrouter_deepseek_deepseek_v4_flash` | 24 | 12 | 12 | 0 | OpenRouter credits/max_tokens |
| `openrouter_meta_llama_llama_3_3_70b_instruct` | 24 | 12 | 12 | 0 | OpenRouter credits/max_tokens |
| `openrouter_moonshotai_kimi_k2_6` | 24 | 12 | 12 | 0 | OpenRouter credits/max_tokens |
| `openrouter_openai_gpt_5_4_mini` | 24 | 12 | 12 | 0 | OpenRouter credits/max_tokens |
| `openrouter_openai_gpt_5_5` | 24 | 12 | 12 | 0 | OpenRouter credits/max_tokens |
| `openrouter_qwen_qwen3_6_35b_a3b` | 24 | 12 | 12 | 0 | OpenRouter credits/max_tokens |
| `openrouter_qwen_qwen3_6_plus` | 24 | 12 | 12 | 0 | OpenRouter credits/max_tokens |
| `openrouter_x_ai_grok_4_3` | 24 | 12 | 12 | 0 | OpenRouter credits/max_tokens |
| `codex_gpt_5_5` | 11 | 11 | 0 | 0 | ok |
| `gemini_gemini_2_5_flash` | 11 | 11 | 0 | 0 | ok |
| `opencode_google_gemini_2_5_flash` | 11 | 9 | 2 | 0 | runtime did not create output |
| `openrouter_deepseek_deepseek_v4_flash_free` | 12 | 3 | 9 | 0 | execution errors |
| `openrouter_qwen_qwen3_6_flash` | 34 | 2 | 32 | 0 | OpenRouter credits/max_tokens |
| `groq_llama_3_1_8b_instant` | 12 | 0 | 12 | 0 | missing GROQ_API_KEY |
| `groq_llama_3_3_70b_versatile` | 12 | 0 | 12 | 0 | missing GROQ_API_KEY |
| `groq_meta_llama_llama_4_scout_17b_16e_instruct` | 12 | 0 | 12 | 0 | missing GROQ_API_KEY |
| `groq_openai_gpt_oss_120b` | 12 | 0 | 12 | 0 | missing GROQ_API_KEY |
| `groq_openai_gpt_oss_20b` | 12 | 0 | 12 | 0 | missing GROQ_API_KEY |
| `groq_qwen_qwen3_32b` | 12 | 0 | 12 | 0 | missing GROQ_API_KEY |
| `opencode_groq_openai_gpt_oss_20b` | 11 | 0 | 11 | 0 | execution errors |
| `opencode_openrouter_deepseek_deepseek_v4_flash` | 11 | 0 | 11 | 0 | runtime did not create output |

## Strategic Conclusions

1. `codex:gpt-5.5` queda como referencia de calidad, pero no conviene usarlo como motor barato de rutina.
2. `codex:gpt-5.4-mini` queda como candidato fuerte para trabajo diario con archivos: hizo 12 salidas y mantuvo buena nota media.
3. `gemini:gemini-2.5-flash` por CLI es competitivo, pero conviene probarlo con mas tareas y ajustar tiempos.
4. `opencode:google/gemini-2.5-flash` funciona como runtime, pero necesita afinarse: falla mas y puntua por debajo en la muestra.
5. OpenRouter necesita corregir saldo/clave antes de sacar conclusiones sobre los modelos de pago; ahora mismo la API responde `402 Payment Required`.
6. Groq queda pendiente hasta configurar `GROQ_API_KEY`; todos sus fallos de esta corrida son de disponibilidad, no de calidad del modelo.

## Next Run

Repetir OpenRouter cuando la clave tenga credito suficiente, con `BENCH_OPENROUTER_MAX_TOKENS=768` para tareas normales y `1536` solo en tareas largas. Repetir Groq cuando exista `GROQ_API_KEY`. Mantener `codex:gpt-5.5` como juez y no como motor masivo salvo muestras pequenas.
