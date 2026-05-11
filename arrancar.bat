@echo off
title Inspector 0.1
echo ============================================================
echo   Inspector 0.1 - Vigilante de pantalla con Telegram
echo ============================================================
echo.

REM Ir a la carpeta del script
cd /d "%~dp0"

REM Comprobar que existe el entorno virtual
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Entorno virtual no encontrado.
    echo Ejecuta primero: python -m venv .venv
    echo Y luego: .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

echo Arrancando con el entorno virtual...
echo.
.venv\Scripts\python.exe inspector_0_1.py

echo.
echo Inspector detenido.
pause
