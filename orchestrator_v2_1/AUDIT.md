# Auditoria profunda del gestor

Fecha: 2026-06-04

## Diagnostico

El sistema actual mezcla tres capas que deberian vivir separadas:

- `orchestrator_v2`: nucleo multi-tier, laboratorio, UI local, voz, web UI, gateway Telegram y operador Codex Desktop.
- `telegram_codex_orchestrator`: orquestador historico de Telegram con memoria, hilos, alarmas, escalado y su propia ruta Codex Desktop.
- `orchestrator_v2/runtime`: evidencias de ejecucion, capturas, calibraciones y resultados mezclados bajo la misma carpeta que el codigo.

## Problemas encontrados

- `orchestrator_v2/telegram_gateway.py` construye `TaskRequest(id=...)`, pero el modelo define `request_id` en v2.1 y no define `id` en v2. Esto rompe el gateway antes de ejecutar la tarea.
- Telegram parseaba texto humano (`Captura:` y `Tokens extraidos:`) para encontrar imagenes. Ese contrato es fragil y mezcla transporte con formato interno.
- Las capturas de Codex Desktop estaban conceptualmente cerca del ejecutor general. Deben ser un resultado exclusivo del adaptador Desktop.
- El router de `orchestrator_v2` manda tareas a Desktop por palabras clave generales. Para una version limpia conviene exigir ruta explicita o indicios visuales/autenticados claros.
- Hay dos modelos de tier: uno compacto en `orchestrator_v2` y otro mas amplio en `telegram_codex_orchestrator`. Ambos tienen valor, pero no deben crecer dentro del mismo nucleo.
- No se encontro `hitl_report.md` dentro de `D:\inspector`; si existe, esta fuera del workspace visible.

## Decision v2.1

Se crea `orchestrator_v2_1` como base limpia paralela.

Separacion:

- `models.py`: contratos estables (`TaskRequest`, `RouteDecision`, `OrchestratorResult`, `ResultAttachment`).
- `router.py`: politica de tier sin efectos secundarios.
- `executor.py`: ejecuta local/API/CLI y desconoce capturas.
- `desktop_adapter.py`: unica frontera con Codex Desktop y unica fuente de adjuntos de imagen.
- `telegram_gateway.py`: envia texto y adjuntos estructurados; no parsea strings internos.

## Migracion recomendada

1. Usar `orchestrator_v2_1` para nuevas pruebas de gestor.
2. Mantener `orchestrator_v2.desktop_codex_operator` como dependencia legacy temporal.
3. Mover calibradores y consola de clicks a un paquete `desktop_tools` si se estabilizan.
4. Portar memoria/hilos de `telegram_codex_orchestrator` solo cuando el nucleo v2.1 este validado.
5. No copiar `runtime` ni historiales dentro de la nueva version limpia.
