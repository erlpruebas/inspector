# Persona Intention Catalog

Catalogo de intenciones operativas que saldrian de notas de voz largas reales.

No intenta imitar la voz humana. Separa dos fases:

1. Captura de intencion desde nota larga real.
2. Resolucion de la tarea ya sintetizada.

Total tareas: 120

## Cobertura

- Abogada laboralista: 20 intenciones
- Agente inmobiliaria: 20 intenciones
- Cientifica biomedica: 20 intenciones
- Consultor financiero para pymes: 20 intenciones
- Ingeniero industrial: 20 intenciones
- Responsable informatico / DevOps: 20 intenciones

## Uso

```powershell
python .\benchmarks\benchmark_scheduler.py --tasks-file .\benchmarks\tasks\persona_intention_tasks.json --engine codex:gpt-5.4-mini --task intent-001 --once
```
