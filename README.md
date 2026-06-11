# Inspector

Inspector es un repositorio para probar, comparar y documentar como se comportan distintos sistemas de IA cuando trabajan con una interfaz de linea de comandos, wrappers API y un orquestador de Telegram.

La carpeta esta pensada para ser portable: si copias `d:\inspector` a otro ordenador y mantienes la misma estructura, los lanzadores y los modulos locales siguen funcionando igual.

La idea central es sencilla:

1. Ejecutar las mismas tareas con varios motores.
2. Guardar resultados reproducibles en disco.
3. Documentar el flujo completo para que cualquiera pueda entender que se esta evaluando.
4. Publicar los resultados de cada ronda cuando esten listos.

Regla de transcripcion: cuando el usuario diga Groq y la transcripcion produzca
`Grok`, debe interpretarse siempre como **Groq, con Q**. No se refiere a los
modelos Grok de xAI.

Antes de seguir con cualquier otra cosa, lee [LEEME_PRIMERO.md](LEEME_PRIMERO.md).

Este repositorio esta dividido en dos bloques principales:

- `benchmarks/`: la arena de evaluacion, los motores, las tareas, el juez y los reportes.
- `orchestrator_v2_1/`: el orquestador operativo actual para Telegram, tiers, memoria, voz y modo desarrollo.
- `telegram_codex_orchestrator/`: la implementacion historica conservada para referencia y compatibilidad.
- `assistant/`, `server.js` y `desktop_assistant.py`: el gestor ligero con Tkinter, Telegram, Groq STT, Codex CLI, alarmas y voz.

## Que vas a encontrar aqui

- Una bateria de tareas sinteticas para medir ofimatica, extraccion de datos, redaccion, programacion, investigacion y manejo de archivos.
- Una matriz de motores que compara CLIs agencicos y wrappers API.
- Un orquestador con memoria persistente, alarmas, hilos de contexto y modo GUI.
- Resultados historicos en formato Markdown y JSON para revisarlos y citarlos.
- Documentacion para que el proyecto pueda leerse sin abrir el codigo.

## Que estamos haciendo ahora

En este momento el gestor se ha reconducido a un flujo mas simple:

- cada mensaje es una peticion unica;
- la ejecucion normal va por Codex CLI;
- Codex Desktop solo se usa si el usuario lo pide explicitamente;
- Telegram y Tkinter son entradas/salidas, no el motor principal de razonamiento.

Esta documentacion esta escrita para:

- explicar la arquitectura actual sin cambiar el comportamiento del sistema;
- dejar claro que partes ya estan pensadas para publicacion;
- ordenar el material del proyecto para que sea facil de auditar por la comunidad.

## Que se publicara

Cuando una ronda de prueba termine, se publicaran los artefactos que permiten revisar el experimento:

- `summary.json`
- `report.md`
- resultados por motor y tarea
- comprobaciones clave y judgements cuando existan

Los detalles de la estructura de salida estan descritos en [docs/RESULTS.md](docs/RESULTS.md).

## Documentacion principal

- [LEEME_PRIMERO.md](LEEME_PRIMERO.md)
- [docs/ROUTER_CAPABILITY_MAP_20260608.html](docs/ROUTER_CAPABILITY_MAP_20260608.html)
- [docs/ROUTER_CAPABILITY_MASTER_20260608.md](docs/ROUTER_CAPABILITY_MASTER_20260608.md)
- [docs/EVOLUTIONARY_ROUTER_DESIGN_20260608.md](docs/EVOLUTIONARY_ROUTER_DESIGN_20260608.md)
- [docs/ANTIGRAVITY_REFACTOR_HANDOFF_20260608.md](docs/ANTIGRAVITY_REFACTOR_HANDOFF_20260608.md)
- [docs/ANTIGRAVITY_MASTER_PROMPT_20260608.md](docs/ANTIGRAVITY_MASTER_PROMPT_20260608.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/RESULTS.md](docs/RESULTS.md)
- [docs/MODEL_LAB_SUMMARY.md](docs/MODEL_LAB_SUMMARY.md)
- [docs/CODEX_ONESHOT_RUNTIME.md](docs/CODEX_ONESHOT_RUNTIME.md)
- [docs/RUNTIME.md](docs/RUNTIME.md)
- [docs/ALARMS.md](docs/ALARMS.md)
- [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md)
- [benchmarks/MODEL_STRATEGY.md](benchmarks/MODEL_STRATEGY.md)
- [benchmarks/PROVIDER_MATRIX.md](benchmarks/PROVIDER_MATRIX.md)
- [telegram_codex_orchestrator/README.md](telegram_codex_orchestrator/README.md)

## Arranque rapido

Instalacion base:

```powershell
python -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
```

Gestor conversacional de escritorio:

```powershell
cd /d D:\inspector
.\start_desktop.ps1
```

Backend del gestor sin abrir Tkinter:

```powershell
cd /d D:\inspector
npm start
```

Orquestador Telegram:

```powershell
arrancar_orquestador.bat
```

Este lanzador inicia `orchestrator_v2_1.telegram_gateway`.

Calibracion de Codex Desktop por equipo:

```powershell
calibrar_codex_desktop_por_equipo.bat
```

Uso desde Telegram:

```text
Cd <instruccion>
```

`Cd` fuerza Codex Desktop. Para Codex CLI se usa `/codex <instruccion>`; la letra `C` sola ya no es un comando reservado.

### Ejemplos del modo desarrollo

Los dialogos siguientes son ilustrativos; el texto exacto de las respuestas del bot puede variar.

1. Aprobar una propuesta:

   ```text
   Usuario: activar modo desarrollo
   Bot: Modo desarrollo activado.
   Usuario: Anade una comprobacion del formato de los mensajes.
   Bot: [dev] Propuesta lista para revisar.
   Usuario: si
   Bot: [dev] Propuesta aprobada. Implementando...
   ```

2. Solicitar una revision antes de aprobar:

   ```text
   Usuario: activar modo desarrollo
   Bot: Modo desarrollo activado.
   Usuario: Documenta el arranque del orquestador.
   Bot: [dev] Propuesta lista para revisar.
   Usuario: Limita el cambio al README y anade un ejemplo.
   Bot: [dev] Propuesta actualizada para revisar.
   Usuario: si
   Bot: [dev] Propuesta aprobada. Implementando...
   ```

3. Descartar o cancelar una tarea:

   ```text
   Usuario: activar modo desarrollo
   Bot: Modo desarrollo activado.
   Usuario: Cambia el formato de todas las respuestas.
   Bot: [dev] Propuesta lista para revisar.
   Usuario: no
   Bot: [dev] Propuesta descartada sin ejecutar cambios.

   Para cancelar el proceso en cualquier fase y salir del modo:
   Usuario: desactivar modo desarrollo
   Bot: Modo desarrollo desactivado.
   ```

La descripcion de una tarea genera primero una propuesta. Solo `si` autoriza su implementacion; `no` la descarta y `desactivar modo desarrollo` cancela el proceso activo y vuelve al modo normal.

Interfaz grafica del orquestador:

```powershell
arrancar_orquestador_gui.bat
```

Panel web portable del laboratorio y del gestor v2:

```powershell
arrancar_orquestador_v2_web.bat
```

Preparar o lanzar la creacion de bots del laboratorio con Codex Desktop:

```powershell
medir_xy_raton.bat
consola_clicks_codex.bat
calibrar_codex_desktop.bat
calibrar_codex_desktop_por_equipo.bat
preparar_bots_lab_codex_desktop.bat
crear_bots_lab_codex_desktop.bat
```

Benchmark principal:

```powershell
python .\benchmarks\benchmark_main.py --engine codex
python .\benchmarks\benchmark_main.py --engine codex --engine groq --task test-01
```

## Estructura resumida

- `benchmarks/assets/`: datos de entrada para las pruebas.
- `benchmarks/tasks/`: catalogo de tareas y metadatos.
- `benchmarks/results/`: ejecuciones ya completadas.
- `benchmarks/engines/`: adaptadores para cada motor.
- `benchmarks/judge.py`: comparador ciego para salidas.
- `benchmarks/report_generator.py`: generador de informes.
- `telegram_codex_orchestrator/`: logica del bot, memoria, voz y threads.
- `assistant/`: memoria, transcripcion, router, TTS y alarmas del gestor conversacional.
- `public/`: laboratorio web auxiliar; no es la interfaz principal.
- `desktop_assistant.py`: ventana Tkinter siempre visible.
- `server.js`: backend local del gestor y puente con Telegram.
- `arrancar*.bat`: accesos rapidos para Windows.

## Nota de publicacion

Este repositorio esta pensado para ser publico, pero sin exponer secretos, caches ni estado de ejecucion local. La configuracion sensible debe quedar fuera del control de versiones y los resultados deben publicarse de forma controlada y legible.
