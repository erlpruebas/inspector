# Orchestrator V2 Architecture

Este documento deja fijada la arquitectura para poder pivotar de modelos, APIs y runtimes sin reescribir el sistema. La palabra estable es **herramienta**: cualquier forma de resolver una tarea.

## Objetivo

Construir un gestor que reciba peticiones por Telegram y por nota de voz local, rote cada tarea a la herramienta adecuada, mantenga memoria por usuario/hilo, devuelva texto y audio, y pueda ser evaluado por un laboratorio ciego multiusuario.

## Entradas

- Telegram: canal principal de peticiones y respuestas.
- Boton local de voz: boton azul abajo a la izquierda; al pulsar pasa a rojo y graba; al volver a pulsar guarda el audio, transcribe y manda la peticion al gestor.
- Panel web portable: interfaz de laboratorio, profesiones, resultados, comandos y voz desde navegador.
- CLI: entrada tecnica para pruebas y depuracion.
- Laboratorio ciego: usuarios/personas sinteticas que hablan por Telegram como clientes reales.

## Herramientas

Una herramienta puede ser:

- `api_directa`: Groq, OpenRouter u otra API compatible.
- `cli_agentico`: Codex CLI, Gemini CLI u otro agente local.
- `runtime_agentico`: OpenCode, Groq Compound u otro runtime con herramientas.
- `desktop_operator`: Codex Desktop controlado por raton/teclado para navegador, logins, apps visuales o BotFather.

La eleccion de modelos cambiara con el mercado. Por eso el router no debe depender de nombres de proveedores, sino de capacidades:

- Router rapido: clasificacion, intencion, privacidad, dificultad.
- API ligera: tareas cortas, extraccion simple, borradores rapidos.
- API razonadora: tareas medianas sin terminal.
- Runtime agentico: tareas con pasos, archivos, herramientas o terminal.
- Operador de escritorio: tareas autenticadas o visuales que ya funcionan bien en Codex Desktop.
- Experto premium: juez, escalado dificil, decisiones ejecutivas criticas.
- Contexto largo: Gemini cuando haya muchos archivos o documentos extensos.

## Decision actual

- Router equilibrado: `groq:qwen/qwen3-32b`.
- Router ultra rapido: `groq:llama-3.1-8b-instant`.
- Worker API fuerte: `openrouter:openai/gpt-5.4-mini`.
- Worker API barato: `openrouter:deepseek/deepseek-v3.2`.
- Runtime cloud: `groq:groq/compound-mini`.
- Runtime CLI externo: `opencode:openrouter/deepseek/deepseek-v3.2`.
- Contexto largo moderado: `gemini:gemini-2.5-flash`.
- Contexto largo fuerte: `gemini:gemini-2.5-pro`.
- Juez/escalado: `codex:gpt-5.5`.

## Voz

STT por defecto:

- Primario: Whisper local `large-v3` con `faster-whisper`.
- Fallback: Groq `whisper-large-v3-turbo`.

TTS:

- El sistema ya tiene piezas en `telegram_codex_orchestrator/speech_io.py` para Gemini, Groq, Kokoro y Piper.
- La respuesta completa siempre se entrega en texto por Telegram.
- La respuesta de voz se resume si supera dos parrafos o unos 900 caracteres.
- El resumen de audio apunta a unos 650 caracteres.
- El usuario puede pedir: `leeme la respuesta completa`.

## Configuracion conversacional

Frases como `vamos a configurar` activan un asistente de configuracion. Preguntas base:

- Nombre preferido.
- Nivel humano de conversacion, 0 a 5.
- Nivel de proactividad, 0 a 5.
- Horario permitido para mensajes no solicitados.
- Altavoz local encendido/apagado.
- Confirmacion obligatoria de ordenes por voz.
- Privacidad por defecto: `ask`, `redacted`, `mixed`, `clear`.
- Audio de respuesta siempre activo o no.

## Multiusuario y archivos

Cada usuario queda compartimentado:

- `runtime/users/{user_id}/threads/{thread_id}/inbox`
- `runtime/users/{user_id}/threads/{thread_id}/outbox`
- `runtime/users/{user_id}/memory`
- `runtime/users/{user_id}/config`

Esto permite recibir archivos, generar resultados y mantener memoria sin mezclar usuarios.

## Memoria

Memoria inmediata:

- `events.jsonl`: timestamp, peticion, respuesta, herramienta, resultado.
- `keyword_index.json`: palabra clave -> timestamps.

Memoria futura:

- Compactacion en ratos de descanso con un modelo ligero fiable.
- Memoria especifica por temas/personas/proyectos.
- Memoria procedimental: como se resolvieron tareas y que estrategia funciono mejor.

## Email

El modulo `email_gateway.py` deja lista la integracion SMTP/IMAP con clave de aplicacion:

- `EMAIL_SMTP_HOST`
- `EMAIL_SMTP_PORT`
- `EMAIL_IMAP_HOST`
- `EMAIL_IMAP_PORT`
- `EMAIL_USERNAME`
- `EMAIL_APP_PASSWORD`
- `EMAIL_SENDER`

Queda pendiente localizar en el disco D el proyecto antiguo donde ya funciono el envio/recepcion.

## Laboratorio ciego

La opcion recomendada es usar cuatro bots/cuentas reales de Telegram. Ventajas:

- Valida multiusuario real.
- Comprueba aislamiento de carpetas.
- Prueba concurrencia y gestion de hilos.
- No requiere meter nombres artificiales dentro del prompt.

Modo fallback:

- Un solo canal con nombres simulados.
- Util para pruebas baratas, pero no demuestra multiusuario real.

El laboratorio debe generar o cargar:

- Personas.
- Profesiones.
- Tareas.
- Archivos sinteticos.
- Respuestas esperadas.
- Evaluacion con motor de excelencia.

## Regla de escalado

El router empieza barato y rapido, pero escala cuando detecta:

- Datos sensibles.
- Muchos archivos.
- Contexto largo.
- Necesidad de terminal.
- Necesidad de herramientas externas.
- Riesgo ejecutivo alto.
- Incertidumbre o fallo de una herramienta anterior.

## Interfaces graficas

La experiencia visual principal vive en `orchestrator_v2/web_ui.py` y queda pensada para:

- configurar los 4 bots de Telegram;
- editar la profesion activa y sus tareas;
- lanzar corridas del laboratorio;
- revisar tablas de resultados y tokens;
- crear nuevas profesiones;
- enviar comandos al gestor;
- grabar y transcribir notas de voz desde el navegador.

El boton local de voz sigue existiendo para uso en escritorio, pero el panel web es el centro operativo portable.

## Codex Desktop Operator

`desktop_codex_operator.py` deja preparada la herramienta `desktop_codex_operator`.
Su primer uso practico es crear los cuatro bots del laboratorio mediante BotFather:

- `preparar_bots_lab_codex_desktop.bat`: genera el prompt y no toca la pantalla.
- `crear_bots_lab_codex_desktop.bat`: envia el prompt a Codex Desktop y espera captura final.

Esta herramienta queda reservada para casos donde una API o CLI no basta: sesiones autenticadas, navegador, descargas, interfaces web y operaciones con credenciales bajo supervision humana.
