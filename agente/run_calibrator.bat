@echo off
cd /d "%~dp0"
echo Lanzando el calibrador de Codex Desktop...
..\.venv\Scripts\python.exe -m orchestrator_v2.codex_desktop_calibrator
pause
