@echo off
title Medidor XY del raton
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -m orchestrator_v2.mouse_coordinate_probe
) else (
    python -m orchestrator_v2.mouse_coordinate_probe
)

pause
