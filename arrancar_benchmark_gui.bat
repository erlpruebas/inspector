@echo off
title AI Arena Benchmark GUI
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe benchmarks\benchmark_gui.py
) else (
    python benchmarks\benchmark_gui.py
)

pause
