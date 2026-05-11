# AI Arena Task Catalog Plan

Objetivo: pasar de 5 tareas semilla a una bateria amplia que mida ofimatica, datos, investigacion, programacion y comportamiento de agentes con dificultad creciente.

## Niveles

| Nivel | Nombre | Proposito |
| --- | --- | --- |
| L1 | Respuesta simple | Ver si el motor entiende la tarea y escribe el archivo esperado |
| L2 | Transformacion con archivo | Leer datos semilla y producir un artefacto estructurado |
| L3 | Multiarchivo | Cruzar informacion entre 2-5 archivos con requisitos concretos |
| L4 | Formato profesional | Generar CSV, ICS, DOCX, XLSX, PPTX o Markdown con estructura validable |
| L5 | Investigacion web | Usar informacion actual, citar fuentes y separar hechos de inferencias |
| L6 | Codigo y tests | Modificar un mini-proyecto, ejecutar tests y reparar fallos |
| L7 | Ambiguedad controlada | Resolver instrucciones incompletas sin inventar datos criticos |
| L8 | Robustez | Manejar datos sucios, formatos mixtos, errores y restricciones de tiempo |

## Familias de tareas

1. Resumen ejecutivo y extraccion de acciones.
2. Conversion de logs a CSV/JSON.
3. Comparacion de presupuestos/facturas.
4. Agenda y calendarios `.ics`.
5. Investigacion web con reporte `.md` o `.docx`.
6. Limpieza de hojas de calculo y formulas.
7. Creacion de presentaciones.
8. Analisis financiero simple con datos dados.
9. Redaccion de emails profesionales.
10. Programacion Python con tests.
11. Refactor pequeno en proyecto existente.
12. Debugging de error reproducible.
13. Extraccion de datos desde HTML.
14. Normalizacion de contactos/clientes.
15. Planificacion de proyecto con dependencias.

## Esquema recomendado para `tasks.json`

Cada tarea deberia incluir:

```json
{
  "id": "nombre_unico",
  "level": "L3",
  "category": "multiarchivo",
  "prompt": "Instruccion exacta para el motor",
  "required_files": ["archivo.txt"],
  "expected_outputs": ["resultado.md"],
  "requires_network": false,
  "rubric": {
    "correctness": 4,
    "format": 2,
    "completeness": 2,
    "efficiency": 1,
    "traceability": 1
  }
}
```

## Estado implementado

Ya hay 18 tareas en `benchmarks/tasks/tasks.json` con assets locales. Cubren resumen, CSV, HTML, calendarios, conciliacion, logs, mini-proyectos Python, investigacion web y datos rotos.

## Siguiente incremento recomendado

Subir de 18 a 40 tareas:

- 10 L1-L2 para humo y regresion rapida.
- 10 L3-L4 para ofimatica real.
- 8 L5 para busqueda y reporte.
- 8 L6-L7 para codigo y debugging.
- 4 L8 para resistencia con datos rotos.

Cada tarea debe traer sus assets minimos y una rubrica concreta para que el juez pueda puntuar sin subjetividad excesiva.
