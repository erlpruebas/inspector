# Plan de implementacion para el siguiente motor

Fecha: 2026-06-04

## Objetivo

Convertir `orchestrator_v2_1` en el nucleo principal del gestor personal.

La prioridad ya no es seguir haciendo pruebas sinteticas por tiers. La validacion real vendra de uso humano continuo: el usuario enviara mensajes por Telegram, el sistema enrutara, ejecutara, recordara, pedira confirmaciones cuando haga falta y se ira corrigiendo con la experiencia real.

El laboratorio multibot queda pausado. No migrarlo ahora.

## Glosario minimo

- **Nucleo principal**: `orchestrator_v2_1`. A partir de ahora las nuevas integraciones deben apuntar aqui.
- **Tier**: nivel de herramienta elegida segun capacidad/coste/riesgo.
- **Codex Desktop**: operador visual de escritorio. Solo se usa cuando la tarea requiere una interfaz grafica, navegador autenticado, imagen, mapa, login, sesion abierta o una operacion que un CLI/API no puede resolver bien.
- **HITL**: Human In The Loop. Significa que el humano participa cuando hay riesgo, ambiguedad, credenciales, accion irreversible, pago, datos sensibles, login, 2FA, captcha o decision importante. En la practica: el sistema debe preguntar antes de actuar.
- **Memoria**: historial y datos recordables del usuario, hilos, preferencias, datos personales utiles, correcciones y aprendizajes de uso.

## Decision de producto

`orchestrator_v2_1` no es un laboratorio paralelo. Debe convertirse en la aplicacion final en evolucion.

La version definitiva se construira iterativamente:

1. El usuario prueba casos reales por Telegram.
2. El sistema enruta y ejecuta.
3. Se observa donde falla.
4. Se corrige el router, memoria, prompts o adaptadores.
5. Se repite.

No buscar una arquitectura perfecta antes de usarla. Buscar una arquitectura suficientemente limpia para que el aprendizaje real no genere deuda imposible.

## Arquitectura deseada

Flujo ideal:

```text
Telegram / CLI / voz
  -> normalizacion de mensaje
  -> carga de hilo y memoria
  -> decision de si hay que recuperar contexto
  -> router
  -> politica de privacidad y confirmaciones humanas
  -> ejecucion en tier elegido
  -> respuesta estructurada
  -> persistencia en memoria
  -> respuesta al usuario con texto y adjuntos
```

Regla central:

El nucleo trabaja con estructuras, no con texto parseado de manera fragil.

Ya existe esta idea en `orchestrator_v2_1.models`:

- `TaskRequest`
- `RouteDecision`
- `OrchestratorResult`
- `ResultAttachment`

Mantener y ampliar estos contratos.

## Estado actual de `orchestrator_v2_1`

Archivos creados:

- `models.py`: contratos base.
- `tool_registry.py`: lista de herramientas y tiers.
- `router.py`: politica de enrutamiento inicial.
- `executor.py`: ejecucion local/API/CLI.
- `desktop_adapter.py`: unica frontera con Codex Desktop legacy.
- `telegram_gateway.py`: gateway Telegram simple.
- `cli.py`: CLI de pruebas.
- `AUDIT.md`: auditoria del sistema anterior.
- `README.md`: guia rapida.
- `tests/test_orchestrator_v2_1.py`: tests de aislamiento basico.

Verificacion actual:

```powershell
python -m pytest tests\test_orchestrator_v2_1.py -q
```

Resultado esperado:

```text
5 passed
```

## Problemas heredados que no se deben arrastrar

### 1. Gateway roto en `orchestrator_v2`

`orchestrator_v2/telegram_gateway.py` usaba:

```python
TaskRequest(id=str(uuid4()), ...)
```

Pero el modelo antiguo no tenia campo `id`. Eso rompe en runtime.

No arreglar ese gateway salvo que sea necesario por compatibilidad. La ruta nueva debe ser `orchestrator_v2_1.telegram_gateway`.

### 2. Parseo fragil de capturas

La version anterior buscaba lineas como:

```text
Captura: ...
Tokens extraidos: ...
```

Esto mezcla transporte con formato de salida. En v2.1, los adjuntos visuales deben viajar en `OrchestratorResult.attachments`.

### 3. Codex Desktop mezclado con tiers normales

Codex Desktop no debe ser una capacidad general del executor. Debe vivir solo en `desktop_adapter.py`.

Regla de aislamiento:

Solo `orchestrator_v2_1/desktop_adapter.py` puede importar:

```python
orchestrator_v2.desktop_codex_operator
```

Los tests deben seguir protegiendo esta frontera.

### 4. Laboratorio multibot

No migrar ahora:

- `blind_lab.py`
- `telegram_lab.py`
- scheduler de laboratorio
- profesiones/personas de laboratorio

Queda aparcado hasta nueva orden.

## Politica de enrutamiento

Codex Desktop no debe depender solo de comandos explicitos.

El router debe elegirlo logicamente cuando una tarea no encaja bien en CLI/API.

Casos para Codex Desktop:

- Navegador autenticado.
- Google Maps o tareas donde el resultado visual importa.
- Rutas de un sitio a otro cuando conviene ver mapa, pantalla, horarios o interfaz.
- Login, sesiones abiertas, apps web privadas.
- Tareas que requieren comprobar una imagen o pantalla.
- Acciones en Telegram Desktop, BotFather, YouTube Studio, paneles web autenticados.
- Cuando el usuario pida explicitamente que mire algo visual, que abra una interfaz, que use raton/teclado, que vea una web como humano.

Casos que NO deben ir a Codex Desktop:

- Resumen de texto normal.
- Analisis estrategico sin interfaz visual.
- Codigo local, tests, edicion de repo.
- Busqueda web textual que puede resolverse por API/herramienta sin ver pantalla.
- Lectura de archivos.

Importante:

El usuario no quiere depender de comandos como `cd ...`, aunque pueden seguir existiendo como override manual.

## Memoria antes del router

Esta es la pieza mas importante a implementar ahora.

Antes de decidir el tier final, el sistema debe preguntarse:

```text
Necesito recuperar memoria para entender esta tarea?
```

Ejemplos:

- "dime como llego desde mi casa"
- "mira la direccion que me dijo tal cliente"
- "continua lo de ayer"
- "usa el proveedor que elegimos"
- "mandalo al cliente de la reforma"
- "recuerda mi direccion"

Si hace falta memoria:

1. Buscar en memoria por usuario/hilo.
2. Recuperar hechos relevantes.
3. Inyectarlos en `TaskRequest.metadata` o en un campo nuevo estructurado.
4. Pasar ese contexto al router y al executor.

Propuesta de contrato:

```python
@dataclass(frozen=True)
class MemoryContext:
    facts: tuple[MemoryFact, ...] = ()
    thread_summary: str = ""
    retrieval_query: str = ""
```

Y en `TaskRequest`:

```python
memory_context: MemoryContext = field(default_factory=MemoryContext)
```

Si se quiere evitar tocar demasiado al principio, usar temporalmente:

```python
request.metadata["memory_context"] = {...}
```

Pero la version limpia deberia acabar usando dataclasses.

## Memoria que hay que guardar

Guardar cada interaccion real:

- mensaje original del usuario;
- decision de router;
- memoria recuperada;
- herramienta usada;
- respuesta final;
- errores;
- correcciones del usuario;
- adjuntos relevantes;
- si hubo confirmacion humana;
- si el resultado fue satisfactorio.

Guardar hechos cuando el usuario diga o implique datos persistentes:

- "mi casa esta en..."
- "mi direccion es..."
- "este cliente se llama..."
- "recuerda que..."
- "prefiero que..."
- "cuando diga X me refiero a Y"

No compactar todavia. Primero acumular memoria util y observable. La compactacion vendra despues.

## Confirmaciones humanas

HITL significa preguntar al humano antes de ciertas acciones.

Pedir confirmacion antes de:

- enviar mensajes a terceros;
- publicar;
- borrar;
- comprar;
- pagar;
- cambiar configuraciones importantes;
- usar credenciales;
- continuar si aparece login, 2FA o captcha;
- operar sobre datos sensibles;
- ejecutar Codex Desktop en un contexto donde pueda tocar una sesion privada;
- enviar archivos o imagenes a servicios externos si contienen datos personales.

Primera implementacion recomendada:

Crear un estado simple de `pending_confirmation`.

Flujo:

```text
Usuario pide tarea riesgosa
  -> sistema responde con resumen de accion y pregunta confirmacion
  -> guarda pending_confirmation en memoria/estado
Usuario responde si/no
  -> si: ejecuta
  -> no: cancela
```

Esto puede vivir inicialmente en `telegram_gateway.py`, pero lo correcto es moverlo pronto a un modulo de conversacion:

```text
conversation_state.py
```

## Telegram como interfaz principal

`orchestrator_v2_1.telegram_gateway` debe evolucionar para ser la interfaz principal.

Pendientes:

1. Cargar y guardar memoria por `chat_id`.
2. Soportar hilos/conversaciones.
3. Manejar confirmaciones pendientes.
4. Enviar adjuntos desde `OrchestratorResult.attachments`.
5. Mostrar al usuario que tier se eligio y por que, de forma breve.
6. Permitir correcciones: "no, eso esta mal", "recuerda que...", "la proxima vez usa..."

No meter laboratorio multibot.

## Propuesta de carpetas v2.1

Estructura objetivo:

```text
orchestrator_v2_1/
  __init__.py
  __main__.py
  models.py
  tool_registry.py
  router.py
  orchestrator.py
  executor.py
  desktop_adapter.py
  memory_store.py
  memory_retrieval.py
  conversation_state.py
  telegram_gateway.py
  privacy.py
  cli.py
  README.md
  AUDIT.md
  NEXT_ENGINE_IMPLEMENTATION_PLAN.md
```

No poner runtime versionado.

`.gitignore` ya debe contener:

```text
orchestrator_v2_1/runtime/
```

## Mapa de trabajo por niveles

La evolucion debe organizarse por niveles, pero la validacion sera con tareas reales del usuario. Cada nivel debe producir senales: que resolvio, que no resolvio, que memoria necesito, si pidio confirmacion, y si hubo que escalar.

### Nivel previo: memoria y contexto

Este nivel ocurre antes de elegir herramienta.

Objetivo:

- entender si el mensaje necesita datos recordados;
- recuperar hechos utiles;
- detectar continuidad de hilo;
- decidir si hay riesgo o confirmacion pendiente.

Ejemplos:

- "desde mi casa a la direccion del cliente";
- "continua con lo de ayer";
- "usa el proveedor barato que vimos";
- "recuerda que mi direccion es...";
- "ese cliente era el de la reforma";
- "hazlo como la ultima vez".

Tareas de implementacion:

- crear memoria por usuario e hilo;
- guardar eventos reales;
- recuperar por palabras clave;
- detectar hechos persistentes;
- inyectar memoria recuperada en router y prompts;
- registrar cuando la memoria fue util o insuficiente.

Senal de que funciona:

- el sistema no pregunta de nuevo datos que ya se le dijeron;
- el router cambia de decision cuando la memoria aporta contexto;
- la respuesta cita brevemente que dato recordado uso.

### Tier 1: local y conversacional

Objetivo:

- resolver comandos simples sin modelo externo;
- gestionar estado de conversacion;
- manejar confirmaciones;
- guardar memoria;
- responder ayuda, estado y cancelaciones.

Ejemplos:

- "recuerda que mi casa esta en X";
- "cancela";
- "si, confirmo";
- "no, para";
- "que recuerdas de mi direccion";
- "que estas haciendo";
- "olvida este dato".

Tareas de implementacion:

- `conversation_state.py`;
- confirmaciones pendientes;
- lectura/escritura de memoria;
- comandos de estado;
- cancelacion de tarea activa si existe.

No escalar si:

- la tarea es solo guardar, recuperar o confirmar;
- basta una respuesta deterministica.

### Tier 2: respuesta rapida API

Objetivo:

- contestar preguntas cortas;
- redactar texto simple;
- clasificar intenciones;
- hacer transformaciones ligeras.

Ejemplos:

- "redactame un mensaje amable para este cliente";
- "resume este texto";
- "dame tres opciones de respuesta";
- "clasifica esta peticion";
- "explicame esto rapido".

Tareas de implementacion:

- mantener prompts compactos;
- inyectar memoria solo si es relevante;
- guardar coste/latencia/resultados;
- permitir fallback a Tier 3 si el usuario corrige o pide mas profundidad.

Escalar si:

- la respuesta queda generica;
- hacen falta fuentes;
- hay varios documentos;
- el usuario pide mas precision o dice que no sirve.

### Tier 3: razonamiento, documentos y busqueda

Objetivo:

- sintetizar;
- comparar opciones;
- analizar archivos;
- investigar con fuentes;
- producir recomendaciones con criterio.

Ejemplos:

- "hazme una auditoria de esta decision";
- "compara proveedores";
- "lee estos documentos y dime riesgos";
- "busca alternativas con fuentes";
- "prepara un plan para resolver esto".

Tareas de implementacion:

- prompt con memoria + archivos + criterio de salida;
- separar busqueda web textual de navegacion visual;
- registrar fuentes cuando existan;
- guardar un resumen de decision en memoria.

Escalar si:

- requiere operar un repo o terminal;
- requiere contexto demasiado grande;
- necesita ver una interfaz o imagen;
- el resultado debe validarse visualmente.

### Tier 4: runtime agentico y contexto largo

Objetivo:

- tareas con varios pasos;
- codigo;
- terminal;
- contexto grande;
- cierre premium de problemas complejos.

Ejemplos:

- "implementa esta mejora";
- "arregla los tests";
- "lee toda esta carpeta";
- "haz una refactorizacion";
- "revisa el repo y propon cambios";
- "cierra esta auditoria con criterio alto".

Tareas de implementacion:

- pasar workdir claro;
- conservar logs;
- pedir confirmacion antes de cambios grandes;
- diferenciar edicion local de accion externa;
- registrar commits/archivos tocados si aplica.

Escalar a Desktop si:

- el runtime no puede acceder a una sesion web;
- hace falta ver una pantalla;
- hay login/captcha/2FA;
- la respuesta esperada es visual.

### Tier 5: Codex Desktop visual

Objetivo:

- operar interfaces reales;
- usar navegador autenticado;
- capturar pantalla;
- resolver tareas donde la imagen o el estado visual es parte del resultado.

Ejemplos:

- "mira como llego de mi casa a esta direccion";
- "abre Google Maps y dime la ruta";
- "comprueba en la web del cliente si aparece X";
- "entra en Telegram Desktop y revisa BotFather";
- "mira esta pantalla y dime que ocurre";
- "usa la sesion abierta para descargar este informe".

Tareas de implementacion:

- mantener `desktop_adapter.py` como unica frontera;
- devolver imagenes en `attachments`;
- pedir confirmacion si hay login, 2FA, captcha, pago o accion irreversible;
- guardar evidencias del run;
- resumir que hizo y que vio.

No usar Desktop para:

- busqueda textual normal;
- resumen de documentos;
- redaccion;
- codigo local;
- tareas que no necesitan pantalla.

### Gestion de escalado

El sistema debe aprender de cada escalado.

Regla operativa:

1. empezar en el nivel mas bajo que razonablemente pueda resolver;
2. si falla, guardar por que fallo;
3. si el usuario pide "prueba otro nivel" o corrige, reutilizar contexto y subir;
4. si el fallo indica pantalla/login/mapa/imagen, subir a Desktop;
5. si el fallo indica falta de contexto o documentos, subir a Gemini/contexto largo;
6. si el fallo indica codigo/terminal, subir a runtime agentico;
7. si el fallo indica calidad insuficiente, subir a tier premium.

Datos a guardar por escalado:

- tier inicial;
- tier final;
- motivo de escalado;
- mensaje de correccion del usuario;
- memoria usada;
- resultado aceptado o rechazado.

### Cola de evolucion del producto

El trabajo no debe gestionarse como laboratorio sintetico, sino como backlog vivo basado en conversaciones reales.

Categorias del backlog:

- `routing`: el router eligio mal;
- `memory`: falto recordar o recordo mal;
- `desktop`: hizo falta pantalla o Desktop fallo;
- `hitl`: falto confirmacion o pidio demasiada;
- `telegram`: la conversacion fue incomoda;
- `quality`: la respuesta no fue suficientemente buena;
- `safety`: hubo riesgo con datos, credenciales o acciones.

Cada vez que el usuario corrija al sistema, guardar un evento de aprendizaje. Ejemplos:

- "esto deberia haber ido a Desktop";
- "no hacia falta Desktop";
- "recuerda que mi casa es otra";
- "cuando diga cliente X me refiero a...";
- "esto tenias que preguntarmelo antes";
- "esto puedes hacerlo sin confirmarme".

Esos eventos deben alimentar cambios pequenos y frecuentes en router, memoria y HITL.

## Orden recomendado de implementacion

### Fase 1: memoria minima real

Crear:

- `memory_store.py`
- `memory_retrieval.py`
- tests de memoria

Implementar:

- append de eventos JSONL por usuario;
- busqueda simple por palabras clave;
- extraccion basica de hechos persistentes por reglas;
- inyeccion de memoria en el prompt.

No usar embeddings todavia. Mantener simple.

### Fase 2: router con memoria

Modificar `OrchestratorV21.handle`:

1. recibe `TaskRequest`;
2. recupera memoria relevante;
3. crea request enriquecido;
4. enruta;
5. ejecuta;
6. guarda interaccion.

El router debe recibir suficiente contexto para decidir si una frase como "desde mi casa" implica memoria y probablemente Google Maps/Desktop.

### Fase 3: Telegram principal

Mejorar `telegram_gateway.py`:

- usar `chat_id` como `user_id`;
- guardar interacciones;
- manejar confirmaciones pendientes;
- enviar imagenes adjuntas;
- responder con mensajes cortos y utiles.

### Fase 4: HITL

Crear `conversation_state.py`.

Estados minimos:

- `pending_confirmation`
- `pending_privacy_choice`
- `running_task`

Confirmaciones por texto:

- "si", "sí", "confirmo", "adelante"
- "no", "cancela", "para"

### Fase 5: Codex Desktop robusto

Mantener `desktop_adapter.py` como frontera.

Mejoras:

- si Desktop devuelve screenshot, enviarlo como attachment;
- si devuelve JSON de vision, adjuntarlo y resumirlo;
- si aparece login/2FA/captcha, devolver `needs_human=True` en metadata futura;
- no recortar imagenes arbitrariamente en Telegram; si hace falta crop, que sea un attachment producido por Desktop adapter.

## Cambios concretos que debe hacer el siguiente motor

1. Crear `orchestrator_v2_1/memory_store.py`.
2. Crear `orchestrator_v2_1/memory_retrieval.py`.
3. Ampliar `models.py` con `MemoryFact`, `MemoryContext` y quizas `HumanConfirmation`.
4. Modificar `orchestrator.py` para recuperar memoria antes de enrutar.
5. Modificar `executor.py` para incluir memoria en prompts normales.
6. Modificar `desktop_adapter.py` para incluir memoria en prompts Desktop.
7. Mejorar `telegram_gateway.py` para persistir interacciones y manejar confirmaciones.
8. Crear tests:
   - memoria guarda eventos;
   - memoria recupera "mi casa";
   - router manda "como llego desde mi casa a X" a Desktop si hay memoria de casa;
   - tiers normales no producen attachments de imagen;
   - Desktop sigue aislado.

## Criterios de aceptacion

La siguiente entrega debe cumplir:

- `python -m pytest tests\test_orchestrator_v2_1.py -q` pasa.
- El CLI puede listar tools.
- El CLI puede enrutar una tarea de estrategia sin Desktop.
- El CLI puede enrutar una tarea visual/mapa a Desktop.
- Una memoria tipo "mi casa esta en X" se guarda.
- Una tarea posterior "como llego desde mi casa a Y" recupera X.
- Telegram usa `orchestrator_v2_1`, no `orchestrator_v2`.
- Ningun modulo salvo `desktop_adapter.py` importa `orchestrator_v2.desktop_codex_operator`.

## Riesgos

- Enrutar demasiado a Desktop puede hacer el sistema lento y fragil.
- Enrutar poco a Desktop puede resolver mal tareas visuales.
- Guardar memoria sin control puede acumular ruido.
- Confirmar demasiadas cosas puede volver el sistema pesado.
- Confirmar demasiado poco puede ser peligroso.

La solucion no es decidirlo perfecto hoy. La solucion es registrar bien cada caso real y ajustar.

## Nota para el siguiente motor

No reconstruyas todo.

Lee primero:

1. `orchestrator_v2_1/AUDIT.md`
2. `orchestrator_v2_1/README.md`
3. `orchestrator_v2_1/models.py`
4. `orchestrator_v2_1/router.py`
5. `orchestrator_v2_1/desktop_adapter.py`
6. `tests/test_orchestrator_v2_1.py`

Despues implementa memoria minima y Telegram principal.

El usuario quiere una aplicacion usable ya, aunque luego se refactorice. Prioriza una version completa, observable y corregible sobre una version teoricamente perfecta.
