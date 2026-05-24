@echo off
title Preparar prompt BotFather para Inspector Lab
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -m orchestrator_v2.desktop_codex_operator --botfather-lab
) else (
    python -m orchestrator_v2.desktop_codex_operator --botfather-lab
)

pause
