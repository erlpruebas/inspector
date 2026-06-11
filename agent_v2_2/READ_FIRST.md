# Agent 2.2: leer primero

Este directorio contiene la version autocontenida del agente Inspector. No
depende de importar codigo de `orchestrator_v2_1`, `orchestrator_v2` ni
`telegram_codex_orchestrator`; esas versiones solo son fuente historica de
verdad funcional.

## Objetivo actual

Llegar a pruebas HITL reales desde Telegram con un router que elige la
herramienta compatible mas rapida respaldada por evidencia.

## Estado a 2026-06-11

- Paridad funcional: 35 de 35 filas completadas.
- Pruebas Agent 2.2: 64 aprobadas.
- Tareas auditadas: 362; fixtures invalidos: 0.
- Capacidades operativas juzgadas: 17 de 17.
- Pares herramienta-capacidad demostrados: 56 de 56.
- Gate HITL: aprobado en local y en un workspace limpio.
- Router evolutivo: activado; 35 de 35 puntos de madurez.

## Orden de lectura

1. `docs/AUTONOMOUS_ROADMAP.md`
2. `docs/FUNCTIONAL_PARITY_MATRIX.md`
3. `docs/TASK_AUDIT_20260611.md`
4. `docs/DEVELOPMENT_JOURNAL.md`
5. `docs/CAPABILITY_CONTRACT.md`
6. `docs/TOOL_CATALOG.md`

## Comandos de comprobacion

```powershell
$env:PYTHONPATH='agent_v2_2/src;.'
python -m pytest agent_v2_2/tests -q
python -m agent_v2_2.cli audit tasks
python -m agent_v2_2.cli audit training
python -m agent_v2_2.cli evolution readiness
python -m agent_v2_2.cli status
```

## Siguiente accion

Iniciar la validacion humana desde Telegram con `iniciar bateria`. Durante la
sesion se puede usar `prueba siguiente`, `repetir prueba`, `correccion: ...` y
`friccion: baja|media|alta`.
