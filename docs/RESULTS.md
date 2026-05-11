# Results and publication

Este repositorio esta pensado para que los resultados sean faciles de revisar desde fuera.

## Que se considera un resultado

Una ejecucion de benchmark no es solo el texto final del modelo. Tambien incluye:

- la tarea exacta que se ejecuto;
- los archivos de entrada usados;
- la salida producida;
- el resumen de ejecucion;
- la informacion de uso o coste, cuando exista;
- el informe comparativo, si hubo mas de un motor.

## Estructura tipica

Las ejecuciones viven en `benchmarks/results/<run_id>/`.

Dentro de una ejecucion suelen aparecer:

- `summary.json`: resumen global del run.
- `report.md`: informe legible para humanos.
- `scheduler_state.json`: estado del planificador, si se uso.
- `<engine>_<task>_resultado.md`: salida final por motor y tarea.
- `expected_key_checks.json`: validaciones clave, cuando existan.
- `judgements.json`: comparaciones o veredictos entre motores, cuando existan.
- `work/`: copia del contexto de trabajo de cada motor.

## Que se publicara

Cuando un run se quiera compartir con la comunidad, lo ideal es publicar:

- el informe general en Markdown;
- los resumenes JSON;
- las salidas finales por tarea;
- los criterios de evaluacion;
- cualquier nota que explique limites o incidencias.

No se deben publicar secretos, claves API, archivos de estado privado ni caches locales.

## Recomendacion de versionado

Cada ronda publica un bloque independiente con un identificador de fecha y hora. Eso facilita:

- comparar una ejecucion con otra;
- rastrear mejoras;
- citar resultados concretos;
- evitar mezclar experimentos distintos.

## Como leer los resultados

1. Empieza por `report.md`.
2. Revisa `summary.json` si necesitas cifras o estados.
3. Abre la carpeta `work/` si quieres reproducir el contexto exacto.
4. Compara las salidas por motor para entender diferencias de calidad.

## Regla practica

Si un resultado no se puede explicar con un `README` y un `report.md`, entonces falta documentacion para publicarlo bien.
