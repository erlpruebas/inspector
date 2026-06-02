$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = "$root;$root\telegram_codex_orchestrator"
$env:ORCH_LAB_MODE = "1"
$env:ORCH_CODEX_SANDBOX = "danger-full-access"
$env:ORCH_CODEX_APPROVAL = "never"

Push-Location "$root\telegram_codex_orchestrator"
try {
    python .\test_bench_runner.py
}
finally {
    Pop-Location
}
