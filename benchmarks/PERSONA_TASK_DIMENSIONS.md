# Dimensiones Para Benchmark De Tareas Naturales

La suite deja de usar niveles rigidos. Las tareas se describen por dimensiones observables, mas estables que la dificultad.

Estas dimensiones son una primera version y deben evolucionar con datos de benchmark y feedback humano.

## context_scope
Cantidad y dispersion del contexto necesario.

Valores: `none`, `small`, `medium`, `large`, `cross_project`

## data_mode
Tipo de informacion dominante.

Valores: `conversation`, `documents`, `tables`, `logs`, `mixed`, `web_fresh`

## tool_need
Capacidad externa necesaria para resolver bien.

Valores: `none`, `read_files`, `create_file`, `code_execution`, `web_search`, `calendar`, `multi_tool`

## risk
Coste potencial de una respuesta mala.

Valores: `low`, `medium`, `high`, `critical`

## output_form
Forma final que el usuario espera.

Valores: `short_reply`, `email`, `table`, `checklist`, `plan`, `report`, `script`, `calendar`, `data_file`

## reasoning_shape
Tipo de procesamiento mental principal.

Valores: `retrieve`, `extract`, `compare`, `calculate`, `synthesize`, `diagnose`, `decide`, `draft`

## freshness
Necesidad de informacion actual.

Valores: `static_local`, `recent_local`, `current_web`

## error_tolerance
Cuanto error puede aceptar el flujo antes de escalar.

Valores: `high`, `medium`, `low`, `near_zero`

## Como Usarlas

1. Generar tareas naturales sin nivel numerico.
2. Etiquetarlas inicialmente con estas dimensiones.
3. Ejecutarlas contra varios modelos.
4. Medir nota, coste, tiempo, fallos, reintentos y claves acertadas.
5. Aprender que dimensiones predicen mejor el modelo minimo suficiente.

La dificultad pasa a ser una variable observada, no una etiqueta impuesta de antemano.
