# Especificacion Tecnica: AI Arena Benchmark

## Contexto actual
El sistema base utiliza un orquestador en Python que lanza procesos externos mediante `subprocess.Popen`. Actualmente, el bot operativo soporta `codex exec` con sandboxing delegado al Codex CLI.

## Objetivo
Crear una arena de evaluacion comparativa que ejecute una lista de tareas sinteticas sobre multiples motores de IA y califique su desempeno sin acoplarse al flujo de Telegram.

## Decisiones de diseno
- Los resultados se guardan con prefijo por motor y tarea: `motor_tareaID_nombre.ext`.
- La ejecucion inicial es secuencial para evitar colisiones de escritura en `D:\inspector`.
- Se registra coste y tokens cuando el motor pueda devolverlos.
- No se usa LangGraph ni LangChain en esta fase.
- El sandbox por defecto para Codex es `workspace-write`.

## Componentes

### Cargador de tareas
`benchmarks/task_loader.py` lee `benchmarks/tasks/tasks.json`, copia los archivos requeridos desde `benchmarks/assets` y prepara un directorio de trabajo aislado por motor y tarea.

### Runner multi-motor
`benchmarks/multi_runner.py` ejecuta motores definidos en `benchmarks/engines/engine_factory.py`.

Motores iniciales:
- `codex`: ejecuta `codex exec`.
- `gemini`: ejecuta un comando Gemini CLI configurable con `BENCH_GEMINI_COMMAND_TEMPLATE`.
- `opencode`: ejecuta `opencode run` configurable con `BENCH_OPENCODE_COMMAND_TEMPLATE`.
- `command`: ejecuta comandos genericos de sistema.
- `groq`: llama a `api_wrapper.py` contra la API de Groq.
- `openrouter`: llama a `api_wrapper.py` contra OpenRouter.

### Juez
`benchmarks/judge.py` usa Gemini via API REST para comparar dos salidas de una misma tarea y devolver JSON con `winner`, `score_a`, `score_b` y `reasoning`.

### Reportes
`benchmarks/report_generator.py` convierte los JSON de resultados en un informe Markdown comparativo.

### Evaluacion automatica
`benchmarks/auto_judge.py` compara por pares las salidas de varios motores dentro de un mismo `run_dir` usando Gemini API como juez ciego.

## Uso rapido

```powershell
python .\benchmarks\benchmark_main.py --engine codex
python .\benchmarks\benchmark_main.py --engine groq --engine codex
python .\benchmarks\judge.py --task resumen_ejecutivo --a .\benchmarks\results\...\a.txt --b .\benchmarks\results\...\b.txt
python .\benchmarks\report_generator.py
python .\benchmarks\auto_judge.py --run-dir .\benchmarks\results\<run_id>
```

## Nota Git
La rama objetivo es `feature/benchmark-coliseum`, pero `D:\inspector` no contiene `.git` en el momento de crear esta especificacion. Cuando el proyecto este dentro de un repositorio:

```powershell
git checkout -b feature/benchmark-coliseum
```
