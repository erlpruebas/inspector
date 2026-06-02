@echo off
title Calibrador Codex Desktop por equipo
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -m orchestrator_v2.codex_desktop_calibrator
) else (
    python -m orchestrator_v2.codex_desktop_calibrator
)

pause
