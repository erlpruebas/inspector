@echo off
title Consola de clicks Codex Desktop
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -m orchestrator_v2.codex_click_console
) else (
    python -m orchestrator_v2.codex_click_console
)

pause
