# Persona Daily Simulation

Esta suite simula uso diario realista de un asistente por Telegram. No reemplaza a los 30 ejercicios ofimaticos; los complementa con continuidad, tono profesional y decision operativa por perfil.

## Perfiles

- Agente inmobiliaria
- Responsable informatico / DevOps
- Cientifica biomedica
- Ingeniero industrial
- Abogada laboralista
- Consultor financiero para pymes

Cada perfil tiene 6 mensajes sinteticos, de dificultad L2-L4, con `expected_keys`, skills y archivos locales asociados.

## Archivos

- `benchmarks/assets/persona_daily_simulation/personas.json`
- `benchmarks/assets/persona_daily_simulation/telegram_messages.jsonl`
- `benchmarks/assets/persona_daily_simulation/knowledge_base.md`
- `benchmarks/tasks/persona_daily_tasks.json`
- `benchmarks/results/persona_daily_simulation_strategy.html`
- `benchmarks/engine_matrix_persona_canary.json`

## Estrategia de pruebas

1. Baseline unico: correr las 36 tareas con `codex:gpt-5.4-mini`.
2. Canary multi-modelo: correr 6 tareas, una por profesion, con la matriz `engine_matrix_persona_canary.json`.
3. Escalado: repetir solo las tareas con nota baja usando `codex:gpt-5.5`.
4. Coste por tarea aprobada: comparar gasto estimado contra `score >= 8` y claves esperadas completas.

## Comandos utiles

Baseline completo:

```powershell
python .\benchmarks\benchmark_scheduler.py --tasks-file .\benchmarks\tasks\persona_daily_tasks.json --engine codex:gpt-5.4-mini --once
```

Canary multi-modelo por profesion:

```powershell
python .\benchmarks\benchmark_scheduler.py --tasks-file .\benchmarks\tasks\persona_daily_tasks.json --engine-matrix .\benchmarks\engine_matrix_persona_canary.json --task daily-01 --task daily-07 --task daily-13 --task daily-19 --task daily-25 --task daily-31 --once
```

Regenerar dataset:

```powershell
python .\benchmarks\generate_persona_daily_simulation.py
```
