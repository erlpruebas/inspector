@echo off
title AI Arena Benchmark Scheduler 2h
cd /d "%~dp0"

set TASKS=benchmarks\tasks\assistant_tasks.json
set MATRIX=benchmarks\engine_matrix.json

if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe benchmarks\benchmark_scheduler.py --tasks-file "%TASKS%" --engine-matrix "%MATRIX%" --level L1 --cooldown-seconds 7200 --cycle-sleep-seconds 7200
) else (
    python benchmarks\benchmark_scheduler.py --tasks-file "%TASKS%" --engine-matrix "%MATRIX%" --level L1 --cooldown-seconds 7200 --cycle-sleep-seconds 7200
)

pause
