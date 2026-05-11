# Architecture

Este documento resume la arquitectura funcional del proyecto sin entrar en detalles de implementacion que puedan cambiar con frecuencia.

## Vision general

El proyecto tiene dos funciones principales:

1. Un orquestador de Telegram que recibe instrucciones, mantiene estado y ejecuta tareas con Codex CLI.
2. Una arena de benchmarks que compara varios motores bajo tareas sinteticas y guarda resultados reproducibles.

Ambas piezas comparten la misma filosofia: separar entrada, ejecucion, memoria y salida para que cada paso pueda auditarse despues.

## Bloques principales

### 1. Orquestador Telegram

Ruta: `telegram_codex_orchestrator/`

Responsabilidades:

- recibir mensajes y comandos;
- interpretar intenciones;
- lanzar Codex cuando corresponde;
- mantener memoria persistente;
- gestionar hilos de contexto, alarmas y tareas pendientes;
- ofrecer una GUI local para supervisar el estado.

Piezas relevantes:

- `orchestrator.py`: bucle principal y coordinacion.
- `gui.py`: interfaz Tkinter para control local.
- `intent.py`: interpretacion de comandos e intenciones.
- `memory.py`, `memories.py`, `pending_tasks.py`, `thread_store.py`: persistencia.
- `voice_state.py`, `speech_io.py`: soporte de voz.
- `telegram_api.py`: capa de comunicacion con Telegram.
- `codex_runner.py`: ejecucion de Codex CLI.

### 2. Arena de benchmarks

Ruta: `benchmarks/`

Responsabilidades:

- cargar tareas desde JSON;
- preparar carpetas de trabajo aisladas;
- ejecutar cada motor con el mismo input;
- registrar salidas, uso y costes si existen;
- comparar resultados y generar reportes.

Piezas relevantes:

- `benchmark_main.py`: entrada principal por linea de comandos.
- `multi_runner.py`: coordinacion de ejecuciones.
- `task_loader.py`: carga de tareas y assets.
- `engines/`: adaptadores para Codex, Gemini, OpenCode, Groq, OpenRouter, LM Studio y comandos genericos.
- `judge.py`: comparacion ciega entre dos salidas.
- `auto_judge.py`: evaluacion por pares dentro de una ejecucion.
- `report_generator.py`: informe Markdown de resultados.

### 3. Catalogo de tareas

Ruta: `benchmarks/tasks/`

El catalogo actual contiene 18 tareas sinteticas. Las pruebas cubren:

- extraccion de datos;
- redaccion asistida;
- agenda y seguimiento;
- limpieza y filtrado;
- comparacion de documentos y registros;
- tareas con archivos de soporte;
- casos con datos sucios y ambiguedad controlada.

### 4. Matriz de motores

La matriz activa combina distintos tipos de motor:

- CLIs agencicos: `codex`, `gemini`, `opencode`.
- Wrappers API: `groq`, `openrouter`, `gemini_api`, `lmstudio`.
- Comandos personalizados: `command`.

El objetivo no es solo medir calidad de respuesta. Tambien se mide si el motor puede trabajar en un flujo real de archivos y herramientas.

## Flujo de ejecucion

### Benchmark

1. El usuario lanza `benchmark_main.py`.
2. `multi_runner.py` crea un directorio de ejecucion.
3. `task_loader.py` copia los assets necesarios.
4. Cada engine procesa la tarea.
5. Se guarda la salida esperada y la informacion auxiliar.
6. Se generan reportes y resumenes.

### Orquestador

1. Telegram entrega un mensaje.
2. `intent.py` clasifica la intencion.
3. `orchestrator.py` decide la accion.
4. Si procede, `codex_runner.py` lanza la tarea.
5. El estado se persiste en memoria local.
6. La GUI refleja eventos y estado en tiempo real.

## Directorios de salida

- `benchmarks/results/`: ejecuciones terminadas.
- `telegram_codex_orchestrator/memory/`: memoria persistente local.
- `telegram_codex_orchestrator/runtime/`: voz y audio generados en tiempo de ejecucion.
- `logs/`: trazas de apoyo y archivos de diagnostico.

## Criterio de diseno

El proyecto separa claramente tres capas:

- configuracion;
- ejecucion;
- publicacion de resultados.

Eso permite que otra inteligencia artificial siga modificando el programa mientras la documentacion y los artefactos publicados siguen una version estable.
