@echo off
title Inspector Orchestrator V2 Web
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -m orchestrator_v2.web_ui --open
) else (
    python -m orchestrator_v2.web_ui --open
)

pause
