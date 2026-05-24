@echo off
setlocal

net session >nul 2>nul
if not "%errorlevel%"=="0" (
  echo Este script necesita permisos de administrador.
  echo Se abrira una ventana elevada.
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

echo Cambiando DNS de adaptadores activos a Cloudflare y Google...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$adapters = Get-NetAdapter | Where-Object { $_.Status -eq 'Up' }; " ^
  "foreach ($a in $adapters) { " ^
  "  Write-Host ('Configurando: ' + $a.Name); " ^
  "  Set-DnsClientServerAddress -InterfaceIndex $a.ifIndex -ServerAddresses @('1.1.1.1','8.8.8.8') " ^
  "}; " ^
  "Clear-DnsClientCache; " ^
  "Write-Host 'DNS configurado. Prueba otra vez Tunnel.bat o TestTunnel.bat.'"

echo.
pause
