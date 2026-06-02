# Plan: Gemini, Codex CLI, Codex Desktop y memoria total

## Objetivo

Gemini debe actuar como capa de comprension y planificacion:

- entender lenguaje humano;
- decidir si la peticion sigue una conversacion existente o abre una nueva;
- enriquecer la orden con contexto y memoria;
- enviar la ejecucion a Codex CLI o Codex Desktop;
- funcionar como fallback cuando Codex no este disponible.

Codex CLI y Codex Desktop siguen siendo los ejecutores principales. Gemini no sustituye a Codex salvo confirmacion o fallback configurado.

## Prefijos operativos

- `Cd <instruccion>` fuerza Codex Desktop.
- `/codex <instruccion>` fuerza Codex CLI.
- `C <instruccion>` deja de ser comando reservado.

## Memoria total

La memoria total deberia registrar cada ciclo con:

- timestamp;
- usuario/canal/hilo;
- texto original;
- archivos adjuntos relevantes;
- decision del router;
- herramienta usada;
- prompt final enviado;
- resultado final;
- errores y fallback si existieron.

Esta memoria se puede usar despues para:

- recordar preferencias explicitas del usuario;
- reconstruir tareas antiguas;
- compilar respuestas frente a preguntas del usuario;
- alimentar a Gemini con contexto breve y relevante.

## Flujo propuesto

1. Llega mensaje por Telegram.
2. Se guarda inmediatamente en memoria total.
3. Gemini clasifica:
   - nueva conversacion;
   - continuacion;
   - recuerdo;
   - alarma;
   - tarea para Codex CLI;
   - tarea para Codex Desktop.
4. Se recupera contexto del hilo y memorias relevantes.
5. Se construye una orden final para la herramienta elegida.
6. Se ejecuta Codex CLI o Codex Desktop.
7. Se guarda resultado final, estado y capturas si existen.
8. Si Codex falla, se pregunta:
   - reintentar automaticamente cuando vuelva a estar disponible;
   - ejecutar con Gemini como fallback.

## Decisiones pendientes

- Si Gemini debe ejecutar fallback automaticamente o pedir siempre confirmacion.
- Como representar tareas pendientes de Codex Desktop en cola.
- Cuanto contexto de memoria incluir en cada prompt para no saturar ni filtrar informacion innecesaria.
- Si la memoria total se guarda solo como JSONL o tambien como indice resumido por hilo.
- Si la respuesta de Gemini fallback debe marcarse claramente como no ejecutada por Codex.

