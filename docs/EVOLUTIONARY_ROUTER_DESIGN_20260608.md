# Router evolutivo basado en evidencia

Fecha: 2026-06-08

## Idea central

El router no debe aprender que una herramienta es "mejor" en general. Debe
aprender qué herramienta resuelve con calidad suficiente cada forma concreta
de tarea y cuánto tarda.

La unidad de experiencia es:

```text
herramienta x capacidades operativas x forma de tarea
```

Ejemplos de formas de tarea:

- recuperar un dato de memoria;
- buscar un dato web actual;
- hacer varias búsquedas y sintetizarlas;
- comparar dos archivos completos;
- leer una imagen y extraer campos;
- abrir una hoja de cálculo, filtrar y calcular;
- modificar un proyecto y ejecutar pruebas.

## Capacidades operativas

Cada capacidad debe tener uno de estos estados por herramienta:

- `direct`: la herramienta puede ejecutar la acción por sí misma;
- `prepared`: puede resolverla si otro componente le inyecta los datos;
- `unsupported`: no puede realizarla con la integración actual.

Esto evita confundir razonamiento con acceso. Un modelo API puede razonar muy
bien sobre una dirección inyectada, pero no por ello sabe buscarla en memoria
ni navegar por Internet.

## Ciclo de aprendizaje

1. El router describe la petición mediante capacidades operativas y requisitos
   cognitivos.
2. El selector elige la ruta compatible más rápida que ya tenga evidencia
   suficiente.
3. En modo evaluación se ejecutan también una o varias rutas desafiantes.
4. Se aplican comprobaciones objetivas: claves, cifras, citas, archivos,
   fórmulas, pruebas o formato.
5. Un juez ciego puntúa exactitud, completitud, ausencia de invenciones y
   utilidad.
6. En cambios importantes se usa un segundo juez y se conserva el desacuerdo.
7. Se guarda una experiencia conforme a
   `benchmarks/schemas/router_experience.schema.json`.
8. Se recalculan tasas de éxito, latencias y confianza por forma de tarea.
9. Una ruta desafiante solo sustituye a la actual cuando supera los umbrales
   con una muestra suficiente.

## Qué debe guardarse

- herramienta y versión;
- capacidades exigidas;
- forma de tarea;
- tiempo total;
- resultado de comprobaciones objetivas;
- notas de Gemini y Codex 5.5 cuando corresponda;
- respuesta del usuario: sí, parcial, no o demasiado lento;
- error, timeout o causa del fallo;
- versión del catálogo y del prompt.

No se debe guardar solamente una nota media global. Una herramienta puede ser
excelente leyendo PDF y mediocre investigando varias fuentes web.

## Selección y exploración

La producción usa una política conservadora:

```text
compatibilidad obligatoria
-> probabilidad de éxito suficiente
-> menor latencia demostrada
```

La exploración se hace sobre tareas sintéticas, tareas reproducibles o un modo
de evaluación explícito. No se deben duplicar silenciosamente todas las
peticiones reales del usuario, porque aumenta espera, consumo y exposición de
datos.

## Umbrales iniciales

- al menos 10 intentos por forma de tarea;
- al menos 80 % de comprobaciones objetivas superadas;
- nota media del juez de 7/10 o superior;
- dos jueces para promover cambios de alto impacto;
- ante desacuerdo, mantener la ruta actual y recoger más evidencia.

Estos valores son iniciales. Deben revisarse cuando exista una muestra mayor.

## Riesgos que hay que controlar

- sesgo o inestabilidad del juez;
- pruebas demasiado literales que penalicen respuestas correctas;
- mezclar resultados de baterías distintas como si fueran comparables;
- sobreajustar el router a las 25 tareas actuales;
- cambios de versión del modelo o proveedor;
- aprender de tareas reales sin anonimización o consentimiento.

## Estado actual

La infraestructura ya contiene gran parte del ciclo:

- arena de fuerza bruta;
- comprobaciones de claves esperadas;
- juez ciego Gemini;
- juez ciego Codex 5.5;
- `quality_winner`;
- `fastest_sufficient`;
- tiempos y resultados por ejecución.

Falta el agregador por capacidad y forma de tarea, la estimación de confianza
y la promoción automática versionada. Hasta entonces, el aprendizaje debe
generar recomendaciones revisables, no modificar directamente el router de
producción.
