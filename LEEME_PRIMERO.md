# LEE ME PRIMERO

Fecha: 2026-06-08

Este archivo es la puerta de entrada rapida al proyecto. Si entras en una
nueva conversacion, lee esto primero y luego sigue los enlaces que aparecen
abajo.

## Estado actual

- El repositorio mezcla codigo base estable con muchas rondas de evaluacion y
  artefactos generados.
- La rama local esta alineada con `origin/codex/orchestrator-v2-1-baseline`.
- No estamos en un buen punto para publicar todavia si queremos una entrega
  limpia: hay mucho trabajo experimental, benchmarks y salidas de prueba.
- La documentacion del router ya tiene una propuesta concreta de capacidades y
  un selector determinista, pero el router de produccion todavia no se ha
  sustituido.

## Que leer en orden

1. [agent_v2_2/docs/AUTONOMOUS_ROADMAP.md](./agent_v2_2/docs/AUTONOMOUS_ROADMAP.md)
2. [agent_v2_2/docs/DEVELOPMENT_JOURNAL.md](./agent_v2_2/docs/DEVELOPMENT_JOURNAL.md)
3. [README.md](./README.md)
4. [docs/ROUTER_CAPABILITY_MAP_20260608.html](./docs/ROUTER_CAPABILITY_MAP_20260608.html)
5. [docs/ROUTER_CAPABILITY_MASTER_20260608.md](./docs/ROUTER_CAPABILITY_MASTER_20260608.md)
6. [docs/EVOLUTIONARY_ROUTER_DESIGN_20260608.md](./docs/EVOLUTIONARY_ROUTER_DESIGN_20260608.md)
7. [docs/ANTIGRAVITY_REFACTOR_HANDOFF_20260608.md](./docs/ANTIGRAVITY_REFACTOR_HANDOFF_20260608.md)
8. [docs/ANTIGRAVITY_MASTER_PROMPT_20260608.md](./docs/ANTIGRAVITY_MASTER_PROMPT_20260608.md)
9. [docs/ROUTER_CAPABILITIES_GAIA_GAPS_20260607.md](./docs/ROUTER_CAPABILITIES_GAIA_GAPS_20260607.md)
10. [docs/HITL_EXCELLENCE_RESULTS_20260607.md](./docs/HITL_EXCELLENCE_RESULTS_20260607.md)
11. [agent_v2_2/docs/TASK_NORMALIZATION.md](./agent_v2_2/docs/TASK_NORMALIZATION.md)
12. [orchestrator_v2_1/README.md](./orchestrator_v2_1/README.md)
13. [orchestrator_v2_1/capability_catalog.json](./orchestrator_v2_1/capability_catalog.json)

## Resumen corto

- `README.md` explica el repositorio y el arranque general.
- `docs/ROUTER_CAPABILITY_MAP_20260608.html` presenta visualmente las
  capacidades, los ejemplos y las rutas E0-E20, una por herramienta.
- `docs/ROUTER_CAPABILITY_MASTER_20260608.md` es la fuente principal para el
  router: capacidades de las tareas, herramientas conocidas, tiempos,
  evidencia, limites y clases de ejecucion.
- `docs/EVOLUTIONARY_ROUTER_DESIGN_20260608.md` define cómo acumular
  experiencias, puntuar por capacidad y promover rutas con confianza.
- `docs/ANTIGRAVITY_REFACTOR_HANDOFF_20260608.md` especifica la construcción
  autocontenida de Agent 2.2, la cuota Codex, la auditoría y la publicación.
- `docs/ANTIGRAVITY_MASTER_PROMPT_20260608.md` contiene el prompt listo para
  entregar a Antigravity/Gemini.
- `docs/ROUTER_CAPABILITIES_GAIA_GAPS_20260607.md` resume la idea del router
  por capacidades concretas y los huecos detectados con GAIA local.
- `docs/HITL_EXCELLENCE_RESULTS_20260607.md` contiene la comparativa Gemini CLI
  3.1 Pro vs Codex 5.5.
- `agent_v2_2/docs/TASK_NORMALIZATION.md` explica el modelo normalizado de
  tareas y el comando `audit normalize`.
- `orchestrator_v2_1/README.md` describe el orquestador v2.1 y el modo
  desarrollo.
- `orchestrator_v2_1/capability_catalog.json` es el contrato legible por
  maquina para elegir herramientas.

## Regla importante

Cuando la transcripcion diga `Grok`, aqui se interpreta siempre como `Groq`
con Q.

## Nota de publicacion

Si vamos a publicar en GitHub, el corte correcto deberia ser:

1. decidir que artefactos de benchmarks se quieren conservar;
2. limpiar salidas temporales y archivos de laboratorio que no deban ir al
   repo;
3. dejar un resumen estable de la propuesta del router y de las conclusiones;
4. publicar cuando el arbol ya sea legible para otra persona.
