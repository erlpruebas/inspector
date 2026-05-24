@echo off
setlocal

cd /d "%~dp0"

set "ARGS="
if /I "%~1"=="mock" set "ARGS=--mock"
if /I "%~1"=="--mock" set "ARGS=--mock"

if exist "%~dp0python.exe" (
  "%~dp0python.exe" "%~dp0app.py" %ARGS%
  exit /b %errorlevel%
)

if exist "%~dp0python\python.exe" (
  "%~dp0python\python.exe" "%~dp0app.py" %ARGS%
  exit /b %errorlevel%
)

if exist "%~dp0venv\Scripts\python.exe" (
  "%~dp0venv\Scripts\python.exe" "%~dp0app.py" %ARGS%
  exit /b %errorlevel%
)

where py >nul 2>nul
if %errorlevel%==0 (
  py "%~dp0app.py" %ARGS%
  exit /b %errorlevel%
)

where python >nul 2>nul
if %errorlevel%==0 (
  python "%~dp0app.py" %ARGS%
  exit /b %errorlevel%
)

echo No encuentro Python. Instala Python o usa una version portable con python.exe junto a esta carpeta.
pause
