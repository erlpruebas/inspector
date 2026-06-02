$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = "$root;$root\telegram_codex_orchestrator"

Push-Location "$root\telegram_codex_orchestrator"
try {
    python -m unittest test_python_repair.py test_integration.py
}
finally {
    Pop-Location
}
