@echo off
setlocal

cd /d "%~dp0"

if exist "%~dp0python.exe" (
  "%~dp0python.exe" "%~dp0DiagnoseApi.py" %*
  pause
  exit /b %errorlevel%
)

if exist "%~dp0python\python.exe" (
  "%~dp0python\python.exe" "%~dp0DiagnoseApi.py" %*
  pause
  exit /b %errorlevel%
)

if exist "%~dp0venv\Scripts\python.exe" (
  "%~dp0venv\Scripts\python.exe" "%~dp0DiagnoseApi.py" %*
  pause
  exit /b %errorlevel%
)

where py >nul 2>nul
if %errorlevel%==0 (
  py "%~dp0DiagnoseApi.py" %*
  pause
  exit /b %errorlevel%
)

where python >nul 2>nul
if %errorlevel%==0 (
  python "%~dp0DiagnoseApi.py" %*
  pause
  exit /b %errorlevel%
)

echo No encuentro Python. Instala Python o deja python.exe junto a esta carpeta.
pause
