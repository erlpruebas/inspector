# Telegram Codex Orchestrator

MVP minimo para recibir ordenes por Telegram y ejecutarlas con Codex CLI.
Las ordenes pasan por una capa de interpretacion de intenciones: reglas locales primero y, si hace falta, un modelo sencillo de Google/Gemini.

## Comandos Telegram

- `C <instruccion>` ejecuta `codex exec`.
- `-c <instruccion>` alias compatible.
- `/c <instruccion>` alias compatible.
- `/status` muestra configuracion operativa.
- `/alarmas` lista alarmas activas.
- `/cancelar_alarma <id>` cancela una alarma.
- `/recuerdos` lista recuerdos guardados.
- `/hilos` lista hilos conversacionales.
- `/hilo` muestra el hilo activo.
- `/pendientes` lista tareas Codex pendientes.
- `/siguiente` ejecuta la siguiente tarea pendiente.
- `/limpiar_pendientes` borra la cola de pendientes.
- `/detener` cancela la tarea actual de Codex.
- `/nuevo_hilo <nombre>` crea y activa un hilo.
- `/usar_hilo <nombre>` cambia de hilo.
- `/directorios` lista carpetas extra que Codex puede usar.
- `/add_dir <ruta>` anade una carpeta extra a Codex.
- `/remove_dir <ruta>` quita una carpeta extra de Codex.
- `/reload` recarga variables de entorno.
- `/restart` reinicia si se usa el supervisor `arrancar_orquestador.bat`.
- `/voz` muestra estado de voz.
- `voz on` activa respuesta en texto y audio por Telegram.
- `voz off` deja solo respuesta en texto y apaga tambien `altavoz`.
- `altavoz on` activa `voz`, manda audio a Telegram y lo reproduce en la tarjeta de sonido del PC.
- `altavoz off` deja de reproducir en el PC, manteniendo el estado actual de `voz`.
- `usa voz groq`, `usa voz kokoro`, `usa voz piper` cambia el primer TTS a intentar.
- `voz api groq <clave>` guarda la clave en `D:\credenciales` y en `memory/voice_settings.json`.
- `voz modelo <modelo>` y `voz timbre <voz>` cambian modelo/voz del proveedor activo.

Tambien entiende peticiones de alarma en lenguaje natural:

- `avisame dentro de 15 minutos de poner la television`
- `ponme una alarma dentro de un minuto para revisar el correo`
- `recuerdame manana a las 9 que revise el correo`
- `todos los lunes a las 9 revisar agenda`
- `todos los dias a las 5 tomar medicacion`
- `todos los dias cinco tomar medicacion`
- `todos los meses dia 5 a las 9 revisar facturas`
- `recuerda que el wifi de casa se llama MiRed`
- `apunta para luego que el garaje se abre con el mando pequeno`
- `anade carpeta G:\Otros ordenadores\Main\D`
- `explorar G:\Otros ordenadores\Main\D`
- `abre un hilo nuevo sobre facturas`
- `cambia al hilo busquedas`
- `buscame informacion sobre IA`
- `que estas haciendo`
- `deten la tarea actual`
- `sigue con lo pendiente`

## Configuracion

Carga variables desde:

1. `D:\credenciales`
2. `D:\inspector\.env`
3. `D:\variables\.env`
4. `D:\inspector\telegram_codex_orchestrator\.env`

Para Google/Gemini, ademas inspecciona `D:\credenciales`: si existe una linea marcada como `use this .erlquimica GOOGLE_API_KEY=...`, esa clave tiene prioridad sobre las variables genericas.
Para Groq, lee `GROQ_API_KEY` desde `D:\credenciales` antes que `.env`.

Variables principales:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ALLOWED_USER_ID`
- `ORCH_CODEX_WORKDIR` opcional, por defecto `D:\inspector`
- `ORCH_CODEX_DIRS_FILE` opcional, por defecto `memory/codex_dirs.json`
- `ORCH_CODEX_EXTRA_DIRS` opcional, lista de rutas separadas por `;`
- `ORCH_CODEX_COMMAND` opcional, por defecto `codex`
- `ORCH_CODEX_MODEL` opcional
- `ORCH_CODEX_SANDBOX` opcional, por defecto `workspace-write`
- `ORCH_CODEX_APPROVAL` opcional, por defecto `never`
- `ORCH_CODEX_TIMEOUT_SECONDS` opcional, por defecto `1800`
- `ORCH_MEMORY_FILE` opcional, por defecto `memory/events.txt`
- `ORCH_MEMORIES_FILE` opcional, por defecto `memory/memories.txt`
- `ORCH_THREADS_FILE` opcional, por defecto `memory/threads.json`
- `ORCH_PENDING_TASKS_FILE` opcional, por defecto `memory/pending_tasks.json`
- `ORCH_ALARMS_FILE` opcional, por defecto `memory/alarms.json`
- `ORCH_VOICE_SETTINGS_FILE` opcional, por defecto `memory/voice_settings.json`
- `ORCH_VOICE_RUNTIME_DIR` opcional, por defecto `runtime/voice`
- `ORCH_ALARM_CHECK_SECONDS` opcional, por defecto `10`
- `ORCH_GOOGLE_INTENT_ENABLED` opcional, por defecto `1`
- `ORCH_GOOGLE_INTENT_MODEL` opcional, por defecto `GOOGLE_MODEL_ALT` o `gemini-2.5-flash-lite`
- `ORCH_GOOGLE_INTENT_TIMEOUT_SECONDS` opcional, por defecto `20`
- `ORCH_HOT_RELOAD` opcional, por defecto `1`
- `ORCH_DRAIN_PENDING_ON_START` opcional, por defecto `1`

## Memoria persistente

Todos los eventos se guardan en `memory/events.txt` con timestamp corto `aammddhhmmss`.
Las alarmas activas se guardan en `memory/alarms.json`.
Los recuerdos persistentes se guardan en `memory/memories.txt`.
Los hilos y sus `thread_id` de Codex se guardan en `memory/threads.json`.
Las tareas Codex pendientes se guardan en `memory/pending_tasks.json`.

Ejemplo:

```text
[260509153000] telegram_in source=telegram user_id=123 chat_id=123
C revisa el proyecto y dime el estado
```

## Arranque

Desde `D:\inspector`:

```bat
arrancar_orquestador.bat
```

Con interfaz grafica Tkinter:

```bat
arrancar_orquestador_gui.bat
```

La GUI muestra estado, eventos recientes, un boton para detener la tarea Codex actual y una linea para inyectar comandos como si llegaran por Telegram.
