# Runtime Codex one-shot

## Cambio de paradigma

El gestor deja de tratar cada mensaje como una conversacion larga con confirmacion intermedia. El flujo normal pasa a ser:

1. Recibe texto, voz o archivo desde Tkinter o Telegram.
2. Si hay voz, transcribe con Groq Whisper y fallback local.
3. Reune los archivos recientes del mismo origen/hilo.
4. Ejecuta una unica peticion con Codex CLI.
5. Devuelve el resultado final por texto y voz.

Cada mensaje se considera una peticion independiente. La memoria queda como registro y auditoria, no como hilo que haya que confirmar en cada paso.

## Ruta por defecto

El motor por defecto es Codex CLI:

```text
assistant/codex_runner.py --mode cli
```

Modelo por defecto:

```text
ASSISTANT_CODEX_MODEL=gpt-5.4-mini
```

Si la variable no existe, se usa `gpt-5.4-mini`, porque fue el mejor candidato operativo diario del laboratorio.

## Codex Desktop

Codex Desktop solo se usa cuando el usuario lo pide explicitamente con frases como:

- `quiero que lo ejecutes con Codex de escritorio`
- `usa Codex Desktop para...`
- `haz esto con Codex escritorio`

En ese caso se llama al operador visual existente:

```text
orchestrator_v2/desktop_codex_operator.py
```

## Archivos de Telegram

Todos los archivos recibidos por Telegram se guardan en:

```text
assistant/inbox/telegram/<chat_id>/<fecha>/
```

Tambien se registra un indice local:

```text
assistant/inbox/index.jsonl
```

Cuando llega una peticion, el gestor incluye automaticamente los archivos del mismo chat recibidos durante los ultimos minutos.

Configuracion:

```text
ASSISTANT_RECENT_FILE_MINUTES=10
```

Esto permite frases naturales como:

- `analiza lo que te acabo de enviar`
- `hazme un resumen del archivo adjunto`
- `convierte los ultimos documentos en una tabla`

## Salida

La respuesta completa se envia por texto. La voz usa el texto completo si es corto, o un resumen si supera dos parrafos o `TTS_MAX_CHARS`.

Comandos de voz:

- `configuracion eleven labs`
- `configuracion kokoro`
- `leeme la respuesta completa`

