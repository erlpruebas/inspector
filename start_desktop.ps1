$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
  Write-Host "Creando entorno Python local..."
  python -m venv (Join-Path $Root ".venv")
  & $Python -m pip install -r (Join-Path $Root "requirements.txt")
}

$listening = Get-NetTCPConnection -LocalPort 8787 -State Listen -ErrorAction SilentlyContinue
if (-not $listening) {
  Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c", "npm start" `
    -WorkingDirectory $Root `
    -WindowStyle Hidden
  Start-Sleep -Seconds 3
}

Start-Process -FilePath $Python `
  -ArgumentList (Join-Path $Root "desktop_assistant.py") `
  -WorkingDirectory $Root
