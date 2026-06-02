# Model Probe

Aplicacion para investigar si un proveedor/modelo funciona para una intencion concreta.

El flujo es:

1. Recibe proveedor, clave e intencion.
2. Crea una carpeta en `model_probe/runs/`.
3. Lanza Codex CLI para estudiar documentacion oficial, escribir pruebas pequenas y ejecutarlas.
4. Usa Gemini para evaluar el reporte de Codex cuando hay clave disponible.
5. Guarda todos los artefactos de la ejecucion.

## Uso

Preferido, usando una variable de entorno o una clave ya guardada en `D:\credenciales`:

```bat
python -m model_probe run --provider groq --api-key-env GROQ_API_KEY --intent "comprobar modelos disponibles, STT y TTS"
```

Con modelo concreto:

```bat
python -m model_probe run --provider groq --api-key-env GROQ_API_KEY --model whisper-large-v3-turbo --intent "probar transcripcion de audio corto en espanol"
```

Con documentacion oficial de arranque:

```bat
python -m model_probe run --provider gemini --api-key-env GOOGLE_API_KEY --docs-url "https://ai.google.dev/gemini-api/docs" --intent "probar generacion de texto y latencia"
```

Tambien acepta `--api-key`, pero es mejor usar `--api-key-env` para no dejar claves en el historial de comandos.

## Artefactos

Cada ejecucion guarda:

- `request.json`: peticion sin secretos.
- `codex_prompt.md`: prompt enviado a Codex CLI.
- `codex_stdout.jsonl`: eventos JSON de Codex.
- `codex_stderr.txt`: errores del proceso Codex.
- `codex_report.md`: mensajes finales extraidos.
- `gemini_evaluation.md`: evaluacion de Gemini si esta disponible.
- `summary.md`: resumen operativo.

## Criterio

La decision final no se basa solo en si una llamada responde. Debe registrar:

- si la clave autentica;
- si el endpoint oficial responde;
- si el modelo existe;
- latencia observada;
- errores exactos;
- configuracion recomendada;
- siguiente accion si falla.
