@echo off
setlocal EnableDelayedExpansion

cd /d "%~dp0"

set "LOG_FILE=%~dp0cloudflared.log"
set "PUBLIC_URL="

if not exist "%LOG_FILE%" (
  echo No existe cloudflared.log.
  echo Ejecuta primero Tunnel.bat.
  pause
  exit /b 1
)

for /f "delims=" %%u in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "$txt = Get-Content '%LOG_FILE%' -Raw; $matches = [regex]::Matches($txt, 'https://[a-z0-9-]+\.trycloudflare\.com'); if ($matches.Count -gt 0) { $matches[$matches.Count - 1].Value }"') do (
  set "PUBLIC_URL=%%u"
)

if "%PUBLIC_URL%"=="" (
  echo No encuentro URL trycloudflare en cloudflared.log.
  pause
  exit /b 1
)

echo URL detectada:
echo   %PUBLIC_URL%
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8788/health' -TimeoutSec 5; Write-Host 'LOCAL OK:' $r.Content } catch { Write-Host 'LOCAL ERROR:' $_.Exception.Message; exit 1 }"
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "try { [System.Net.Dns]::GetHostAddresses(([uri]'%PUBLIC_URL%').Host) | ForEach-Object { Write-Host 'DNS Windows:' $_.IPAddressToString }; exit 0 } catch { Write-Host 'DNS Windows ERROR:' $_.Exception.Message; exit 2 }"
if errorlevel 2 (
  echo.
  echo Tu DNS de Windows no resuelve esta URL.
  echo Prueba primero FixCurrentTunnelHosts.bat como administrador.
  echo Si prefieres arreglar DNS globalmente, usa SetDnsCloudflare.bat como administrador.
  echo Mientras tanto, la API local sigue funcionando en:
  echo   http://127.0.0.1:8788/v1
  pause
  exit /b 2
)

echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r = Invoke-WebRequest -UseBasicParsing '%PUBLIC_URL%/health' -TimeoutSec 15; Write-Host 'REMOTE OK:' $r.Content } catch { Write-Host 'REMOTE ERROR:' $_.Exception.Message; exit 1 }"
echo.
echo Si REMOTE OK aparece arriba, abre:
echo   %PUBLIC_URL%/chat
pause
