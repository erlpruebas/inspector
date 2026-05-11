@echo off
title Telegram Codex Orchestrator
cd /d "%~dp0"

set EXITCODE=75

:loop
echo ============================================================
echo   Telegram Codex Orchestrator
echo ============================================================
echo.

if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe telegram_codex_orchestrator\orchestrator.py
) else (
    python telegram_codex_orchestrator\orchestrator.py
)

set EXITCODE=%ERRORLEVEL%
echo.
echo Orquestador detenido con codigo %EXITCODE%.

if "%EXITCODE%"=="75" (
    echo Reinicio en caliente...
    timeout /t 2 /nobreak >nul
    goto loop
)

pause
