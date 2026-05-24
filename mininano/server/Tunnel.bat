@echo off
setlocal EnableDelayedExpansion

cd /d "%~dp0"

set "PORT=8788"
set "SERVER_URL=http://127.0.0.1:%PORT%"

echo Mini Nano OpenAI-compatible server
echo.

if "%MINI_NANO_API_KEY%"=="" (
  echo AVISO: MINI_NANO_API_KEY no esta configurada.
  echo El servidor aceptara llamadas sin clave mientras este tunel este abierto.
  echo Para protegerlo, cierra esto y ejecuta antes:
  echo   set MINI_NANO_API_KEY=pon-una-clave-larga
  echo.
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r = Invoke-WebRequest -UseBasicParsing '%SERVER_URL%/health' -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } } catch { exit 1 }; exit 1" >nul 2>nul
if errorlevel 1 (
  echo Arrancando servidor local en %SERVER_URL% ...
  start "Mini Nano API Server" cmd /k ""%~dp0MiniNanoServer.bat""
  echo Esperando a que el servidor responda...
  for /L %%i in (1,1,30) do (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r = Invoke-WebRequest -UseBasicParsing '%SERVER_URL%/health' -TimeoutSec 1; if ($r.StatusCode -eq 200) { exit 0 } } catch { exit 1 }; exit 1" >nul 2>nul
    if not errorlevel 1 goto server_ready
    timeout /t 1 /nobreak >nul
  )
  echo No pude confirmar que el servidor este listo.
  echo Revisa la ventana "Mini Nano API Server".
  pause
  exit /b 1
)

:server_ready
echo Servidor listo: %SERVER_URL%
echo La pestana bridge debe quedar abierta en Chrome para ejecutar Gemini Nano.
echo.

set "CLOUDFLARED="
if exist "%~dp0cloudflared.exe" set "CLOUDFLARED=%~dp0cloudflared.exe"
if "%CLOUDFLARED%"=="" (
  for /f "delims=" %%p in ('where cloudflared 2^>nul') do (
    if "%CLOUDFLARED%"=="" set "CLOUDFLARED=%%p"
  )
)
if "%CLOUDFLARED%"=="" (
  for /f "delims=" %%p in ('dir /b /s "%LOCALAPPDATA%\Microsoft\WinGet\Packages\cloudflared.exe" 2^>nul') do (
    if "%CLOUDFLARED%"=="" set "CLOUDFLARED=%%p"
  )
)

if "%CLOUDFLARED%"=="" (
  echo No encuentro cloudflared.
  echo Instala Cloudflare Tunnel con:
  echo   winget install Cloudflare.cloudflared
  echo.
  echo Despues vuelve a ejecutar este Tunnel.bat.
  pause
  exit /b 1
)

echo Abriendo Cloudflare Tunnel hacia %SERVER_URL%
echo.
echo Cuando aparezca la URL https://....trycloudflare.com:
echo   1. Abrela desde otro ordenador para usar el chat web.
echo   2. Usa esa URL como Base URL en clientes compatibles OpenAI.
echo.
set "LOG_FILE=%~dp0cloudflared.log"
if exist "%LOG_FILE%" del "%LOG_FILE%" >nul 2>nul
echo Tambien guardo la salida en:
echo   %LOG_FILE%
echo.
start "Cloudflare Tunnel" cmd /k ""%CLOUDFLARED%" tunnel --logfile "%LOG_FILE%" --loglevel info --url "%SERVER_URL%""

echo Esperando URL publica de Cloudflare...
for /L %%i in (1,1,45) do (
  for /f "delims=" %%u in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "$p='%LOG_FILE%'; if (Test-Path $p) { $txt = Get-Content $p -Raw; $m = [regex]::Match($txt, 'https://[a-z0-9-]+\.trycloudflare\.com'); if ($m.Success) { $m.Value } }" 2^>nul') do (
    set "PUBLIC_URL=%%u"
  )
  if not "!PUBLIC_URL!"=="" goto tunnel_ready
  timeout /t 1 /nobreak >nul
)

echo No he encontrado la URL publica todavia.
echo Revisa la ventana "Cloudflare Tunnel" o abre el log:
echo   %LOG_FILE%
pause
exit /b 1

:tunnel_ready
echo.
echo URL publica lista:
echo   !PUBLIC_URL!
echo.
echo Chat web:
echo   !PUBLIC_URL!/chat
echo.
echo Base URL OpenAI-compatible:
echo   !PUBLIC_URL!/v1
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { [System.Net.Dns]::GetHostAddresses(([uri]'!PUBLIC_URL!').Host) ^| Out-Null; exit 0 } catch { exit 1 }" >nul 2>nul
if errorlevel 1 (
  echo AVISO: Windows no puede resolver esta URL con el DNS actual.
  echo.
  echo Intento aplicar automaticamente el arreglo local de hosts...
  call "%~dp0FixCurrentTunnelHosts.bat" /quiet
  echo.
)
start "" "!PUBLIC_URL!/chat"
echo Deja abierta la ventana "Cloudflare Tunnel" para mantener la URL activa.
pause
