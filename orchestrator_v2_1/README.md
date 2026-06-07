# Orchestrator v2.1

Version limpia del gestor multi-tier.

Principios:

- El nucleo no sabe capturar pantalla.
- Las peticiones normales se clasifican con un router LLM que devuelve una decision estructurada.
- El tier elegido resuelve la peticion completa en lenguaje natural; el nucleo no contiene respuestas por palabras clave para estado, tiempo o memoria.
- Las reglas deterministas se limitan a transporte, privacidad, confirmaciones humanas, persistencia y overrides manuales.
- Los tiers API/CLI devuelven texto y archivos normales.
- Codex Desktop vive aislado en `desktop_adapter.py`.
- Solo `desktop_adapter.py` puede importar `orchestrator_v2.desktop_codex_operator`.
- Telegram consume `attachments` estructurados; no parsea textos tipo `Captura:`.

## Comandos

Listar herramientas:

```powershell
python -m orchestrator_v2_1 --list-tools
```

Ver ruta sin ejecutar:

```powershell
python -m orchestrator_v2_1 --route-only "audita este diseño"
```

Forzar Desktop en seco:

```powershell
python -m orchestrator_v2_1 --tool desktop_codex_operator "cd revisar navegador"
```

Enviar a Codex Desktop:

```powershell
python -m orchestrator_v2_1 --tool desktop_codex_operator --desktop-send "abre el navegador autenticado y revisa el estado"
```

Telegram:

```powershell
python -m orchestrator_v2_1.telegram_gateway
```

Notas:

- El gateway Telegram principal vive en `orchestrator_v2_1.telegram_gateway`.
- La memoria mínima persistente se guarda en `orchestrator_v2_1/runtime/memory/` en Markdown legible por humanos.
- Cada hilo guarda un diario bruto por dia en `raw/YYYY-MM-DD.md` y un `index.md` compacto por palabras.
- La compactacion manual se puede hacer con `MemoryStore.compact_thread(user_id, thread_id)`.
- Las confirmaciones humanas simples se manejan por `si` / `no` cuando la tarea es sensible o riesgosa.
- Las notas de voz se transcriben con Groq (`GROQ_API_KEY`).
- El audio-resumen usa Edge TTS por defecto para reducir la espera; Gemini permanece disponible como proveedor alternativo.
- ElevenLabs Flash v2.5 tambien esta integrado como proveedor seleccionable con las voces publicas Adam y George.
- El modo comparativo puede generar dos audios por respuesta, pero queda desactivado tras la evaluacion humana.
- La voz definitiva activa es Edge `es-ES-ElviraNeural`; ElevenLabs permanece integrado como alternativa desactivada.
- El audio-resumen se genera para respuestas de texto y voz, se envia a Telegram y se reproduce en el altavoz del ordenador.
- La configuracion persistente vive en `orchestrator_v2_1/runtime/voice_settings.json`; `generate_audio`, `play_audio`, `provider` y `voice_name` se pueden ajustar sin tocar el gateway.
- Las respuestas de hasta 700 caracteres pasan directamente a voz; solo los textos largos usan un segundo modelo para crear el resumen oral.
- Edge TTS se precalienta al arrancar el gateway para reducir la espera de la primera respuesta.
- Si no hay claves de voz, Telegram sigue respondiendo por texto y el flujo no se cae; solo se omite el audio-resumen.
- Telegram muestra tiempos compactos para transcripcion, enrutado, ejecucion, sintesis y lanzamiento de reproduccion, por ejemplo `3s`.
- El aviso de enrutado incluye el tier y el motor/modelo elegido.
- Cada respuesta completa termina con uso restante y reinicios, por ejemplo `70% 17.15 60% 25/3`.
- El primer porcentaje es lo que queda de la ventana Codex de cinco horas y va seguido de su hora local de reinicio.
- El segundo porcentaje es lo que queda de la ventana semanal y va seguido de su fecha local de reinicio.
- Los datos se leen mediante una unica instancia persistente de `codex app-server` y se actualizan en segundo plano, sin lanzar Codex en cada turno.
- Codex devuelve `usedPercent`; el gateway muestra el restante mediante `100 - usedPercent`. Si no existe un snapshot valido, no inventa valores ni muestra el pie.
- Las respuestas empiezan directamente por la informacion util, sin saludos de relleno ni reformulaciones de la pregunta.

## Modo desarrollo por Telegram

`activar modo desarrollo` cambia el chat a un circuito persistente de desarrollo controlado:

1. El usuario describe un cambio.
2. Codex CLI inspecciona una copia Git temporal y devuelve una propuesta.
3. `si` aprueba la propuesta; `no` la descarta; cualquier otro mensaje la modifica y genera una version nueva.
4. Una propuesta aprobada se implementa en un `git worktree` temporal con permisos limitados al workspace.
5. Al terminar, el controlador crea un commit, lo aplica a la rama activa y trata de publicarlo en `origin`.
6. Cada respuesta del modo desarrollo se entrega por texto, audio Edge en el movil y reproduccion en el altavoz.
7. La ultima linea de cada interaccion muestra el uso restante y los reinicios de Codex.
8. El modo permanece activo para encadenar la siguiente mejora.

`desactivar modo desarrollo` tiene prioridad en cualquier fase. Cancela el proceso Codex activo, elimina el entorno temporal y devuelve inmediatamente el chat al comportamiento normal.

El estado vive por chat en `orchestrator_v2_1/runtime/state/`. La propuesta usa un worktree desechable: incluso si Codex escribiera durante el analisis, esos cambios se eliminan y nunca llegan al proyecto principal. La implementacion usa `codex exec --sandbox workspace-write`, el sandbox nativo de Windows en modo `unelevated` y aprobaciones cerradas: cualquier operacion que necesite salir del workspace falla en lugar de escalar permisos.

Antes de publicar, el commit temporal se rebasa sobre el `HEAD` actual para incorporar cambios que hayan llegado mientras Codex trabajaba. Si Git aun detecta un conflicto, la rama y el commit de rescate se conservan y el detalle completo queda en `orchestrator_v2_1/runtime/development/failures.md`.

## Pruebas iniciales por Telegram

Empieza por estas cuatro, de lo más simple a lo más complejo:

1. `recuerda que mi casa esta en Calle Luna 12`
2. `que recuerdas de mi casa`
3. `hazme un resumen breve de lo que sabes de mi casa y cómo usarías ese dato`
4. Graba una nota de voz diciendo algo como `recuerda que mi casa esta en Calle Luna 12` y luego manda otra nota de voz con `como llego desde mi casa a la direccion del cliente`

Después puedes probar una acción sensible:

5. `borra la carpeta temporal`

## Pruebas de comportamiento real

1. Texto directo: `que tiempo hace hoy en Madrid`
2. Nota de voz: `resume en tres frases por que estamos construyendo este agente`
3. Memoria: `recuerda que mi casa esta en Calle Luna 12`
4. Recuperacion: `que recuerdas de mi casa`
5. Tier visual: `abre Google Maps y calcula como llegar desde mi casa a Plaza Mayor`
6. Confirmacion humana: `envia este resumen a un tercero`

En cada prueba deben aparecer el tier elegido y los tiempos de las etapas. Las respuestas correctas deben incluir texto, resumen de audio en Telegram y reproduccion por el altavoz.

## Politica Desktop

Codex Desktop es Tier 5 y se reserva para tareas visuales, autenticadas o explicitamente pedidas.
Las capturas no existen como concepto global del orquestador: son adjuntos de resultado producidos por el adaptador Desktop.
