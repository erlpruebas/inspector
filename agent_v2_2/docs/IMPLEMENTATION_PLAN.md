# Refactorización a Inspector Agent 2.2

Este plan detalla la construcción de **Agent 2.2**, una versión limpia, portable y autocontenida del agente Inspector. Siguiendo las directrices del Master Prompt y el Handoff del 2026-06-08, el objetivo es mantener toda la funcionalidad útil histórica sin importar código directamente de las versiones anteriores (`orchestrator_v2_1/`, `orchestrator_v2/`, `telegram_codex_orchestrator/`), implementando un sistema robusto de paridad funcional comprobada, un enrutador evolutivo basado en capacidades y una gestión avanzada de cuota Codex.

## User Review Required

**Exclusiones de Funcionalidad**: Si alguna función histórica no encaja en el diseño nuevo y no puede ser mantenida ni siquiera mediante un adaptador claro, solicitaré explícitamente aprobación antes de excluirla, documentando la justificación de diseño.

**Modificaciones Destructivas**: Las versiones antiguas no deben ser modificadas (salvo actualización de `docs` o `.gitignore`), borradas o revertidas.

## Proposed Changes

### Fase 0. Inventario
- Analizar el sistema actual leyendo en profundidad la lista obligatoria.
- Identificar código reutilizable, datos sintéticos y ruido.
- Crear y aprobar este Plan de Implementación (actualmente en curso).

### Fase 1. Esqueleto Autocontenido
- Crear el paquete en `agent_v2_2/` con `pyproject.toml`, configuración (`config.py`), CLI y `.env.example`.
- Crear `agent_v2_2/docs/FUNCTIONAL_PARITY_MATRIX.md` cruzando funciones esperadas vs implementación 2.2.
- Añadir el catálogo operacional de capacidades y asegurar que se pueda hacer un smoke test instalando el paquete.

### Fase 2. Núcleo y Paridad Operativa
- Migrar y adaptar: Telegram, memoria, hilos, alarmas, cola de tareas pendientes, capacidades de voz (STT/TTS con Groq/Whisper, Gemini, Edge TTS) y altavoz local.
- Adaptar opciones de estado, privacidad (`clear`, `mixed`, `redacted`), confirmación humana y modo desarrollo aislando los componentes base de los proveedores.
- Validar paridad funcional en la matriz antes de considerar completo el bloque.

### Fase 3. Scheduler y Cuota
- Implementar una cola de tareas persistente capaz de sobrevivir a reinicios.
- Implementar el monitor de cuota Codex (`codex_rate_limits.py` lógico adaptado) para pausar ejecuciones Codex al alcanzar el umbral (≤25%) sin cancelar tareas en curso, permitiendo que Gemini, Groq, y otros procesos continúen.

### Fase 4. Arena y Jueces
- Migrar ejecutores (API, Gemini CLI, Codex CLI, OpenCode) detrás de interfaces limpias.
- Implementar métricas y evaluación: Comprobaciones objetivas, Juez habitual Gemini, Juez Codex 5.5 aplazable.
- Guardar esquema de experiencias (`router_experience.schema.json`).

### Fase 5. Auditoría de Cobertura
- Etiquetar las 25 tareas actuales y generar el informe de huecos de evaluación frente a los formatos exigidos (Docs, Audio, Web, etc).
- Generar tareas sintéticas para cubrir dichos huecos en suites (smoke, capability, slow/nightly, codex-only).

### Fase 6. Router Evolutivo
- Usar el catálogo de métricas (`herramienta x capacidad x forma de tarea`) para rutar llamadas hacia la herramienta más rápida, confiable y obligatoriamente compatible.

### Fase 7. Publicación
- Limpiar el entorno limitándose a `agent_v2_2`.
- Validar la batería completa de tests y paridad (incluyendo test integral de Telegram).
- Preparar los commits en la rama `gemini/agent-v2-2` y crear un Pull Request sin fusionarlo. Documentar el manual de reanudación y clonado en otro Windows.

## Verification Plan

### Automated Tests
- Ejecutar la batería de tests de `agent_v2_2/tests/` simulando respuestas de la API para no gastar cuota real (especialmente Codex).
- Validar persistencia de colas y scheduler con simulaciones temporales (snapshots falsos).
- Verificación mecánica del fichero `FUNCTIONAL_PARITY_MATRIX.md` (comprobando que todas las líneas tengan pruebas y estado finalizado).

### Manual Verification
- Lanzar `agent_v2_2/src/agent_v2_2/cli.py` en entorno Windows real.
- Comunicación "end-to-end" por Telegram verificando voz, texto, descargas, subidas, memoria y ejecución de código aislada.
- Verificar a mano que no se hayan expuesto tokens en los ficheros, logs o en la rama remota, usando auditoría de `git status` y `git diff` exhaustiva.
