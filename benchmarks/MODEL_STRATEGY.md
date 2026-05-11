# Model Strategy

Fecha de revision: 2026-05-11.

## Matriz activa

| Grupo | Engine spec | Tipo | Uso previsto |
| --- | --- | --- | --- |
| Codex | `codex:gpt-5.5` | CLI agente | Maxima calidad para tareas dificiles, edicion y ejecucion |
| Codex | `codex:gpt-5.4-mini` | CLI agente | Baseline Codex mas barato/rapido |
| Gemini CLI | `gemini:gemini-2.5-pro` | CLI agente | Razonamiento alto y tareas largas |
| Gemini CLI | `gemini:gemini-2.5-flash` | CLI agente | Equilibrio calidad/coste/latencia |
| Gemini CLI | `gemini:gemini-2.5-flash-lite` | CLI agente | Baseline rapido y barato |
| OpenRouter | `openrouter:deepseek/deepseek-v4-flash` | API wrapper | DeepSeek muy barato/rapido para volumen |
| OpenRouter | `openrouter:deepseek/deepseek-v3.2` | API wrapper | DeepSeek principal de eficiencia coste/calidad |
| OpenRouter | `openrouter:deepseek/deepseek-v3.2-speciale` | API wrapper | Variante DeepSeek mas fuerte para tareas agenticas |
| Groq | `groq:llama-3.1-8b-instant` | API wrapper | Ultra rapido y barato; tareas simples |
| Groq | `groq:openai/gpt-oss-20b` | API wrapper | Razonamiento/coding barato con mas capacidad |
| Local | `lmstudio:qwen3.5-0.8b:2` | API wrapper local | Baseline offline/local sin coste externo |

## Integracion

`codex:*` y `gemini:*` se lanzan como programas de linea de comandos mediante `CommandEngine` o `CodexEngine`. Son agentes completos: pueden leer archivos, ejecutar comandos y corregir errores dentro del workspace preparado por el benchmark.

`openrouter:*`, `groq:*` y `lmstudio:*` se lanzan mediante `engines/api_wrapper.py`. Estas APIs son modelos de chat, no agentes completos. El wrapper les da una interfaz uniforme: lee los archivos del directorio de trabajo, llama al modelo y escribe el archivo de salida esperado. Esto es suficiente para tareas de ofimatica, extraccion, resumen, CSV, ICS y redaccion.

Para tareas que exijan bucles reales de programacion, ejecucion de tests o edicion multiarchivo, los API wrappers no equivalen todavia a Codex/Gemini CLI. La siguiente evolucion seria un `agentic_api_wrapper.py` con bucle: planificar, escribir archivo, ejecutar comando permitido, leer error, corregir y repetir con limite de pasos.

## Comandos utiles

```powershell
python .\benchmarks\benchmark_main.py --tasks-file .\benchmarks\tasks\assistant_tasks.json --engine codex:gpt-5.5 --task test-01
python .\benchmarks\benchmark_main.py --tasks-file .\benchmarks\tasks\assistant_tasks.json --engine codex:gpt-5.4-mini --task test-01
python .\benchmarks\benchmark_main.py --tasks-file .\benchmarks\tasks\assistant_tasks.json --engine gemini:gemini-2.5-flash --task test-01
python .\benchmarks\benchmark_main.py --tasks-file .\benchmarks\tasks\assistant_tasks.json --engine openrouter:deepseek/deepseek-v3.2 --task test-01
python .\benchmarks\benchmark_main.py --tasks-file .\benchmarks\tasks\assistant_tasks.json --engine groq:openai/gpt-oss-20b --task test-01
```

Scheduler con descansos:

```powershell
python .\benchmarks\benchmark_scheduler.py --tasks-file .\benchmarks\tasks\assistant_tasks.json --engine-matrix .\benchmarks\engine_matrix.json --level L1 --cooldown-seconds 7200 --cycle-sleep-seconds 7200
```
