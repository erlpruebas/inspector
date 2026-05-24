@echo off
setlocal EnableDelayedExpansion

cd /d "%~dp0"

set "LOG_FILE=%~dp0cloudflared.log"
set "HOSTS_FILE=%SystemRoot%\System32\drivers\etc\hosts"
set "PUBLIC_URL="
set "TUNNEL_HOST="
set "CLOUDFLARE_IP=104.16.230.132"
set "QUIET=0"
if /I "%~1"=="/quiet" set "QUIET=1"

if not exist "%LOG_FILE%" (
  echo No existe cloudflared.log. Ejecuta primero Tunnel.bat.
  if "%QUIET%"=="0" pause
  exit /b 1
)

for /f "delims=" %%u in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "$txt = Get-Content '%LOG_FILE%' -Raw; $matches = [regex]::Matches($txt, 'https://[a-z0-9-]+\.trycloudflare\.com'); if ($matches.Count -gt 0) { $matches[$matches.Count - 1].Value }"') do (
  set "PUBLIC_URL=%%u"
)

if "%PUBLIC_URL%"=="" (
  echo No encuentro una URL trycloudflare.com en cloudflared.log.
  if "%QUIET%"=="0" pause
  exit /b 1
)

for /f "delims=" %%h in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "([uri]'%PUBLIC_URL%').Host"') do (
  set "TUNNEL_HOST=%%h"
)

net session >nul 2>nul
if not "%errorlevel%"=="0" (
  echo Este script necesita permisos de administrador para editar hosts.
  echo Se abrira una ventana elevada.
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

echo Aplicando resolucion temporal:
echo   %CLOUDFLARE_IP% %TUNNEL_HOST%
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$hosts = '%HOSTS_FILE%'; " ^
  "$hostName = '%TUNNEL_HOST%'; " ^
  "$ip = '%CLOUDFLARE_IP%'; " ^
  "$content = Get-Content $hosts -ErrorAction Stop; " ^
  "$filtered = New-Object System.Collections.Generic.List[string]; " ^
  "$skipNext = $false; " ^
  "foreach ($line in $content) { " ^
  "  if ($line -match 'MiniNano trycloudflare fix') { $skipNext = $true; continue } " ^
  "  if ($skipNext -and $line -match 'trycloudflare\.com') { $skipNext = $false; continue } " ^
  "  $skipNext = $false; $filtered.Add($line) " ^
  "}; " ^
  "$filtered + (''), ('# MiniNano trycloudflare fix'), ($ip + ' ' + $hostName) | Set-Content -Path $hosts -Encoding ASCII; " ^
  "Clear-DnsClientCache; " ^
  "Write-Host 'Hosts actualizado. Abre de nuevo:'; " ^
  "Write-Host '%PUBLIC_URL%/chat'"

echo.
if "%QUIET%"=="0" pause
