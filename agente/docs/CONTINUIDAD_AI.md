# Continuidad del proyecto Inspector

Fecha de referencia: 2026-06-03

Este documento es el punto de entrada para una IA que retome el trabajo en este repositorio después de un tiempo sin contexto.

## Qué hay ahora mismo

El proyecto es un agente Telegram que recibe mensajes, los clasifica y los despacha a Codex CLI o a Codex Desktop según la intención detectada. Además maneja:

- hilos de trabajo persistentes,
- memoria y cuaderno de eventos,
- alarmas,
- recuerdos persistentes,
- adjuntos de Telegram,
- voz saliente por TTS,
- transcripción de audio entrante por STT.

La parte importante de esta sesión es que la integración de escritorio ha sido restaurada como una capa real de ratón y teclado sobre la interfaz de Codex Desktop.

## Archivos clave

- `D:\inspector\agente\telegram_codex_orchestrator\orchestrator.py`
- `D:\inspector\agente\telegram_codex_orchestrator\telegram_api.py`
- `D:\inspector\agente\telegram_codex_orchestrator\speech_io.py`
- `D:\inspector\agente\telegram_codex_orchestrator\voice_state.py`
- `D:\inspector\agente\orchestrator_v2\desktop_codex_operator.py`
- `D:\inspector\agente\orchestrator_v2\desktop_calibration_store.py`
- `D:\inspector\agente\orchestrator_v2\codex_desktop_calibrator.py`
- `D:\inspector\agente\orchestrator_v2\calibrate_codex_desktop.py`

## Integración de escritorio restaurada

El operador de escritorio ya no es un stub. Recupera el enfoque histórico:

- localizar la ventana de Codex,
- darle foco,
- clicar en la interfaz con coordenadas calibradas,
- pegar el prompt por portapapeles,
- verificar el pegado,
- pulsar enviar,
- capturar pantalla de finalización,
- guardar metadatos de ejecución en un directorio de runtime.

El sistema soporta varios nombres de coordenadas por compatibilidad:

- `new_chat`
- `input_box`
- `initial_input`
- `browser_input`
- `send_button`
- `initial_send`
- `browser_send_stop`
- `initial_stop_no_browser`

Eso permite convivir con distintas calibraciones históricas sin romper la ejecución.

## Voz y audio

La salida hablada usa un resumen corto cuando el texto es largo. El resumen ahora:

- se genera con Gemini cuando hay API disponible,
- está limitado a un máximo aproximado de 80 a 120 palabras,
- se mantiene en dos párrafos como máximo,
- evita formato, listas y ruido visual.

La entrada de audio distingue entre:

- nota de voz nueva,
- audio reenviado,
- audio adjunto como documento.

En la telemetría del orquestador se registra si el audio venía reenviado y de qué tipo de origen venía.

## Estado operativo a tener en cuenta

No se deben lanzar pruebas reales de Codex Desktop desde una sesión de documentación si el sistema ya está siendo usado en vivo. Esa parte debe respetarse porque el operador puede estar ocupado.

En esta sesión no se ha ejecutado ninguna prueba real del escritorio; solo se ha restaurado el código y se ha dejado documentación de continuidad.

## Qué hacer a continuación

1. Revisar `orchestrator.py` y confirmar que el flujo de Telegram sigue apuntando al operador de escritorio restaurado.
2. Revisar que las dependencias de escritorio estén instaladas en la `venv`.
3. Confirmar que la calibración por máquina existe para el equipo actual.
4. Revisar el comportamiento del resumen de voz en mensajes largos.
5. Confirmar que la transcripción de audio entrante sigue funcionando con Groq Whisper y Gemini.
6. Si se va a seguir desarrollando, añadir más telemetría antes de tocar la lógica de decisión.

## Cómo debe leer esto una IA que retome el proyecto

La intención no es reescribir el sistema. La intención es continuar la misma línea:

- conservar la arquitectura actual,
- no introducir una nueva integración de escritorio inventada,
- respetar el modelo de trabajo por hilos,
- mantener la compatibilidad con los artefactos ya generados.

## Mensaje de arranque para la siguiente IA

> Ya tienes una integración de Telegram + Codex CLI + Codex Desktop reconstruida sobre la capa histórica de ratón y teclado. Empieza leyendo `telegram_codex_orchestrator/orchestrator.py`, `orchestrator_v2/desktop_codex_operator.py` y `orchestrator_v2/desktop_calibration_store.py`. No lances pruebas reales de escritorio si el sistema está en uso. Primero valida la documentación, luego revisa la configuración y después continúa por la parte de audio/voz y por el flujo de confirmaciones.

