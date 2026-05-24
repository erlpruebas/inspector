@echo off
title Crear bots del laboratorio con Codex Desktop
cd /d "%~dp0"

echo Este comando tomara el control de Codex Desktop para pedir la creacion de 4 bots a BotFather.
echo Abre Codex Desktop antes de continuar y deja la sesion preparada.
pause

if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -m orchestrator_v2.desktop_codex_operator --botfather-lab --send
) else (
    python -m orchestrator_v2.desktop_codex_operator --botfather-lab --send
)

pause
