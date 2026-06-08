# Functional Parity Matrix: Agent 2.2

| fuente anterior | comportamiento esperado | módulo 2.2 | pruebas | estado |
| :--- | :--- | :--- | :--- | :--- |
| **Telegram y transporte** |
| `orchestrator_v2_1/telegram_gateway.py` | long polling y restricción por usuarios o chats autorizados | `transport/telegram.py` | [x] | Completado |
| `orchestrator_v2_1/telegram_gateway.py` | mensajes de texto y mensajes editados | `transport/telegram.py` | [x] | Completado |
| `orchestrator_v2_1/telegram_gateway.py` | recepción y descarga de notas de voz y archivos | `transport/telegram.py` | [x] | Completado |
| `orchestrator_v2_1/telegram_gateway.py` | envío de texto dividido según el límite de Telegram | `transport/telegram.py` | [x] | Completado |
| `orchestrator_v2_1/telegram_gateway.py` | envío de audio, imágenes y archivos de resultado | `transport/telegram.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | inbox y outbox aislados por ejecución | `transport/queue.py` | [ ] | Pendiente |
| `orchestrator_v2_1/telegram_gateway.py` | progreso visible: recibido, enrutado, ejecutando y completado | `transport/telegram.py` | [ ] | Pendiente |
| `orchestrator_v2_1/telegram_gateway.py` | tiempos de transcripción, memoria, routing, ejecución y voz | `transport/metrics.py` | [ ] | Pendiente |
| `orchestrator_v2_1/orchestrator.py` | recarga y reinicio controlados | `transport/lifecycle.py` | [ ] | Pendiente |
| `orchestrator_v2_1/telegram_gateway.py` | degradación limpia cuando Telegram o un proveedor falla | `transport/telegram.py` | [ ] | Pendiente |
| **Voz** |
| `orchestrator_v2_1/orchestrator.py` | transcripción de notas de voz | `capabilities/voice.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | Groq/Whisper como vía rápida y Gemini como respaldo | `capabilities/voice.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | respuesta textual completa | `capabilities/voice.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | resumen oral para respuestas largas | `capabilities/voice.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | Edge TTS como proveedor predeterminado | `capabilities/voice.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | proveedores alternativos ya integrados cuando estén configurados | `capabilities/voice.py` | [x] | Completado |
| `orchestrator_v2_1/telegram_gateway.py` | envío del audio a Telegram | `transport/telegram.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | reproducción opcional por el altavoz del ordenador | `capabilities/voice.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | comandos `voz on/off` y `altavoz on/off` | `cli.py` / `transport/telegram.py` | [ ] | Pendiente |
| `orchestrator_v2_1/orchestrator.py` | selección persistente de proveedor y voz | `config.py` | [ ] | Pendiente |
| `orchestrator_v2_1/orchestrator.py` | precalentamiento | `capabilities/voice.py` | [ ] | Pendiente |
| `orchestrator_v2_1/orchestrator.py` | funcionamiento solo por texto cuando no exista proveedor de voz | `capabilities/voice.py` | [x] | Completado |
| **Memoria y conversación** |
| `orchestrator_v2_1/memory_retrieval.py` | memoria persistente por usuario e hilo | `capabilities/memory.py` | [x] | Completado |
| `orchestrator_v2_1/memory_retrieval.py` | diario Markdown legible | `capabilities/memory.py` | [x] | Completado |
| `orchestrator_v2_1/memory_retrieval.py` | índice o compactación | `capabilities/memory.py` | [x] | Completado |
| `orchestrator_v2_1/memory_retrieval.py` | guardar hechos solicitados | `capabilities/memory.py` | [x] | Completado |
| `orchestrator_v2_1/memory_retrieval.py` | recuperar únicamente hechos relevantes | `capabilities/memory.py` | [x] | Completado |
| `orchestrator_v2_1/memory_retrieval.py` | no anunciar contadores ni inventarios de memoria salvo petición | `capabilities/memory.py` | [x] | Completado |
| `orchestrator_v2_1/memory_retrieval.py` | hilos: listar, crear, cambiar y consultar el hilo activo | `capabilities/memory.py` | [x] | Completado |
| `orchestrator_v2_1/memory_retrieval.py` | conservación de contexto y adjuntos relevantes | `capabilities/memory.py` | [x] | Completado |
| `orchestrator_v2_1/memory_retrieval.py` | migrador opcional de datos antiguos, sin convertirlos en dependencia | `capabilities/memory.py` | [x] | Completado |
| **Alarmas y trabajo pendiente** |
| `orchestrator_v2_1/orchestrator.py` | alarmas relativas y con fecha/hora | `scheduling/alarms.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | recurrencia diaria, semanal y mensual | `scheduling/alarms.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | listar y cancelar alarmas | `scheduling/alarms.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | entrega por Telegram cuando vence una alarma | `scheduling/alarms.py` / `transport/telegram.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | persistencia y recuperación tras reiniciar | `scheduling/alarms.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | cola de tareas pendientes | `scheduling/queue.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | listar, continuar, limpiar y detener trabajos | `scheduling/queue.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | reanudación controlada al arrancar | `scheduling/queue.py` | [x] | Completado |
| **Router y ejecución** |
| `orchestrator_v2_1/executor.py` | comandos locales rápidos | `routing/executor.py` | [x] | Completado |
| `orchestrator_v2_1/capability_selector.py` | routing estructurado por capacidades | `routing/selector.py` | [x] | Completado |
| `orchestrator_v2_1/tool_registry.py` | todas las herramientas activas o experimentales registradas | `routing/registry.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | fallbacks de proveedor | `routing/fallbacks.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | archivos y adjuntos estructurados | `routing/attachments.py` | [x] | Completado |
| `orchestrator_v2_1/executor.py` | aislamiento de workdirs | `engines/workspace.py` | [x] | Completado |
| `orchestrator_v2_1/executor.py` | API, Gemini CLI, Codex CLI y OpenCode | `engines/` | [x] | Completado |
| `orchestrator_v2_1/desktop_codex_operator.py` | Codex Desktop aislado y aplazable, sin contaminar el núcleo | `engines/codex_desktop.py` | [x] | Completado |
| `orchestrator_v2_1/executor.py` | ejecución de código y creación o modificación de artefactos | `engines/execution.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | trazas de ruta, modelo, versión, tiempos y errores | `routing/tracing.py` | [x] | Completado |
| **Seguridad y control humano** |
| `orchestrator_v2_1/orchestrator.py` | privacidad `clear`, `mixed` y `redacted`, además de confirmación | `privacy/levels.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | confirmación `sí/no` para acciones sensibles, externas o irreversibles | `privacy/confirmation.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | cancelación de una operación en curso | `routing/cancellation.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | secretos solo por entorno o almacén local ignorado | `config.py` | [x] | Completado |
| `orchestrator_v2_1/executor.py` | sandbox y límites de workspace | `engines/sandbox.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | no mostrar credenciales ni datos internos en logs o estado | `privacy/redaction.py` | [x] | Completado |
| **Estado, autoconocimiento y desarrollo** |
| `orchestrator_v2_1/orchestrator.py` | `estado` y `/status` con integraciones, APIs, CLIs, runtime y config | `cli.py` / `capabilities/status.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | estado de voz, altavoz, privacidad, confirmación y modo desarrollo | `capabilities/status.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | no incluir inventario de memoria | `capabilities/status.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | preguntas sobre capacidades y herramientas disponibles | `capabilities/introspection.py` | [x] | Completado |
| `orchestrator_v2_1/development_mode.py` | activación equivalente mediante comandos específicos | `capabilities/dev_mode.py` | [x] | Completado |
| `orchestrator_v2_1/development_mode.py` | propuesta, aprobación, implementación aislada, pruebas, commit, push... | `capabilities/dev_mode.py` | [x] | Completado |
| `orchestrator_v2_1/development_mode.py` | desactivación y cancelación inmediata | `capabilities/dev_mode.py` | [x] | Completado |
| `orchestrator_v2_1/codex_rate_limits.py` | monitor de cuota Codex y pie compacto cuando exista snapshot válido | `scheduling/codex_quota.py` | [x] | Completado |
| **Gestión operativa** |
| `orchestrator_v2_1/orchestrator.py` | directorio de trabajo configurable | `config.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | lista de directorios adicionales permitidos | `config.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | añadir y retirar directorios | `cli.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | configuración portable | `config.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | diagnóstico de proveedores y CLIs | `cli.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | logs y trazas estructurados | `config.py` / `routing/tracing.py` | [x] | Completado |
| `orchestrator_v2_1/orchestrator.py` | interfaz CLI para estado, routing, ejecución y pruebas | `cli.py` | [x] | Completado |
| N/A | GUI antigua solo se migra si sigue siendo útil | N/A | [x] | Completado (Omitida por diseño) |
