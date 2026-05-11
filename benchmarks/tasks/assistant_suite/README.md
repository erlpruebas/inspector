# Assistant Synthetic Benchmark

Este paquete contiene 30 ejercicios sinteticos de asistencia digital adaptados a la arquitectura actual del proyecto.

## Mapeo

- Recursos compartidos: `benchmarks/assets/assistant_synthetic/`
- Ejercicios: `benchmarks/tasks/assistant_suite/test-XX/`
- Cada `test-XX` contiene solo:
  - `task.md`
  - `metadata.json`
- Version ejecutable por el runner: `benchmarks/tasks/assistant_tasks.json`

## Regenerar

```powershell
python .\benchmarks\generate_assistant_suite.py
python .\benchmarks\assistant_suite_to_tasks.py
```

## Ejecutar

```powershell
python .\benchmarks\benchmark_main.py --tasks-file .\benchmarks\tasks\assistant_tasks.json --engine gemini_api --task test-01
python .\benchmarks\expected_key_check.py --run-dir .\benchmarks\results\<run_id> --tasks-file .\benchmarks\tasks\assistant_tasks.json
```
