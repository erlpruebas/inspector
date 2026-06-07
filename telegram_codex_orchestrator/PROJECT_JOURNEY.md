# Project Journey

Run date: 2026-06-04

This document is the summary of the path we took, where the system is now, and where we want to go next.
It is written for implementation handoff and for future maintenance by another agent or another person.

## 1. What we are building

We are building a Telegram-first orchestrator that can:

- receive text and voice from a single authorized user
- maintain a clean operational memory
- store durable user memories and alarms
- route work across multiple tiers
- use fast models for small tasks
- escalate to stronger models when needed
- send two outputs when useful: a full text answer and a short voice summary

The main goal is not raw model capability. The goal is low-friction mobile usage with predictable routing and auditable behavior.

## 2. Where we started

The first version assumed that a single agent surface could cover many tasks:

- CLI work
- desktop work
- memory writes and reads
- alarms

At that stage, the main unknowns were:

- how much latency different surfaces introduce
- whether a single tier could cover public web research well enough
- whether the user experience in Telegram would stay usable when tasks get longer
- whether the system should escalate automatically or ask first

## 3. What we tested

We moved from synthetic assumptions to real measurement.

### 3.1 Tier 3 web research packs

We created several public-web task packs to separate speed from completeness.

Main task shapes:

- single-source concert lookup
- two-source comparison
- citation-heavy technical summary
- two-step company research brief

The tradeoff pack is documented in:

- [benchmarks/TIER3_WEB_RESEARCH_TRADEOFF_RESULTS_20260604.md](/D:/inspector/benchmarks/TIER3_WEB_RESEARCH_TRADEOFF_RESULTS_20260604.md)

### 3.2 Engines evaluated

We measured:

- `groq/compound-mini`
- `groq/compound`
- `gemini_api:gemini-2.5-flash` with `google_search`
- `gemini:gemini-2.5-flash` CLI
- `codex:gpt-5.4-mini`
- `codex:gpt-5.5`

### 3.3 What the measurements showed

For the strict Tier 3 pack, the final picture was:

| Engine | Avg time | Passes | Interpretation |
|---|---:|---:|---|
| Groq `compound-mini` | 2.492s | 1/4 | Fastest, but brittle on comparisons and citations |
| Groq `compound` | 20.672s | 3/4 | Best Groq quality/coverage in this sample |
| Gemini API + `google_search` | 10.281s | 0/4 | Faster than CLI, but too terse on this pack |
| Gemini CLI | 37.945s | 2/4 | Too slow for the default mobile path |
| Codex `gpt-5.4-mini` | 121.051s | 3/4 | Reliable, but too slow to be a middle ground |
| Codex `gpt-5.5` | 105.742s | 4/4 | Best completeness, but the slowest practical option |

The operational conclusion was:

1. `groq/compound-mini` should be the first attempt for simple current-info questions.
2. `groq/compound` should be the next tier when the task asks for multiple sources, explicit citations, or richer synthesis.
3. `codex:gpt-5.5` should be the final escalation when completeness matters and earlier tiers did not close the task.
4. `codex:gpt-5.4-mini` should not be used as a routing step in this system.

### 3.4 Codex CLI reality check

Codex CLI was initially failing because Windows was resolving `codex` to the Microsoft Store alias in `WindowsApps`, which returned `Acceso denegado`.

The standalone binary works and must be forced explicitly in benchmarks:

- `C:\Users\erlqu\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe`

That is the only safe way to measure the real CLI behavior in this environment.

## 4. Current state of the orchestrator

The system now has these pieces in place:

### 4.1 Core behavior

- single authorized user
- Telegram text ingestion
- Telegram audio ingestion
- memory writes and reads
- alarms
- thread tracking
- pending Codex work
- voice state

### 4.2 Evaluation contract

The contract is documented in:

- [telegram_codex_orchestrator/evaluation_contract.md](/D:/inspector/telegram_codex_orchestrator/evaluation_contract.md)

The contract says:

- do not use anonymization in the active phase
- keep live operational memory separate from evaluation history
- log structured events
- do not store raw chain-of-thought
- keep escalation traceable

### 4.3 Voice policy

Current intended behavior:

- voice input from Telegram
- STT order:
  1. Groq + Whisper
  2. Gemini fallback
- text answer is always sent in full
- voice answer is a short narrative summary, at most two paragraphs

### 4.4 Tier map

The tier map we converged on is:

1. Tier 1: local deterministic logic
2. Tier 2: fast LLM for simple natural-language tasks
3. Tier 3: public web research and current-information tasks
4. Tier 4: Codex CLI
5. Tier 5: Codex Desktop

## 5. Final routing direction

The final intended routing policy is:

### Tier 1

Use for:

- memory lookup
- alarm parsing
- thread management
- static commands
- direct local answers

### Tier 2

Use for:

- short rewrites
- clarifications
- simple answers
- intent classification
- lightweight textual tasks

### Tier 3

Use the following policy:

1. Start with `groq/compound-mini`
2. Judge the result with a very fast small model or deterministic checks
3. Escalate to `groq/compound` if the answer is incomplete
4. Escalate to `codex:gpt-5.5` if the task still does not close
5. Never use `codex:gpt-5.4-mini` as an intermediate tier

This tier is for:

- current public facts
- one-source lookups
- two-source comparisons
- citation-heavy summaries
- two-step public-web compilation

### Tier 4

Use Codex CLI for:

- code changes
- shell work
- file edits
- multi-file analysis
- scripted repo changes

### Tier 5

Use Codex Desktop for:

- browser interaction
- UI steps
- visually guided workflows
- tasks that require clicking and watching the screen

## 6. What we learned

### 6.1 Speed is not the same as usefulness

The fastest model is not automatically the best first tier.

`groq/compound-mini` is very fast, but it only works as the default when the task is simple enough that a partial or compact answer is acceptable.

### 6.2 Quality escalates in a staircase

The most useful pattern was not “one model to rule them all”.

The best pattern was:

- cheap first attempt
- fast validation
- only then escalation

### 6.3 Codex is strong, but too expensive to be the first shot on mobile

`codex:gpt-5.5` is the strongest quality result in the Tier 3 research pack, but it is too slow for the user-facing first pass on Telegram.

That makes Codex a great final escalation tier, not the default Tier 3 route.

### 6.4 `gpt-5.4-mini` did not earn a permanent slot

It was slower than expected and did not offer enough advantage over `gpt-5.5` to justify a dedicated escalation step.

## 7. What still needs to be done

The remaining work is mostly implementation hardening and UX refinement:

- make the Tier 3 routing policy explicit in the runtime router
- ensure the fast judge uses cheap deterministic checks first
- keep the escalation prompt short and clear
- verify that the user can ask for the next tier explicitly
- make sure every escalation is logged
- keep the text answer and voice summary separate
- run human-in-the-loop tests over Telegram

## 8. Acceptance criteria for the next phase

We are ready for the human-in-the-loop phase when:

1. Tier 3 starts on `compound-mini` by default
2. The fast judge can reject weak answers without a large-model pass every time
3. The system escalates to `groq/compound` when the answer is incomplete
4. The system escalates to `codex:gpt-5.5` when the task still does not close
5. The live trace shows every meaningful step
6. Audio input and voice output work end to end
7. A reset of operational memory does not destroy evaluation history

## 9. Short version

- We started with a broad agent idea.
- We measured real latency and real quality.
- We learned that Tier 3 should be a staircase, not a single model.
- We settled on `compound-mini` first, `compound` next, and `gpt-5.5` as the final closure tier.
- We ruled out `gpt-5.4-mini` for the routing chain.
- We kept operational memory, evaluation history, audio, and routing separate.
- The system is now ready for human-in-the-loop validation.

## 10. Pulido del agente real desde Telegram

Fecha: 2026-06-06.

La direccion actual deja atras el laboratorio sintetico y se concentra en el uso humano continuo. El objetivo inmediato es que cada mensaje de Telegram permita observar, corregir y mejorar el comportamiento real del agente.

Cambios de esta etapa:

- Cada fase visible termina con una duracion compacta: transcripcion, enrutado, ejecucion, sintesis y reproduccion.
- El router sigue siendo el responsable de elegir el tier; Telegram solo presenta la decision y no resuelve tareas con atajos.
- Las respuestas empiezan por la solucion, sin preambulos, elogios ni reformulaciones innecesarias.
- Todas las respuestas correctas generan un resumen de voz con Gemini, tanto si la entrada fue texto como si fue audio.
- El mismo WAV se envia a Telegram y se reproduce automaticamente en el altavoz del ordenador.
- La configuracion de voz queda en Markdown de proyecto y en un JSON operativo pequeno: `orchestrator_v2_1/runtime/voice_settings.json`.
- Las interacciones y decisiones siguen entrando en la memoria Markdown para poder revisarlas y compactarlas despues.

La siguiente fase consiste en enviar peticiones reales de dificultad creciente, observar rutas, tiempos, calidad de texto y calidad de audio, y registrar las correcciones que surjan del uso.

### Ajuste de presentacion

- Las duraciones se reducen al formato `2s`.
- El aviso de ruta muestra tambien el motor/modelo efectivo.
- La reproduccion del altavoz se notifica al lanzar el reproductor, sin esperar a que termine el audio.
- En esa etapa, una barra `----------` marcaba de forma discreta el final de cada respuesta completa; despues fue sustituida por el estado de las ventanas Codex.

### Comparativa de sintesis de voz

Medicion local con la misma frase en espanol:

- Gemini TTS: `34.862s` en frio; `11.598s` y `11.030s` en caliente.
- Windows SAPI: `2.230s` en frio; `0.432s` y `0.460s` en caliente.
- Edge TTS neural, Elvira: `1.257s`, `0.876s` y `0.522s`.
- Edge TTS neural, Alvaro: `4.045s`, `1.195s` y `0.503s`.
- ElevenLabs Flash v2.5 estaba configurado, pero la credencial disponible respondio `401`, por lo que no pudo medirse.

Se adopta Edge TTS con `es-ES-ElviraNeural`: queda muy cerca de la velocidad local de Windows, con una voz neural mas natural y una mejora aproximada de veinte veces frente a Gemini caliente.

La medicion de extremo a extremo separo dos costes: el resumen oral con Groq tarda entre `2.4s` y `3.5s`, mientras Edge caliente tarda alrededor de `0.9s`. Para no pagar ese segundo modelo cuando la respuesta ya es breve, los textos de hasta 700 caracteres pasan directamente a TTS. Edge se precalienta al iniciar el gateway para absorber su primera conexion lenta fuera de la conversacion.

La clave de ElevenLabs termino siendo valida pero restringida: no permite leer usuario, modelos ni listado de voces. La sintesis directa si funciona. Con Flash v2.5, Adam produjo audio en `1.368s` y George entre `1.410s` y `1.637s`. Rachel quedo bloqueada por una limitacion del plan. ElevenLabs se incorpora como proveedor seleccionable sin sustituir todavia a Edge, a la espera de comparar las muestras por oido.

Comparacion final en caliente, con archivos enviados al Telegram real:

- Windows SAPI: `0.135s`.
- Edge Elvira Neural: `0.721s`.
- ElevenLabs Adam Flash: `2.532s`.
- ElevenLabs George Flash: `2.541s`.
- Gemini Kore: `26.036s` en la muestra final.

Los cinco audios se enviaron correctamente al bot para evaluacion humana. Edge permanece como proveedor activo por su equilibrio entre velocidad y naturalidad; ElevenLabs queda funcional y seleccionable.

Se activa temporalmente un modo comparativo por respuesta: Edge Elvira y ElevenLabs Flash v2.5 con Laura. Telegram recibe ambos archivos y sus tiempos; el altavoz los reproduce de forma secuencial para que la comparacion sea clara. Matilda y Jessica tambien quedaron enviadas como candidatas femeninas.

### Decision definitiva de voz

Tras escuchar las muestras, se elige Edge `es-ES-ElviraNeural` como unica voz activa. ElevenLabs mejora algo la calidad general, pero las voces disponibles no ofrecen el acento femenino de espanol de Espana buscado y no compensan la espera adicional. El codigo de ElevenLabs se conserva como alternativa, con el modo comparativo desactivado.

La siguiente direccion de producto que se esta evaluando es un modo `clave desarrollo`: Telegram capturaria correcciones de desarrollo y las entregaria a Codex CLI en una ejecucion nueva, usando el cuaderno vivo como memoria persistente en lugar de alargar indefinidamente una conversacion.

### Ventanas de uso de Codex

Se sustituye la barra final de Telegram por dos porcentajes compactos:

```text
70% 17.15 60% 25/3
```

El primer valor indica el porcentaje restante de la ventana de cinco horas y va seguido de la hora local de reinicio. El segundo indica el porcentaje restante semanal y va seguido de la fecha local de reinicio. La API experimental de Codex entrega `usedPercent` y `resetsAt`; el orquestador calcula `100 - usedPercent` y convierte el timestamp a la zona horaria local.

La integracion usa una unica instancia persistente de `codex app-server` con el metodo JSON-RPC `account/rateLimits/read`. Un hilo en segundo plano refresca una cache cada 30 segundos. La respuesta principal nunca inicia un subproceso ni espera una consulta. Si el monitor no dispone de datos validos, el pie se omite.

La implementacion se verifico contra Codex CLI `0.137.0`. Durante la prueba real, el snapshot mostro `89%` y `38%` usados, equivalentes a `11% y 62%` restantes; una lectura posterior mostro `8% y 61%` restantes. La comprobacion final del formato completo produjo `4% 23.07 61% 11/6`.

### Modo desarrollo desde Telegram

Se incorpora un circuito persistente por chat que se activa con `activar modo desarrollo` y se abandona con `desactivar modo desarrollo`. Dentro de este modo, una peticion no modifica inmediatamente el agente: Codex CLI inspecciona primero un worktree desechable y devuelve una propuesta estructurada. Aunque el proceso de analisis escribiera accidentalmente en esa copia, se elimina sin alterar el proyecto principal. El usuario puede aprobarla con `si`, descartarla con `no` o escribir correcciones sucesivas hasta obtener la version deseada.

La implementacion aprobada se ejecuta en segundo plano dentro de un `git worktree` temporal. Esto mantiene Telegram receptivo, permite cancelar el proceso y evita mezclar una ejecucion incompleta con el arbol principal. Codex trabaja con sandbox `workspace-write`, la variante nativa de Windows `unelevated` y sin escaladas interactivas; el controlador crea el commit, lo incorpora a la rama activa y trata de publicarlo. El informe final vuelve como texto y resumen de voz, mientras el modo desarrollo permanece activo para la siguiente mejora.

Todas las respuestas de esta conversacion de desarrollo pasan por la misma entrega multimedia que el agente normal: texto completo en Telegram, resumen con Edge enviado al movil y reproduccion local. Despues del audio, el ultimo mensaje muestra siempre el porcentaje restante y el reinicio de las ventanas Codex. Esto se aplica tambien a activacion, propuestas, revisiones, descartes y errores, no solo al informe final de implementacion.

### Ejemplos de uso documentados

Fecha: 2026-06-07.

El README principal incorpora tres ejemplos breves del modo desarrollo por Telegram: aprobar una propuesta con `si`, pedir una revision antes de aprobar y descartar o cancelar una tarea con `no` o `desactivar modo desarrollo`. Los ejemplos remarcan que describir el cambio solo genera una propuesta y que la implementacion no empieza hasta recibir la aprobacion.

La primera implementacion real termino correctamente dentro del worktree, pero el `cherry-pick` fallo porque el cuaderno habia avanzado en la rama principal mientras Codex trabajaba desde un commit anterior. Se recupero el commit temporal `063647d`, se incorporaron sus cambios y se corrigio el publicador: ahora rebasa sobre el `HEAD` vigente antes de aplicar, conserva una rama de rescate si persiste el conflicto y registra el diagnostico completo en Markdown.
