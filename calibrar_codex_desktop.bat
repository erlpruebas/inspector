@echo off
title Calibrar Codex Desktop
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -m orchestrator_v2.calibrate_codex_desktop
) else (
    python -m orchestrator_v2.calibrate_codex_desktop
)

pause
