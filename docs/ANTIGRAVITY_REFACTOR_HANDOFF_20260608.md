# Handoff para Antigravity: Inspector Agent 2.2

Fecha: 2026-06-08

## Objetivo

Construir `agent_v2_2/` como la versión limpia, portable y autocontenida del
agente Inspector. Esta versión no debe importar módulos de:

- `orchestrator_v2_1/`;
- `orchestrator_v2/`;
- `telegram_codex_orchestrator/`;
- scripts sueltos de la raíz.

Las versiones anteriores se conservan sin cambios destructivos como referencia
y fuente de comportamiento probado. Agent 2.2 puede copiar y adaptar ideas,
pero el código final debe vivir dentro de su propia carpeta.

Autocontenida significa:

- código, configuración de ejemplo, esquemas, documentación, pruebas y assets
  sintéticos necesarios dentro de `agent_v2_2/`;
- dependencias externas declaradas;
- secretos y estados de ejecución fuera de Git;
- ningún path obligatorio específico de `D:\inspector`;
- arranque reproducible en otro Windows después de clonar el repositorio.

## Lectura obligatoria

Leer en este orden antes de editar:

1. `LEEME_PRIMERO.md`
2. `docs/ROUTER_CAPABILITY_MAP_20260608.html`
3. `docs/ROUTER_CAPABILITY_MASTER_20260608.md`
4. `docs/EVOLUTIONARY_ROUTER_DESIGN_20260608.md`
5. `docs/ROUTER_CAPABILITIES_GAIA_GAPS_20260607.md`
6. `docs/HITL_EXCELLENCE_RESULTS_20260607.md`
7. `docs/HITL_BRUTEFORCE_ARENA_20260607.md`
8. `docs/TELEGRAM_HITL_SYNTHETIC_BATTERY_20260607.md`
9. `orchestrator_v2_1/capability_catalog.json`
10. `orchestrator_v2_1/capability_selector.py`
11. `orchestrator_v2_1/codex_rate_limits.py`
12. `benchmarks/benchmark_scheduler.py`
13. `benchmarks/gemini_competitive_judge.py`
14. `benchmarks/codex_competitive_judge.py`
15. `benchmarks/schemas/router_experience.schema.json`
16. `benchmarks/tasks/telegram_hitl_business_battery_20260607.json`
17. `benchmarks/tasks/telegram_hitl_business_arena_20260607.json`
18. `benchmarks/engine_matrix_hitl_bruteforce_20260607.json`
19. `benchmarks/engine_matrix_hitl_excellence_20260607.json`
20. `benchmarks/env_utils.py`
21. `.gitignore`

Para ideas de tareas difíciles puede consultarse el dataset local de GAIA en
`D:\gaiabench`, pero Agent 2.2 no debe depender de ese path para funcionar.

## Situación actual que no debe perderse

- El proveedor rápido se llama **Groq**, con Q. Las transcripciones `Grok`,
  `Rock` o similares normalmente se refieren a Groq.
- Existen 25 tareas HITL con memoria, redacción, comparación, web simulada,
  CSV, imagen, PDF, Excel, ZIP, diagnóstico y ambigüedad.
- Existen ejecutores para API, Gemini CLI, Codex CLI y OpenCode.
- Existen comprobadores de claves, jueces ciegos Gemini y Codex y selección
  `fastest_sufficient`.
- Gemini CLI 3.1 Pro obtuvo 21/25 y 8,42/10 con mediana de 24,44 segundos.
- Codex 5.5 obtuvo 23/25 y 9,18/10 con mediana de 51,88 segundos.
- `orchestrator_v2_1/codex_rate_limits.py` ya lee la ventana de cinco horas y
  la semanal mediante el método JSON-RPC experimental
  `account/rateLimits/read`.
- El árbol Git actual contiene muchos cambios y archivos sin seguimiento. No
  debe limpiarse mediante reset, checkout, borrado masivo o stashing
  destructivo.

## Paridad funcional obligatoria

Agent 2.2 es una reconstrucción limpia, no una reducción del producto. Antes
de considerarlo sustituto debe conservar el conjunto útil de funcionalidades
presentes en `orchestrator_v2_1/` y en
`telegram_codex_orchestrator/`.

Crear primero
`agent_v2_2/docs/FUNCTIONAL_PARITY_MATRIX.md`. Para cada función debe indicar:

```text
fuente anterior | comportamiento esperado | módulo 2.2 | pruebas | estado
```

La matriz debe cubrir como mínimo:

### Telegram y transporte

- long polling y restricción por usuarios o chats autorizados;
- mensajes de texto y mensajes editados;
- recepción y descarga de notas de voz y archivos;
- envío de texto dividido según el límite de Telegram;
- envío de audio, imágenes y archivos de resultado;
- inbox y outbox aislados por ejecución;
- progreso visible: recibido, enrutado, ejecutando y completado;
- tiempos de transcripción, memoria, routing, ejecución y voz;
- recarga y reinicio controlados;
- degradación limpia cuando Telegram o un proveedor falla.

### Voz

- transcripción de notas de voz;
- Groq/Whisper como vía rápida y Gemini como respaldo cuando proceda;
- respuesta textual completa;
- resumen oral para respuestas largas;
- Edge TTS como proveedor predeterminado;
- proveedores alternativos ya integrados cuando estén configurados;
- envío del audio a Telegram;
- reproducción opcional por el altavoz del ordenador;
- comandos `voz on/off` y `altavoz on/off`;
- selección persistente de proveedor y voz;
- precalentamiento;
- funcionamiento solo por texto cuando no exista proveedor de voz.

### Memoria y conversación

- memoria persistente por usuario e hilo;
- diario Markdown legible;
- índice o compactación;
- guardar hechos solicitados;
- recuperar únicamente hechos relevantes;
- no anunciar contadores ni inventarios de memoria salvo petición explícita;
- hilos: listar, crear, cambiar y consultar el hilo activo;
- conservación de contexto y adjuntos relevantes;
- migrador opcional de datos antiguos, sin convertirlos en dependencia.

### Alarmas y trabajo pendiente

- alarmas relativas y con fecha/hora;
- recurrencia diaria, semanal y mensual;
- listar y cancelar alarmas;
- entrega por Telegram cuando vence una alarma;
- persistencia y recuperación tras reiniciar;
- cola de tareas pendientes;
- listar, continuar, limpiar y detener trabajos;
- reanudación controlada al arrancar.

### Router y ejecución

- comandos locales rápidos;
- routing estructurado por capacidades;
- todas las herramientas activas o experimentales registradas;
- fallbacks de proveedor;
- archivos y adjuntos estructurados;
- aislamiento de workdirs;
- API, Gemini CLI, Codex CLI y OpenCode;
- Codex Desktop aislado y aplazable, sin contaminar el núcleo;
- ejecución de código y creación o modificación de artefactos;
- trazas de ruta, modelo, versión, tiempos y errores.

### Seguridad y control humano

- privacidad `clear`, `mixed` y `redacted`, además de confirmación cuando
  corresponda;
- confirmación `sí/no` para acciones sensibles, externas o irreversibles;
- cancelación de una operación en curso;
- secretos solo por entorno o almacén local ignorado;
- sandbox y límites de workspace;
- no mostrar credenciales ni datos internos en logs o estado.

### Estado, autoconocimiento y desarrollo

- `estado` y `/status` con integraciones, APIs, CLIs, runtime y configuración;
- estado de voz, altavoz, privacidad, confirmación y modo desarrollo;
- no incluir inventario de memoria;
- preguntas sobre capacidades y herramientas disponibles;
- activación equivalente mediante `activar modo desarrollo`,
  `activar modo de desarrollo` y `activar modo desarrollador`;
- propuesta, aprobación, implementación aislada, pruebas, commit, push y
  recuperación ante conflictos;
- desactivación y cancelación inmediata;
- monitor de cuota Codex y pie compacto cuando exista snapshot válido.

### Gestión operativa

- directorio de trabajo configurable;
- lista de directorios adicionales permitidos;
- añadir y retirar directorios;
- configuración portable;
- diagnóstico de proveedores y CLIs;
- logs y trazas estructurados;
- interfaz CLI para estado, routing, ejecución y pruebas;
- GUI antigua solo se migra si sigue siendo útil; si se excluye debe
  justificarse y dejarse como adaptador posterior, no desaparecer por olvido.

No basta con que una función exista en código. Debe tener una prueba o un
procedimiento de aceptación reproducible.

## Arquitectura objetivo

Estructura recomendada:

```text
agent_v2_2/
  README.md
  pyproject.toml
  .env.example
  src/agent_v2_2/
    cli.py
    config.py
    models.py
    capabilities/
    routing/
    engines/
    scheduling/
    judging/
    experiences/
    privacy/
    transport/
  schemas/
  tasks/
  assets/
  configs/
  scripts/
  tests/
  docs/
  runtime/        # ignorado por Git
```

Puede ajustarse si existe una alternativa más clara, pero deben mantenerse
fronteras explícitas entre catálogo, ejecutores, scheduler, evaluación,
experiencias y transporte.

## Capacidades que se puntúan

Cada herramienta recibirá notas de 0 a 10, con número de muestras y confianza,
para:

1. extracción puntual en texto corto;
2. extracción puntual en documento largo;
3. extracción cruzada en varios documentos;
4. síntesis de texto largo;
5. síntesis de varios documentos;
6. comparación de datos o documentos;
7. cálculo y filtrado estructurado;
8. transformación y redacción con datos;
9. búsqueda web puntual;
10. búsqueda web multifactor;
11. investigación y criterio multifuente;
12. lectura de PDF y documentos binarios;
13. lectura visual y OCR;
14. inspección de carpetas y archivos comprimidos;
15. creación o modificación de archivos;
16. ejecución técnica y diagnóstico;
17. verificación del resultado.

No calcular una nota a partir de tareas incompatibles con la herramienta.

## Accesos y formatos

Los accesos no se califican de 0 a 10. Se registran por operación y formato:

```text
unsupported | prepared | direct
```

Operaciones:

- leer;
- extraer;
- crear;
- modificar;
- conservar formato;
- verificar.

Familias mínimas:

- texto: TXT, MD, CSV, TSV, JSON, XML, YAML, HTML y LOG;
- Office moderno: DOCX, XLSX y PPTX;
- Office antiguo: DOC, XLS y PPT;
- OpenDocument y texto enriquecido: ODT, ODS y RTF;
- documentos: PDF;
- imágenes: PNG, JPG/JPEG, WEBP, TIFF y HEIC;
- audio: MP3, WAV, M4A y OGG;
- comprimidos: ZIP, 7Z, RAR, TAR y TAR.GZ;
- correo: EML, MSG y MBOX;
- código, repositorios y carpetas completas.

Una herramienta puede leer un formato y no poder modificarlo o conservarlo.

## Scheduler consciente de cuota Codex

Reutilizar el protocolo demostrado en
`orchestrator_v2_1/codex_rate_limits.py`, pero implementar una copia limpia
dentro de Agent 2.2.

Reglas:

1. Consultar la cuota antes de cada ejecución que use Codex 5.5, incluido su
   uso como juez.
2. No iniciar trabajos Codex cuando quede 25 % o menos de la ventana de cinco
   horas.
3. No cancelar un trabajo ya empezado únicamente porque la lectura posterior
   cruce el umbral.
4. Guardar `five_hour_remaining`, `five_hour_resets_at`, cuota semanal,
   captura y decisión del scheduler.
5. Cuando Codex quede pausado, continuar con trabajos Gemini, Groq,
   OpenRouter, comprobadores y preparación de datos.
6. Programar los trabajos Codex pendientes para después de
   `five_hour_resets_at`, añadiendo un pequeño margen configurable.
7. Persistir la cola para sobrevivir reinicios del proceso o del ordenador.
8. Si la cuota no puede leerse o el snapshot está caducado, no lanzar Codex:
   diferirlo con una razón explícita.
9. Permitir configurar umbral, frescura máxima, margen de reinicio y cuota
   semanal mínima.
10. Probar todo con snapshots falsos; los tests no deben gastar cuota real.

## Evaluación evolutiva

La unidad de aprendizaje es:

```text
herramienta x capacidad x forma de tarea
```

Cada intento debe guardar:

- herramienta, proveedor, modelo y versión;
- tarea, capacidades y formatos;
- tiempo;
- resultado técnico;
- comprobaciones objetivas;
- notas de uno o varios jueces;
- feedback humano cuando exista;
- motivo de error;
- versión del catálogo, prompt y código.

Política:

1. Las comprobaciones objetivas tienen prioridad sobre el juez.
2. Gemini es el juez habitual.
3. Codex 5.5 actúa como segundo juez o árbitro cuando haya cuota.
4. Los jueces reciben respuestas anonimizadas.
5. No usar una nota global del modelo: agregar por capacidad y forma de tarea.
6. Registrar tamaño de muestra y una estimación de confianza.
7. Promover una ruta solo con muestra suficiente.
8. La exploración se hace en baterías sintéticas o modo evaluación explícito,
   no duplicando silenciosamente trabajo real del usuario.

## Auditoría y ampliación de tareas

Las 25 tareas actuales son una base, no cobertura suficiente.

Crear una matriz:

```text
capacidad x formato x operación x dificultad x herramienta compatible
```

Identificar huecos antes de generar nuevas tareas. Deben cubrirse al menos:

- DOCX: lectura, creación, modificación y conservación de formato;
- XLSX: filtros, fórmulas, gráficos, estilos y edición;
- PPTX: lectura, creación y modificación;
- OCR fácil y difícil, multipágina y tablas;
- audio y transcripción;
- EML, MSG, MBOX y adjuntos;
- archivos grandes y contexto largo;
- varios formatos combinados;
- creación y modificación real de artefactos;
- código, terminal, diagnóstico y pruebas;
- búsqueda web puntual real;
- búsqueda web multifactor;
- investigación multifuente y contradicciones;
- información insuficiente;
- timeouts, errores de proveedor y resultados parciales;
- autoverificación.

Objetivo inicial: 60-80 tareas pequeñas y dirigidas. No ejecutar toda la
batería en cada cambio. Crear:

- smoke suite;
- suite por capacidad;
- suite completa nocturna o lenta;
- suite exclusiva de Codex gobernada por cuota.

Todos los datos deben ser sintéticos y aptos para publicación.

## Portabilidad

- Eliminar paths absolutos del nuevo código.
- Resolver todo desde la raíz de `agent_v2_2` o configuración.
- Crear `.env.example` solo con nombres y comentarios, nunca valores.
- Detectar CLIs y producir diagnóstico comprensible.
- Documentar instalación y arranque en otro Windows.
- Incluir comandos de smoke test y reanudación del scheduler.
- El runtime, respuestas, colas, credenciales y resultados voluminosos deben
  quedar ignorados.

## Git y publicación

Repositorio remoto:

```text
origin https://github.com/erlpruebas/inspector.git
```

Rama base actual:

```text
codex/orchestrator-v2-1-baseline
```

Reglas:

1. No ejecutar `git reset --hard`, `git checkout --`, `git clean`, borrados
   masivos ni reversiones de cambios existentes.
2. Tratar todos los cambios actuales como trabajo del usuario.
3. Crear una rama nueva con prefijo `gemini/`, por ejemplo
   `gemini/agent-v2-2`.
4. No publicar `.env`, credenciales, perfiles, memoria real, runtime ni
   resultados masivos.
5. Auditar con `git status`, `git diff`, búsquedas de secretos y tamaño de
   archivos.
6. Preparar un manifiesto que clasifique qué se publica, qué se ignora y qué
   queda como histórico.
7. Mantener los commits pequeños y temáticos.
8. Ejecutar pruebas antes de cada commit importante.
9. Publicar la rama y abrir un PR; no fusionar directamente a la rama base.
10. Si la autenticación GitHub no está disponible, dejar todos los commits
    preparados y documentar el comando pendiente sin exponer credenciales.

## Fases de trabajo

### Fase 0. Inventario

- Leer y mapear el sistema.
- Identificar código reutilizable, datos sintéticos y ruido.
- Escribir el plan dentro de `agent_v2_2/docs/IMPLEMENTATION_PLAN.md`.
- No modificar versiones antiguas salvo documentación o `.gitignore`
  estrictamente necesarios.

### Fase 1. Esqueleto autocontenido

- Crear paquete, configuración, CLI, modelos y tests mínimos.
- Crear la matriz de paridad funcional contra las dos generaciones anteriores.
- Añadir catálogo operacional y esquema de formatos.
- Conseguir instalación y smoke test.

### Fase 2. Núcleo y paridad operativa

- Migrar Telegram, memoria, hilos, alarmas, pendientes, voz, altavoz, estado,
  privacidad, confirmaciones y modo desarrollo.
- Mantener transportes y proveedores como adaptadores alrededor de un núcleo
  independiente.
- Añadir pruebas de paridad antes de retirar cualquier ruta antigua.

### Fase 3. Scheduler y cuota

- Implementar cola persistente.
- Implementar monitor y guardia de cuota Codex.
- Permitir que otros proveedores sigan trabajando mientras Codex espera.
- Añadir tests temporales deterministas.

### Fase 4. Arena y jueces

- Migrar ejecutores necesarios a interfaces limpias.
- Implementar comprobaciones objetivas, juez Gemini y juez Codex aplazable.
- Guardar experiencias estructuradas.

### Fase 5. Auditoría de cobertura

- Etiquetar las 25 tareas.
- Generar informe de huecos.
- Crear tareas nuevas y assets sintéticos hasta cubrir la matriz prioritaria.

### Fase 6. Router evolutivo

- Calcular métricas por capacidad y forma de tarea.
- Seleccionar la herramienta compatible más rápida con confianza suficiente.
- Mantener exploración controlada y promociones versionadas.

### Fase 7. Publicación

- Limpiar únicamente Agent 2.2 y sus artefactos de publicación.
- Ejecutar suite.
- Crear commits, push y PR.
- Entregar informe de reproducción en otro equipo.

## Criterios de aceptación

- `agent_v2_2` no importa ninguna versión anterior.
- La matriz de paridad no contiene funciones obligatorias pendientes.
- Telegram, voz, memoria, alarmas, hilos, pendientes, estado, privacidad,
  confirmación y modo desarrollo tienen pruebas de aceptación.
- Puede instalarse y ejecutar smoke tests desde un clon nuevo.
- Los tests nunca usan credenciales ni cuota real por defecto.
- El scheduler pausa Codex a 25 % o menos y reanuda tras el reset.
- Mientras Codex espera, otros trabajos progresan.
- Reiniciar el proceso no pierde la cola.
- Las capacidades puntuables y accesos por formato son legibles por máquina.
- Las 25 tareas están etiquetadas y existe un informe de huecos.
- Existen nuevas tareas sintéticas para los huecos prioritarios.
- Cada resultado conserva evidencia objetiva, juez, latencia y versiones.
- No se ha publicado ningún secreto ni runtime personal.
- Existe una rama `gemini/...` publicada y un PR, o un bloqueo documentado.
- La documentación explica instalación, ejecución, pausa, reanudación y
  reproducción de resultados.

## Decisiones que requieren detenerse y preguntar

- borrar o reescribir trabajo existente;
- cambiar el comportamiento del orquestador operativo actual;
- publicar datos que podrían ser personales;
- fusionar el PR;
- usar una credencial no configurada;
- ejecutar una batería que pueda consumir una cuota importante sin límites;
- adoptar dependencias pesadas o servicios nuevos no presentes en el proyecto.
