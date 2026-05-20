# Chrome Gemini Nano Bridge

Este puente integra Gemini Nano de Chrome sin leer `weights.bin`. Usa la API oficial Built-in AI de Chrome mediante `LanguageModel`.

## Piezas

- `engines/chrome_nano_cli.py`: pseudo CLI para el benchmark.
- `engines/chrome_nano_server.py`: servidor local OpenAI-compatible.
- `engines/chrome_nano_bridge.py`: automatiza Chrome con Playwright y reutiliza una sesion de Prompt API.
- `engine_matrix_local_experimental.json`: matriz experimental local.
- `chrome_nano_opencode.example.json`: ejemplo de proveedor OpenCode.

## Instalacion

```powershell
python -m pip install playwright
```

No hace falta instalar Chromium de Playwright si se usa Chrome del sistema.

## Flags de Chrome

Habilita las Built-in AI APIs en Chrome. En versiones actuales suele requerir flags de Built-in AI / Prompt API / Gemini Nano en `chrome://flags`.

El puente lanza Chrome con:

```text
--enable-features=PromptAPIForGeminiNano,OptimizationGuideOnDeviceModel
```

Puedes cambiarlo con:

```powershell
$env:CHROME_NANO_FLAGS='--enable-features=PromptAPIForGeminiNano,OptimizationGuideOnDeviceModel'
```

## Probe

```powershell
python .\benchmarks\engines\chrome_nano_cli.py --health
```

Si devuelve `available` o `readily`, se puede probar inferencia.

## CLI

```powershell
python .\benchmarks\engines\chrome_nano_cli.py --prompt "Responde OK" --output resultado.md
```

## Servidor OpenAI-compatible

```powershell
python .\benchmarks\engines\chrome_nano_server.py --port 8787
```

Prueba:

```powershell
curl.exe http://127.0.0.1:8787/health
curl.exe http://127.0.0.1:8787/v1/models
curl.exe http://127.0.0.1:8787/v1/chat/completions -H "Content-Type: application/json" --data "{\"model\":\"gemini-nano\",\"messages\":[{\"role\":\"user\",\"content\":\"Responde OK\"}]}"
curl.exe http://127.0.0.1:8787/v1/chat/completions -H "Content-Type: application/json" --data "{\"model\":\"gemini-nano\",\"stream\":true,\"messages\":[{\"role\":\"user\",\"content\":\"Responde OK\"}]}"
curl.exe -X POST http://127.0.0.1:8787/v1/abort/REQUEST_ID
```

## Benchmark

```powershell
python .\benchmarks\benchmark_scheduler.py --tasks-file .\benchmarks\tasks\assistant_tasks.json --engine chrome-nano:gemini-nano --task test-01 --once --heuristic-only
```

## OpenCode

Copia/adapta `benchmarks/chrome_nano_opencode.example.json` a tu configuracion de OpenCode y arranca el servidor local antes de usar:

```powershell
opencode run --model geminiNanoLocal/gemini-nano "Responde OK"
```

## Limitaciones

- Gemini Nano no expone uso de tokens.
- Tool calling nativo no esta garantizado por la Prompt API.
- El streaming SSE se implementa como un proxy de `promptStreaming()`.
- `/v1/abort/:requestId` es best-effort y depende de que la sesion del navegador observe el `AbortSignal`.
- Para OpenCode puede servir como proveedor texto/OpenAI-compatible, pero no sera equivalente a Codex u OpenCode con modelos que soportan herramientas reales.
- Si `LanguageModel.availability()` devuelve `downloadable`, `downloading` o `unavailable`, el problema esta en Chrome/modelo/flags, no en el benchmark.
