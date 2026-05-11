# Inspector 0.1 - Setup para Windows 11
# Ejecutar en PowerShell con:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\setup.ps1

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Inspector 0.1 - Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Ir a la carpeta del script
Set-Location $PSScriptRoot

# Crear entorno virtual si no existe
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "Creando entorno virtual..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] No se pudo crear el entorno virtual. ¿Tienes Python instalado?" -ForegroundColor Red
        pause
        exit 1
    }
    Write-Host "Entorno virtual creado OK." -ForegroundColor Green
} else {
    Write-Host "Entorno virtual ya existe." -ForegroundColor Green
}

Write-Host ""
Write-Host "Instalando dependencias..." -ForegroundColor Yellow
.\.venv\Scripts\pip.exe install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Fallo al instalar dependencias." -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Instalacion completada." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Para arrancar el Inspector:" -ForegroundColor Cyan
Write-Host "  Opcion 1 (mas facil): doble clic en arrancar.bat" -ForegroundColor White
Write-Host "  Opcion 2 (PowerShell):" -ForegroundColor White
Write-Host "    .\.venv\Scripts\python.exe inspector_0_1.py" -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANTE:" -ForegroundColor Yellow
Write-Host "  - LM Studio debe estar corriendo con algun modelo de vision cargado." -ForegroundColor Yellow
Write-Host "  - El inspector detecta automaticamente el modelo activo." -ForegroundColor Yellow
Write-Host ""
pause
