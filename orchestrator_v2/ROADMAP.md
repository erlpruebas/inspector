# Roadmap minimo y backlog completo

## Vision estrategica minima

1. Cerrar contratos de profesiones, tareas y archivos.
2. Hacer que el laboratorio cargue una profesion y active personas/bots.
3. Enviar tareas a ciegas al gestor por un canal realista.
4. Recibir respuestas, guardar evidencias y evaluarlas con juez de excelencia.
5. Usar los resultados para ajustar router, herramientas y memoria.
6. Repetir con mas profesiones y modelos sin reescribir el sistema.

## Politica de modelos

- GPT-5.5: arquitectura, juez de excelencia y escalado dificil.
- GPT-5.4 mini: trabajador operativo barato para generacion repetitiva, normalizacion y ejecucion no critica.
- Groq rapido: router y tareas ligeras.
- OpenRouter: workers baratos/alternativos.
- Gemini: contexto largo y archivos grandes.

Los nombres concretos son reemplazables. La arquitectura se apoya en capacidades, no en marcas.

## Pendiente real, desglosado

### A. Contratos y catalogo

- Definir esquema unico de profesion.
- Definir esquema unico de tarea.
- Definir esquema unico de archivo sintetico.
- Definir respuesta esperada y claves evaluables.
- Convertir `benchmarks/contracts/office_general` en catalogo cargable.
- Permitir varias profesiones en carpetas hermanas.
- Validar que cada tarea referencia archivos existentes.
- Exportar catalogo a JSONL para maquinas.
- Mantener Markdown legible para humanos.

### B. Laboratorio ciego

- Crear activacion de laboratorio: profesion, personas, tareas, velocidad.
- Permitir modo dry-run.
- Permitir modo Telegram grupo/bots.
- Preparar modo futuro de cuentas reales MTProto.
- Programar velocidad: fija, aleatoria o burst.
- Enviar archivos junto a la tarea cuando aplique.
- Guardar cada envio como evidencia.
- Esperar respuesta del gestor.
- Guardar respuesta textual y audio si llega.
- Asociar respuesta con tarea/persona.
- Reintentar si hay timeout.
- Marcar tarea como fallida si no responde.

### C. Evaluacion

- Evaluar con expected keys.
- Evaluar con rubrica.
- Evaluar con juez de excelencia.
- Guardar juicio, puntuacion y razon.
- Comparar herramientas/modelos.
- Generar informe ejecutivo final.
- Detectar regresiones frente a runs anteriores.

### D. Orquestador gestor

- Conectar Telegram existente con `orchestrator_v2`.
- Conectar boton local de voz con `GestorOrquestador`.
- Implementar confirmacion de ordenes por voz.
- Implementar modo configuracion conversacional.
- Enviar texto completo a Telegram.
- Enviar audio resumido si la respuesta es larga.
- Permitir `leeme la respuesta completa`.
- Separar archivos por usuario/hilo.
- Guardar memoria inmediata.
- Compactar memoria en reposo.
- Crear memoria procedimental.

### E. Herramientas y router

- Medir salud de cada herramienta.
- Registrar coste, latencia y fallos.
- Enrutar por dificultad, archivos, privacidad y riesgo.
- Escalar si falla una herramienta.
- Mantener Gemini para contexto largo.
- Mantener GPT-5.5 como juez/escalado, no como dependencia unica.

### F. Email

- Localizar proyecto antiguo de correo en disco D.
- Recuperar variables SMTP/IMAP.
- Probar envio con clave de aplicacion.
- Probar lectura de no leidos.
- Integrar email como herramienta del gestor.

### G. Operacion

- Crear comandos CLI claros.
- Crear `.env.example`.
- Crear logs por componente.
- Crear estado de laboratorio.
- Crear documentacion de arranque.
- Crear pruebas unitarias de loader, scheduler y router.

## Primer bloque que estamos implementando ahora

- `lab_contracts.py`: contratos internos. Implementado.
- `catalog_loader.py`: carga profesiones y tareas. Implementado.
- `lab_scheduler.py`: seleccion y cadencia. Implementado.
- `telegram_lab.py`: transporte Telegram abstracto. Implementado para dry-run, mensajes y documentos por grupo/bots.
- `lab_cli.py`: comandos para listar y activar en dry-run. Implementado.
- `lab_evaluator.py`: evaluacion por claves y prompt de juez. Implementado.
- `task_generator.py`: prompt/escritura de nuevas profesiones. Implementado.

## Estado actual verificable

- Catalogo `office_general`: 30 tareas.
- Personas sinteticas disponibles: 6.
- Archivos faltantes: 0.
- Activacion dry-run: genera evidencias JSON por mensaje.
- Transporte Telegram grupo/bots: preparado con variables `LAB_BOT_1_TOKEN` ... `LAB_BOT_4_TOKEN` y `LAB_TELEGRAM_CHAT_ID`.
- Modo usuario real MTProto: pendiente, recomendado si queremos simular usuarios humanos completos.
- Contabilidad de tokens: activa para benchmarks, laboratorio y orquestador final con logs JSONL.
