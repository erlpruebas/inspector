@echo off
cd /d D:\inspector
if exist .venv\Scripts\python.exe (
  .venv\Scripts\python.exe -m model_probe %*
) else (
  python -m model_probe %*
)
