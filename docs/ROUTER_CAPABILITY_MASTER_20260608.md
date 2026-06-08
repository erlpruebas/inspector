# Matriz maestra de capacidades y herramientas

Fecha: 2026-06-08

## Objetivo

Esta es la fuente de referencia para construir el router definitivo.

La vista visual y navegable de esta especificacion esta en
[ROUTER_CAPABILITY_MAP_20260608.html](./ROUTER_CAPABILITY_MAP_20260608.html).

El router no debe elegir un modelo por una impresion general de dificultad.
Debe convertir la peticion en necesidades concretas, filtrar las herramientas
que no pueden cumplirlas y elegir la ruta mas rapida que haya demostrado
calidad suficiente.

En este proyecto el proveedor rapido se llama **Groq**. Las transcripciones
`Rock`, `Grok` o similares deben interpretarse como Groq salvo que se mencione
expresamente la familia Grok de xAI.

## Las cuatro dimensiones de una tarea

## Regla de lectura de capacidades

Una capacidad operativa no es una cualidad abstracta del modelo. Describe una
acción que la integración puede ejecutar:

- `direct`: la herramienta hace la acción por sí misma;
- `prepared`: necesita que otro componente recupere o transforme los datos y
  se los inyecte;
- `unsupported`: no puede hacerlo de forma fiable ahora mismo.

Ejemplo: Qwen3-32B puede comparar tres páginas si recibe su texto preparado,
pero no puede realizar por sí solo tres búsquedas web. Compound sí puede hacer
las búsquedas. La capacidad de comparar y el acceso a la web son dimensiones
distintas.

### 1. Ingredientes que hay que preparar

Son datos que deben estar disponibles antes de resolver:

- recuperar un dato de memoria;
- recuperar varios fragmentos de memoria;
- consultar la conversacion reciente;
- localizar uno o varios archivos;
- leer una parte concreta de un archivo;
- preparar archivos completos;
- extraer texto de una imagen;
- transcribir audio;
- descomprimir un archivo;
- consultar un dato web actual;
- investigar varias fuentes web;
- obtener datos de calendario;
- obtener datos de contactos.

La recuperacion de memoria no es un nivel. Es una operacion previa que puede
alimentar cualquier ruta.

### 2. Accesos instrumentales necesarios

Describen lo que la herramienta debe poder tocar:

- texto ya preparado;
- web actual;
- investigacion web de varias fuentes;
- archivo de texto;
- PDF, Word u otro documento binario;
- hoja de calculo;
- imagen;
- audio;
- ZIP u otro archivo comprimido;
- descubrimiento de archivos en carpetas;
- varios archivos completos;
- calculo estructurado;
- ejecucion de codigo o comandos;
- escritura de archivos;
- conservacion del formato;
- contexto largo.

### 3. Trabajo cognitivo necesario

Estas son las caracteristicas que el router debe marcar:

| Capacidad cognitiva | Que significa en una tarea |
| --- | --- |
| `exact_retrieval` | Devolver el dato correcto sin mezclar otros datos. |
| `instruction_following` | Respetar formato, tono, limites y salida solicitada. |
| `field_extraction` | Encontrar nombres, fechas, importes, direcciones o clausulas. |
| `classification` | Asignar una categoria, estado, prioridad o ruta. |
| `controlled_rewriting` | Reescribir sin alterar hechos ni condiciones. |
| `multi_item_synthesis` | Unir varias piezas en una respuesta coherente. |
| `comparison` | Contrastar opciones, documentos, periodos o cifras. |
| `constraint_satisfaction` | Cumplir simultaneamente varias condiciones. |
| `multi_step_calculation` | Calcular, filtrar y volver a calcular o elegir. |
| `causal_diagnosis` | Inferir una causa a partir de sintomas y evidencias. |
| `source_evaluation` | Valorar actualidad, autoridad y consistencia de fuentes. |
| `ambiguity_detection` | Detectar que faltan cliente, fecha, archivo o importes. |
| `artifact_planning` | Decidir como crear o modificar un archivo util. |
| `self_verification` | Comprobar cifras, restricciones, archivos y resultado final. |

### 4. Garantias exigidas

Una tarea puede exigir:

- valores exactos;
- informacion actual;
- citas o fuentes;
- que el archivo exista;
- que el archivo haya sido verificado;
- pedir aclaracion si falta informacion;
- confirmacion humana antes de una accion sensible.

## Contrato del router

El router rapido debe producir una estructura equivalente a esta:

```json
{
  "prepare": [
    {
      "action": "memory_lookup",
      "query": "direccion de la proxima cita con el dentista",
      "return": "text",
      "required": true
    },
    {
      "action": "web_lookup",
      "query": "floristerias cerca de {{dentist_address}}",
      "depends_on": ["dentist_address"],
      "return": "text",
      "required": true
    }
  ],
  "execute": {
    "operation": "compare",
    "cognitive_level": "general",
    "cognitive_requirements": [
      "exact_retrieval",
      "comparison",
      "source_evaluation"
    ],
    "requires": [
      "prepared_text",
      "current_web_lookup"
    ],
    "guarantees": [
      "fresh_information",
      "exact_values"
    ]
  }
}
```

## Plano de control

| Componente | Funcion | Tiempo observado | Uso |
| --- | --- | ---: | --- |
| Parser local | Comandos, sinonimos, acentos y errores leves | ~0,01 s | Siempre primero |
| Groq Llama 3.1 8B Instant | Generar JSON corto y clasificar | 0,58-1,45 s | Router primario |
| Groq Qwen3-32B | Revisar routing ambiguo | ~1,92 s | Fallback por baja confianza |

El router no responde al usuario. Solo prepara el contrato.

## Herramientas activas

| Herramienta | Acceso real | Capacidad cognitiva | Tiempo observado | Papel |
| --- | --- | --- | ---: | --- |
| `local_direct` | Comandos y almacenes locales registrados | Ninguna inferencia | ~0,05 s | Estado, configuracion, dato exacto y acciones deterministas |
| `router_groq_qwen32` | Texto preparado y calculo estructurado | Restricciones, calculo, diagnostico | mediana 1,67 s; media 1,95 s | Worker rapido de razonamiento autocontenido |
| `worker_openrouter_deepseek32` | Texto preparado y contexto largo | Sintesis, comparacion, plan y redaccion | mediana 3,8 s; media 4,91 s | Worker general cuando todo cabe como texto |
| `worker_groq_compound_mini` | Web o codigo, una llamada de herramienta | Recuperacion puntual | ~2,05-2,86 s | Dato actual simple |
| `worker_groq_compound` | Web y codigo con varias llamadas | Sintesis, comparacion y fuentes | 6,86-20,67 s segun pack | Investigacion web de varias fuentes |
| `gemini_grounded_search` | Google Search con grounding | Sintesis y evaluacion de fuentes | 10,28-13,85 s en web real | Busqueda grounded con fuentes |
| `gemini_flash_files` | Texto y varios archivos preparados | Extraccion, resumen y comparacion | mediana 2,84 s; media 3,58 s | Archivos de texto preparados por API |
| `gemini_flash_35` | CLI, imagen, PDF y varios archivos | Extraccion y sintesis general | mediana 24,33 s en muestra de 3 | Entrada multimodal rapida |
| `gemini_pro_long_context` | CLI, PDF, Excel, imagen, audio, ZIP, codigo y escritura | Razonamiento, calculo, diagnostico y verificacion | mediana 24,44 s; media 27,95 s | Ruta agentica potente con prioridad de tiempo |
| `premium_codex_55` | Workspace, archivos, codigo, ejecucion y verificacion | Maxima capacidad de cierre | mediana 51,88 s; media 64,73 s | Escalado de maxima calidad |

## Evidencia de calidad principal

En la bateria HITL de 25 tareas:

| Herramienta | Tareas superadas por juez | Nota media | Victorias directas |
| --- | ---: | ---: | ---: |
| Gemini CLI 3.1 Pro | 21/25 | 8,42 | 8 |
| Codex CLI 5.5 | 23/25 | 9,18 | 17 |

Lectura:

- Gemini 3.1 Pro es aproximadamente dos veces mas rapido.
- Codex 5.5 entrega la mejor respuesta con mayor frecuencia.
- Gemini resolvio imagen, PDF, Excel y ZIP.
- La politica correcta es Gemini primero y Codex si falla la comprobacion o la
  tarea exige un cierre especialmente delicado.

En la muestra adicional de tres tareas:

- Gemini 3.5 Flash produjo salidas utilizables en 3/3;
- paso 2/3 comprobaciones literales;
- fue ligeramente mas rapido que Gemini 3.1 Pro;
- todavia no tiene evidencia suficiente para sustituir a Pro en tareas de
  razonamiento alto.

## Herramientas de respaldo o experimentales

| Herramienta | Resultado | Decision |
| --- | --- | --- |
| OpenRouter Qwen3-32B `sort=latency` | Media 2,84 s frente a 1,92 s en Groq directo | Buen fallback si Groq falla |
| OpenRouter GPT-5.4-mini | 5,82 s y 6,67/10 en pack corto | API fuerte experimental |
| DeepSeek R1 | 3/3 en razonamiento; media 43,29 s | Escalado cognitivo puntual, no primera ruta |
| OpenCode + DeepSeek V3.2 | Funcional, 92-170 s | Runtime alternativo, demasiado lento |
| OpenRouter Gemini 3.5 Flash | 2,39 s en una tarea, salida incompleta | No promover hasta ajustar wrapper |
| OpenRouter Gemini 3.1 Pro | 5,78 s en una tarea, salida incompleta | No promover hasta ajustar wrapper |
| Codex 5.4-mini | 121,05 s en web estricta, 3/4 | No ofrece un escalon claro frente a 5.5 |
| Codex Desktop | Operacion visual y GUI | Aplazado y siempre con confirmacion |

## Herramientas conocidas que no deben entrar

- xAI Grok 4.3: 0/12 con el contrato ofimatico probado.
- R1 Distill Qwen 32B por OpenRouter: lento y con error aritmetico.
- Variante R1 homonima de Groq: retirada por el proveedor.
- Modelos gratuitos de OpenRouter: disponibilidad y calidad inestables.
- Mini Nano/VikingNano: endpoint intermitente.
- LM Studio: depende de que el servidor local este levantado.

## Clases de ejecucion propuestas

Los niveles son rutas operativas. No significan que cada numero sea
intelectualmente superior al anterior.

### E0. Determinista

Herramienta: `local_direct`.

Para comandos, configuracion, estado, alarmas estructuradas y recuperaciones
exactas que no necesitan redaccion.

### E1. Texto preparado rapido

Herramientas:

- Groq Llama Instant para salida trivial;
- Groq Qwen3-32B para restricciones, calculo o diagnostico;
- OpenRouter DeepSeek V3.2 para sintesis y redaccion mas desarrollada.

No abre archivos ni consulta la web. Todo debe llegar preparado.

### E2. Especialistas conectados

Herramientas:

- Compound Mini para un dato web;
- Compound para varias fuentes;
- Gemini Grounded para grounding y citas;
- Gemini Flash Files para archivos de texto preparados.

Se elige por el acceso requerido, no por una nota abstracta de inteligencia.

### E3. Multimodal rapido

Herramienta: Gemini 3.5 Flash CLI.

Para imagenes, PDF sencillos, comparaciones de archivos y extraccion
multimodal cuando no hacen falta calculos complejos, ZIP o verificacion fuerte.

### E4. Agentico potente

Herramienta: Gemini 3.1 Pro CLI.

Para Excel, PDF, imagen, audio, ZIP, muchos archivos, calculo, codigo y
creacion de artefactos con prioridad de velocidad.

### E5. Cierre premium

Herramienta: Codex 5.5 CLI.

Para modificacion delicada, repositorios, pruebas, verificacion fuerte,
diagnosticos importantes o escalado tras un fallo objetivo.

### E6. Visual

Herramienta: Codex Desktop.

Queda fuera del router activo actual. Cuando vuelva, sera una ruta por tipo de
interfaz, no un nivel superior de razonamiento.

## Reglas de seleccion

```text
1. Normalizar y probar comando determinista.
2. Preparar memoria, conversacion, archivos o web que sean necesarios.
3. Descartar herramientas sin los accesos instrumentales requeridos.
4. Descartar herramientas sin las capacidades cognitivas requeridas.
5. Descartar herramientas experimentales o aplazadas.
6. Entre las compatibles, elegir la menor mediana demostrada.
7. Ejecutar comprobaciones objetivas.
8. Escalar dentro de la misma familia solo si falla una comprobacion.
9. Pedir aclaracion si falta un ingrediente obligatorio.
10. Pedir confirmacion humana por riesgo, no por falta de inteligencia.
```

## Aprendizaje evolutivo

El diseño detallado está en
[EVOLUTIONARY_ROUTER_DESIGN_20260608.md](./EVOLUTIONARY_ROUTER_DESIGN_20260608.md).

La unidad de aprendizaje debe ser
`herramienta x capacidades operativas x forma de tarea`, no una nota global
por modelo. Cada intento registra latencia, comprobaciones objetivas, jueces
ciegos, feedback del usuario y versión del catálogo mediante
`benchmarks/schemas/router_experience.schema.json`.

Las rutas nuevas se prueban como desafiantes en tareas sintéticas o
reproducibles. Solo se promocionan con muestra suficiente; mientras tanto, el
sistema genera recomendaciones y no altera automáticamente producción.

## Ejemplos de routing

### Recordar el dentista

```text
preparar: memory_lookup
cognitivo: exact_retrieval
acceso: prepared_text
ruta: local_direct
```

### Dentista y floristeria

```text
preparar: memory_lookup -> web_lookup
cognitivo: exact_retrieval + comparison
acceso: prepared_text + current_web_lookup
ruta: Compound Mini
```

### Comparar presupuestos pegados en el mensaje

```text
preparar: ninguno
cognitivo: comparison + multi_step_calculation
acceso: prepared_text
ruta: Groq Qwen3-32B
```

### Investigar un mercado con fuentes

```text
preparar: web_research
cognitivo: multi_item_synthesis + comparison + source_evaluation
acceso: multi_source_web_research
ruta: Compound o Gemini Grounded segun exigencia de grounding
```

### Extraer un ticket fotografiado

```text
preparar: prepare_files
cognitivo: field_extraction + instruction_following
acceso: read_image
ruta: Gemini 3.5 Flash
```

### Informe mensual desde Excel

```text
preparar: find_files + prepare_files
cognitivo: multi_item_synthesis + multi_step_calculation + self_verification
acceso: read_spreadsheet + read_multiple_files + write_file
ruta: Gemini 3.1 Pro
escalado: Codex 5.5 si falla la comprobacion
```

### Corregir un proyecto y ejecutar pruebas

```text
preparar: find_files
cognitivo: causal_diagnosis + artifact_planning + self_verification
acceso: discover_files + code_execution + write_file
ruta: Codex 5.5
```

## Estado de congelacion

Se pueden congelar ya:

- el vocabulario de capacidades;
- el contrato de salida del router;
- la separacion entre preparacion y ejecucion;
- las clases E0-E6;
- la seleccion determinista por compatibilidad y latencia;
- la politica de comprobacion y escalado.

Queda por medir antes de considerar el router terminado:

- precision del router Groq al generar este contrato sobre las 25 tareas;
- bateria completa de Gemini 3.5 Flash;
- Gemini Files API nativa;
- mejor prompt o wrapper de Gemini por OpenRouter;
- comportamiento de memoria estructurada para eventos y fechas.
