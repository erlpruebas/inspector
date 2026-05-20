# AI Arena Provider Matrix

Fecha de comprobacion local: 2026-05-11.

## Estado local

| Proveedor | Modo previsto | CLI local | API key local | Prueba real | Estado |
| --- | --- | --- | --- | --- | --- |
| Codex | CLI directo: `codex exec` | Si, `codex-cli 0.130.0-alpha.5` | Gestionada por Codex CLI, no por `OPENAI_API_KEY` | `codex exec --help` OK | Listo para benchmark CLI |
| Gemini CLI | CLI directo: `gemini -p` | Si, `0.41.2` | `GEMINI_API_KEY` presente | Benchmark real OK con `test-01` | Listo, usa `--skip-trust --approval-mode yolo` |
| OpenCode | CLI directo: `opencode run` | Si, `1.14.48` | `opencode auth login` o variables de entorno | Benchmark real OK con `test-01` | Ya disponible como engine agéntico separado |
| Groq | API wrapper compatible OpenAI | No hay CLI local | `GROQ_API_KEY` presente | Chat OK con headers explicitos | Listo como motor API |
| OpenRouter | API wrapper compatible OpenAI | No aplica | `OPENROUTER_API_KEY` presente | Chat OK, 13 tokens, coste reportado | Listo para benchmark API |
| Mini Nano remoto | API wrapper compatible OpenAI | No aplica | `BENCH_VIKING_NANO_API_KEY=local` por defecto | Pendiente de conectividad a `trycloudflare.com` | Listo para test de red |
| Gemini API | API wrapper REST | No aplica | `GEMINI_API_KEY` presente | Benchmark real OK leyendo assets | Listo como fallback al CLI |

## Modelos iniciales propuestos

| Proveedor | Modelo por defecto en la arena | Uso |
| --- | --- | --- |
| Codex | `gpt-5.5` y `gpt-5.4-mini` | Tareas de codigo, edicion de archivos, ofimatica con herramientas |
| Gemini CLI | `gemini-2.5-pro`, `gemini-2.5-flash`, `gemini-2.5-flash-lite` | Agente CLI comparable a Codex |
| Gemini API | `gemini-2.5-flash-lite`, configurable con `BENCH_GEMINI_API_MODEL` | Baseline barato API con lectura de assets |
| OpenCode | `openrouter/deepseek/deepseek-v3.2`, configurable con `BENCH_OPENCODE_MODEL` | Alternativa CLI multi-proveedor con permisos y `--format json` |
| Groq | `llama-3.1-8b-instant`, configurable con `BENCH_GROQ_MODEL` | Respuestas rapidas de texto/API; no debe modificar archivos salvo wrapper |
| OpenRouter | `deepseek/deepseek-v3.2`, configurable con `BENCH_OPENROUTER_MODEL` | DeepSeek coste/calidad con token/coste medible |
| Mini Nano remoto | `gemini-nano-local`, configurable con `BENCH_VIKING_NANO_MODEL` | Gemini Nano local expuesto por proxy OpenAI-compatible |
| Juez Gemini | `gemini-2.5-flash-lite`, configurable con `BENCH_JUDGE_MODEL` | Evaluacion ciega barata |
| LM Studio | `qwen3.5-0.8b:2`, configurable con `BENCH_LMSTUDIO_MODEL` | Modelo local en `http://127.0.0.1:1234/v1/chat/completions` |

## Scheduler

`benchmark_scheduler.py` permite ejecutar una matriz de modelos, diferir errores transitorios y reintentar mas tarde.

Ejemplo de ciclo cada dos horas:

```powershell
python .\benchmarks\benchmark_scheduler.py --tasks-file .\benchmarks\tasks\assistant_tasks.json --engine-matrix .\benchmarks\engine_matrix.json --level L1 --cooldown-seconds 7200 --cycle-sleep-seconds 7200
```

Tambien esta disponible `arrancar_benchmark_scheduler_2h.bat`.

## Reglas operativas

- Los CLIs que pueden tocar archivos son Codex, Gemini CLI y OpenCode.
- Los motores API puros, Groq, OpenRouter y Gemini API, no tienen herramientas locales por si mismos; usan wrappers que leen assets del workspace, llaman a la API y escriben el archivo esperado.
- OpenCode puede correr en modo no interactivo con `opencode run`, adjuntar archivos con `--file`, forzar JSON con `--format json` y afinar permisos con `permission` o `--dangerously-skip-permissions`.
- Groq requiere headers explicitos (`Accept: application/json` y `User-Agent`) para evitar `HTTP 403 / code 1010`.
- Mini Nano remoto usa el mismo wrapper OpenAI-compatible que Groq/OpenRouter/LM Studio, con `Authorization: Bearer local`.
- Para tareas con edicion real de carpetas, los API wrappers solo son comparables si se les da una capa adicional que convierta la respuesta del modelo en acciones controladas.
- Para costes, OpenRouter ya devuelve `usage.cost`; Groq deberia devolver `usage` si la autenticacion queda resuelta.
- La ejecucion se mantiene secuencial hasta que cada motor tenga un workspace totalmente aislado y nombres de salida prefijados.
