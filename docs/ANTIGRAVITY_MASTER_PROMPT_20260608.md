# Prompt maestro para Antigravity / Gemini

Copia desde la línea siguiente:

---

Estás trabajando en el repositorio Windows `D:\inspector`.

Tu misión es diseñar, implementar, verificar y preparar para publicación
**Inspector Agent 2.2**, una versión limpia y autocontenida dentro de la carpeta
`agent_v2_2/`.

Agent 2.2 debe conservar todas las funcionalidades útiles ya existentes. No es
un laboratorio reducido. La referencia funcional combinada está en
`orchestrator_v2_1/` y `telegram_codex_orchestrator/`.

Antes de hacer cambios:

1. Lee íntegramente
   `docs/ANTIGRAVITY_REFACTOR_HANDOFF_20260608.md`.
2. Sigue su lista de lectura obligatoria en el orden indicado.
3. Inspecciona `git status` y asume que todos los cambios existentes pertenecen
   al usuario. No los reviertas, borres ni ocultes.
4. Comprueba las herramientas instaladas y la configuración por presencia,
   pero no muestres, copies ni publiques valores de credenciales.
5. Escribe primero `agent_v2_2/docs/IMPLEMENTATION_PLAN.md` con arquitectura,
   fases, riesgos y criterios verificables.

Restricciones fundamentales:

- No utilices Codex, ChatGPT ni modelos GPT para programar, revisar o juzgar
  durante esta refactorización.
- Usa las capacidades de Antigravity/Gemini y las credenciales de Google ya
  configuradas en el equipo.
- No leas secretos salvo mediante los cargadores existentes y nunca imprimas
  sus valores.
- No ejecutes `git reset --hard`, `git checkout --`, `git clean`, borrados
  recursivos ni stashing destructivo.
- No modifiques las implementaciones antiguas salvo documentación o ignore
  imprescindibles. Son referencia y red de seguridad.
- `agent_v2_2` no puede importar código de `orchestrator_v2_1`,
  `orchestrator_v2` ni `telegram_codex_orchestrator`.
- No uses paths absolutos en la nueva implementación.
- No ejecutes benchmarks costosos sin un presupuesto y una matriz explícitos.

Resultados obligatorios:

1. Paquete autocontenido `agent_v2_2/`, portable a otro ordenador Windows.
2. Matriz completa
   `agent_v2_2/docs/FUNCTIONAL_PARITY_MATRIX.md`, siguiendo la sección
   «Paridad funcional obligatoria» del handoff.
3. Paridad probada de:
   - Telegram, texto, voz y archivos;
   - STT, resumen oral, TTS, envío de audio y altavoz;
   - memoria por usuario e hilo, compactación y recuperación relevante;
   - alarmas únicas y recurrentes;
   - hilos, cola pendiente, detener y reanudar;
   - estado y explicación de capacidades;
   - privacidad y confirmación humana;
   - modo desarrollo y su ciclo aislado de Git;
   - monitor de cuota Codex;
   - routing, fallbacks, adjuntos, tiempos y trazas.
4. Catálogo legible por máquina con:
   - las 17 capacidades puntuables descritas en el handoff;
   - accesos `unsupported`, `prepared` o `direct`;
   - operaciones por formato: leer, extraer, crear, modificar, conservar y
     verificar;
   - familias de texto, Office, PDF, imagen, audio, comprimidos, correo,
     código y carpetas.
5. Batería auditada mediante matriz
   `capacidad × formato × operación × dificultad`.
6. Etiquetado de las 25 tareas actuales y creación de tareas sintéticas para
   los huecos prioritarios, con smoke suite, suites por capacidad y suite lenta.
7. Arena que ejecute únicamente combinaciones compatibles.
8. Comprobaciones objetivas antes de cualquier nota de juez.
9. Juez Gemini habitual y juez Codex 5.5 opcional/aplazable.
10. Registro de experiencias por
   `herramienta × capacidad × forma de tarea`, incluyendo latencia, notas,
   confianza, versiones y causa de fallo.
11. Scheduler persistente y reanudable.
12. Guardia de cuota Codex basada en el protocolo probado de
    `orchestrator_v2_1/codex_rate_limits.py`.

Comportamiento exacto de la cuota Codex:

- Consulta un snapshot fresco antes de cualquier trabajo Codex, incluido
  Codex como juez.
- Si queda 25 % o menos de la ventana de cinco horas, no inicia el trabajo.
- Guarda la hora de reset y aplaza el trabajo hasta esa hora más un margen
  configurable.
- Continúa mientras tanto con Gemini, Groq, OpenRouter, comprobadores y tareas
  de preparación.
- Si no puede leer la cuota o el snapshot ha caducado, difiere Codex de forma
  segura.
- Persiste la cola y reanuda después de reiniciar el ordenador.
- Prueba la lógica con snapshots falsos; los tests no deben consumir Codex.

Política de selección:

```text
compatibilidad técnica obligatoria
-> evidencia objetiva suficiente
-> nota y confianza suficientes para esa capacidad y forma de tarea
-> menor latencia demostrada
```

No calcules una única nota global por modelo. No mezcles baterías distintas
como si fueran directamente comparables. Toda cifra debe indicar muestra,
batería, versión y fecha.

Flujo de Git:

1. Trabaja en una rama nueva `gemini/agent-v2-2`.
2. Audita secretos, runtimes, resultados voluminosos y archivos locales.
3. Crea commits pequeños y temáticos.
4. Ejecuta pruebas y documenta resultados reales.
5. Publica la rama en
   `https://github.com/erlpruebas/inspector.git`.
6. Abre un pull request, pero no lo fusiones.
7. Si GitHub no está autenticado, deja los commits preparados y documenta el
   bloqueo sin solicitar ni mostrar tokens.

Trabaja por fases y no te detengas después de escribir un plan. Implementa,
prueba y documenta cada fase. Al terminar entrega:

- resumen de arquitectura;
- archivos creados o modificados;
- cobertura de capacidades y huecos restantes;
- pruebas ejecutadas y resultados;
- estado del scheduler de cuota;
- estado Git, rama, commits, push y PR;
- instrucciones exactas para clonar y continuar en el otro equipo;
- riesgos y decisiones pendientes.

No sustituyas la implementación operativa actual hasta que la matriz de
paridad esté completa y se haya ejecutado una prueba end-to-end de Telegram.
Cuando una función histórica no encaje en el diseño nuevo, mantenla mediante
un adaptador claro o documenta la decisión y solicita aprobación antes de
excluirla.

No declares completada la misión si Agent 2.2 todavía depende de una versión
anterior, si la cola no sobrevive reinicios, si los tests pueden gastar Codex
sin guardia, o si no se ha auditado la publicación.

---
