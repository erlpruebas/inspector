@echo off
title Inspector Orchestrator GUI
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe telegram_codex_orchestrator\gui.py
) else (
    python telegram_codex_orchestrator\gui.py
)

pause
