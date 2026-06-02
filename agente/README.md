# Agente Telegram Codex Orchestrator

Version limpia y autocontenida del agente de `inspector`.

## Que incluye

- Orquestador Telegram + Codex CLI en `telegram_codex_orchestrator/`.
- Clasificador de intents con fallback local en espanol e ingles.
- Gestion de hilos, alarmas, recuerdos, inbox de adjuntos y ejecucion Codex.
- Reparador local seguro para errores simples de sintaxis Python antes de llamar a Codex.
- Bateria sintetica de 30 tareas con validaciones funcionales.

## Que queda fuera

- Credenciales y `.env`.
- Memorias/runtime generados.
- Workdirs temporales.
- `__pycache__`, logs y reportes antiguos.
- Operador completo de Codex Desktop. La version limpia conserva un shim y prioriza Codex CLI.

## Estructura

```text
agente/
  benchmarks/                     # token accounting local
  orchestrator_v2/                 # shim desktop opcional
  scripts/
    run_unit_tests.ps1
    run_bench.ps1
  telegram_codex_orchestrator/
    temp_bench_assets/             # fixtures de la bateria
    test_bench_runner.py
    test_python_repair.py
```

## Pruebas rapidas

```powershell
.\scripts\run_unit_tests.ps1
```

## Bateria final

```powershell
.\scripts\run_bench.ps1
```

El runner genera `test_bench_report.md`, `temp_bench_memory/` y `temp_bench_workdir/` dentro de `agente/`.

## Ejecucion del bot

Configura las variables necesarias en `agente/.env` o en el entorno:

```text
TELEGRAM_BOT_TOKEN=...
ORCH_TELEGRAM_ALLOWED_USER_ID=...
ORCH_CODEX_COMMAND=codex
ORCH_CODEX_SANDBOX=danger-full-access
ORCH_CODEX_APPROVAL=never
```

Despues ejecuta:

```powershell
cd .\telegram_codex_orchestrator
python .\orchestrator.py
```
