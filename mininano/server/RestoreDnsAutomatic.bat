@echo off
setlocal

net session >nul 2>nul
if not "%errorlevel%"=="0" (
  echo Este script necesita permisos de administrador.
  echo Se abrira una ventana elevada.
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

echo Restaurando DNS automatico en adaptadores activos...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$adapters = Get-NetAdapter | Where-Object { $_.Status -eq 'Up' }; " ^
  "foreach ($a in $adapters) { " ^
  "  Write-Host ('Restaurando: ' + $a.Name); " ^
  "  Set-DnsClientServerAddress -InterfaceIndex $a.ifIndex -ResetServerAddresses " ^
  "}; " ^
  "Clear-DnsClientCache; " ^
  "Write-Host 'DNS restaurado a automatico.'"

echo.
pause
