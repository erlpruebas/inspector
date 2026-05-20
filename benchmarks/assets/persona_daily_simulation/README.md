# Persona Daily Simulation

Dataset sintetico de mensajes tipo Telegram para evaluar un asistente diario multi-profesion.

Archivos:
- `personas.json`: seis perfiles profesionales.
- `telegram_messages.jsonl`: 36 mensajes entrantes, seis por persona.
- `knowledge_base.md`: contexto local que sustituye datos privados reales.

Tareas generadas:
- `benchmarks/tasks/persona_daily_tasks.json`

Uso recomendado:
```powershell
python .\benchmarks\benchmark_scheduler.py --tasks-file .\benchmarks\tasks\persona_daily_tasks.json --engine codex:gpt-5.4-mini --task daily-01 --once --heuristic-only
```
