# Auditoria de tareas y capacidades

Fecha: 2026-06-11

## Resultado

- 362 tareas parseadas y normalizadas.
- 0 archivos requeridos ausentes o con firma invalida.
- 17 de 17 capacidades operativas cubiertas por juicio valido.
- 13 familias de formato cubiertas: audio, codigo, CSV, correo, imagen, JSON,
  JSONL, Markdown, Office, PDF, texto, web y ZIP.
- 31 tareas requieren red.
- 31 formas de tarea aparecen en la experiencia aprendida.

## Lectura correcta de los metadatos heredados

La bateria contiene 226 tareas sin nivel editorial explicito y 33 sin categoria
de origen. Esto no implica que carezcan de contrato operativo: el normalizador
deriva accesos, archivos, operacion, capacidad primaria, garantias y
herramientas compatibles desde la peticion y los fixtures.

Estos campos heredados no se usaran para elegir herramienta. La seleccion usa
el contrato canonico y la matriz de evidencia.

## Cobertura operativa

La bateria representa:

- extraccion puntual, larga y cruzada;
- lectura de PDF binario, imagen, audio, tablas, Office y ZIP;
- comparacion, calculo, filtrado, transformacion y redaccion;
- creacion o modificacion de artefactos;
- diagnostico y ejecucion tecnica;
- verificacion;
- busqueda web puntual, busqueda multiple e investigacion consolidada;
- sintesis de contexto largo y de varias fuentes;
- recuperacion puntual de memoria seguida de otra operacion.

## Hueco restante

No faltan tipos de tarea ni formatos para abrir HITL. Falta evidencia live
ciega de Codex 5.5 en 12 capacidades compatibles. El gate no acepta evidencia
simulada, no juzgada, invalidada, en cola ni importada sin ejecucion live.

## Politica de crecimiento

No se ampliara la bateria por cantidad. Se añadiran tareas solo cuando:

1. aparezca una capacidad o formato nuevo;
2. una celda muestre alta dispersion;
3. dos herramientas queden empatadas sin muestra discriminante;
4. HITL descubra una forma de peticion natural no representada.
