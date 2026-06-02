$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = "$root;$root\telegram_codex_orchestrator"

Push-Location "$root\telegram_codex_orchestrator"
try {
    @'
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from codex_discovery import discover_codex_executable

codex = discover_codex_executable()
if not codex:
    raise SystemExit("No se encontro un ejecutable Codex validado")

print(f"CODEX={codex}")

version = subprocess.run(
    [str(codex), "--version"],
    stdin=subprocess.DEVNULL,
    text=True,
    capture_output=True,
    timeout=30,
)
print(f"VERSION_RC={version.returncode}")
print((version.stdout or version.stderr).strip())
if version.returncode != 0:
    raise SystemExit(version.stderr)

with tempfile.TemporaryDirectory(prefix="agente_codex_cli_") as tmp:
    workdir = Path(tmp)
    output_file = workdir / "codex_probe.txt"
    prompt = "Crea un archivo codex_probe.txt con exactamente la palabra OK y responde solo HECHO."
    exec_result = subprocess.run(
        [
            str(codex),
            "--ask-for-approval",
            "never",
            "--sandbox",
            "danger-full-access",
            "--cd",
            str(workdir),
            "exec",
            "--json",
            "--skip-git-repo-check",
            prompt,
        ],
        stdin=subprocess.DEVNULL,
        text=True,
        capture_output=True,
        timeout=180,
    )
    print(f"EXEC_RC={exec_result.returncode}")
    print(exec_result.stdout[-1000:])
    if exec_result.returncode != 0:
        print(exec_result.stderr)
        raise SystemExit(exec_result.returncode)
    if not output_file.exists():
        raise SystemExit("Codex exec no creo codex_probe.txt")
    if output_file.read_text(encoding="utf-8", errors="replace").strip() != "OK":
        raise SystemExit("codex_probe.txt no contiene OK")

print("CODEX_CLI_AUDIT_PASS")
'@ | python -
}
finally {
    Pop-Location
}
