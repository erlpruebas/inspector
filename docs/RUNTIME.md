# Runtime de Inspector

## Objetivo

Inspector funciona como gestor de escritorio. La web queda como laboratorio, no como interfaz principal.

La interfaz principal es `desktop_assistant.py`, una ventana Tkinter siempre visible con:

- boton `REC` para iniciar grabacion
- boton `STOP` para detener grabacion
- linea de estado
- caja de texto para enviar peticiones con `Enter`
- respuesta textual
- reproduccion de voz

## Estados

- `Listo`: esperando texto o grabacion
- `Grabando...`: el microfono esta capturando audio
- `Transcribiendo...`: se envia el audio a Gemini STT y, si falla, cae a Groq o fallback local
- `Procesando...`: el router interpreta intencion, memoria, hilo y herramienta
- `Generando voz...`: se sintetiza la respuesta con Kokoro o ElevenLabs
- `Alarma`: hay un aviso vencido
- `Error`: hubo un fallo recuperable

## Respuestas y voz

Las respuestas normales salen por el altavoz del ordenador y, si Telegram esta configurado, tambien por Telegram como texto completo mas audio.

Si una respuesta supera dos parrafos o el limite de voz configurado, el texto completo se envia escrito y la voz usa un resumen de maximo dos parrafos. Para forzar la lectura completa se puede decir:

- `leeme la respuesta completa`
- `no me resumas, leelo todo`
- `dame el audio completo`

## Arranque

```powershell
cd .\inspector
.\start_desktop.ps1
```

## Backend

El backend sigue siendo `server.js` porque centraliza Telegram, transcripcion, router, memoria, TTS y alarmas.

Endpoints usados por la ventana:

- `POST /api/assistant/transcribe`
- `POST /api/assistant/message`
- `POST /api/assistant/speech`
- `GET /api/assistant/alarms/due`
- `GET /api/assistant/state`

Las alarmas las vigila el backend con `ALARM_POLL_MS` (por defecto 5000 ms). El endpoint `/api/assistant/alarms/due` solo marca alarmas como entregadas si se llama con `?deliver=1`; el flujo normal lo hace el watcher interno del servidor.

## Archivos de estado

- `assistant/state.json`: memoria tecnica del gestor
- `assistant/alarms.md`: resumen legible de alarmas pendientes y entregadas
- `assistant/media/`: audios temporales

Estos archivos locales no se suben a Git cuando contienen estado vivo.
