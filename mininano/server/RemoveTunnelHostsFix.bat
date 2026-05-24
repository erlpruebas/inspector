@echo off
setlocal EnableDelayedExpansion

set "HOSTS_FILE=%SystemRoot%\System32\drivers\etc\hosts"

net session >nul 2>nul
if not "%errorlevel%"=="0" (
  echo Este script necesita permisos de administrador para editar hosts.
  echo Se abrira una ventana elevada.
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$hosts = '%HOSTS_FILE%'; " ^
  "$content = Get-Content $hosts -ErrorAction Stop; " ^
  "$out = New-Object System.Collections.Generic.List[string]; " ^
  "$skipNext = $false; " ^
  "foreach ($line in $content) { " ^
  "  if ($line -match 'MiniNano trycloudflare fix') { $skipNext = $true; continue } " ^
  "  if ($skipNext -and $line -match 'trycloudflare\.com') { $skipNext = $false; continue } " ^
  "  $skipNext = $false; $out.Add($line) " ^
  "}; " ^
  "$out | Set-Content -Path $hosts -Encoding ASCII; " ^
  "Clear-DnsClientCache; " ^
  "Write-Host 'Entrada temporal de MiniNano eliminada.'"

echo.
pause
