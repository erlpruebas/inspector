# Orchestrator V2

Nuevo nucleo del gestor. La palabra estable es **herramienta**:

Una herramienta es cualquier manera de resolver una tarea:

- API directa: `groq:*`, `openrouter:*`
- CLI agentico: `codex:*`, `gemini:*`
- Runtime agentico externo: `opencode:*`, `groq/compound*`

## Interfaces graficas

Hay dos interfaces visuales pensadas para trabajar sin abrir el codigo:

- Panel web del laboratorio y del gestor: `python -m orchestrator_v2.web_ui --open`
- Interfaz humana local minima: `python -m orchestrator_v2.desktop_voice_button`

El panel web permite:

- configurar los 4 bots de Telegram;
- elegir profesiones y tareas;
- lanzar corridas del laboratorio;
- ver tablas de resultados y tokens;
- generar y guardar nuevas profesiones;
- enviar comandos al gestor;
- grabar una nota de voz desde el navegador.

Todo esta pensado para que copiar la carpeta `d:\inspector` a otro ordenador siga dejando el sistema usable con la misma estructura.

## Decision actual

Resultados principales usados:

- `benchmarks/results/20260521_174516_442823`
- `benchmarks/results/orchestrator_probe_report_20260521.md`

Roles iniciales:

| Rol | Herramienta candidata |
| --- | --- |
| Router rapido equilibrado | `groq:qwen/qwen3-32b` |
| Router ultra rapido | `groq:llama-3.1-8b-instant` |
| Worker barato API | `openrouter:deepseek/deepseek-v3.2` |
| Worker razonador API | `openrouter:openai/gpt-5.4-mini` |
| Runtime cloud con herramientas | `groq:groq/compound-mini` |
| Runtime CLI externo | `opencode:openrouter/deepseek/deepseek-v3.2` |
| Contexto largo moderado | `gemini:gemini-2.5-flash` |
| Contexto largo fuerte | `gemini:gemini-2.5-pro` |
| Juez/escalado premium | `codex:gpt-5.5` |

## Uso local

Listar herramientas:

```powershell
python -m orchestrator_v2.cli --list-tools
```

Ver solo ruta:

```powershell
python -m orchestrator_v2.cli --route-only "Resume este CSV y detecta anomalias" --file benchmarks/assets/assistant_synthetic/gastos_2026_02.csv
```

Ejecutar:

```powershell
python -m orchestrator_v2.cli "Extrae tareas pendientes de este archivo" --file benchmarks/assets/assistant_synthetic/notas_voz.jsonl --privacy clear
```

Forzar herramienta:

```powershell
python -m orchestrator_v2.cli "Investiga alternativas con fuentes" --tool worker_groq_compound_mini --privacy clear
```

## Privacidad

El modo por defecto es `ask`. Si el texto parece contener PII, el gestor no ejecuta
directamente y pide confirmar `redacted`, `mixed` o `clear`.

Modos:

- `clear`: no anonimiza.
- `mixed`: conserva original + token para auditoria humana.
- `redacted`: usa tokens antes de enviar a modelos externos.
- `ask`: decide si necesita confirmacion.

## Siguiente integracion

Esta carpeta es el nucleo local. La siguiente capa debe conectar:

- Telegram multiusuario.
- Memoria de hilos.
- Cola de tareas.
- Confirmaciones de privacidad.
- Laboratorio ciego que hable por Telegram con este gestor.

## Modulos nuevos

- `ARCHITECTURE.md`: contrato de arquitectura y decisiones pivotables.
- `settings.py`: preferencias por usuario, voz, horarios y privacidad.
- `config_wizard.py`: preguntas base para `vamos a configurar`.
- `workspace.py`: compartimentos por usuario e hilo.
- `memory_store.py`: eventos, indice de palabras clave y notas de procedimiento.
- `voice_io.py`: Whisper local `large-v3` con fallback Groq.
- `desktop_user_ui.py`: panel humano Tkinter minimo con un unico boton. Verde espera, rojo graba, transcribe con Whisper, confirma por altavoz y acepta si/no por voz.
- `desktop_voice_button.py`: entrypoint compatible que abre la interfaz humana local.
- `web_ui.py`: dashboard web portable para laboratorio, profesiones, resultados y gestor.
- `desktop_codex_operator.py`: operador experimental de Codex Desktop para navegador, logins, BotFather y apps visuales. Tiene modo de borrador para pegar, capturar pantalla y esperar validacion antes de enviar.
- `calibrate_codex_desktop.py`: calibracion de coordenadas fijas para `Nuevo chat`, caja de texto y boton de enviar.
- `codex_desktop_calibrator.py`: calibrador guiado por equipo con selector de aplicacion y captura del siguiente clic.
- `mouse_coordinate_probe.py`: visor siempre visible para apuntar coordenadas XY del raton en distintos estados de Codex Desktop.
- `codex_click_console.py`: consola de prueba con botones para hacer clic en los puntos fijos de Codex Desktop.
- `response_voice.py`: regla de resumen de audio para respuestas largas.
- `blind_lab.py`: estructura del laboratorio ciego multiusuario.
- `lab_contracts.py`: contratos de profesion, tarea, persona, bot y activacion.
- `catalog_loader.py`: carga `benchmarks/contracts/office_general` y personas existentes.
- `lab_scheduler.py`: reparte tareas entre personas con velocidad fija/jitter/burst.
- `telegram_lab.py`: dry-run y transporte Telegram grupo/bots.
- `lab_evaluator.py`: evaluacion automatica basica y prompt para juez de excelencia.
- `task_generator.py`: prompt y escritura de nuevas profesiones/tareas/assets.
- `lab_cli.py`: comandos del laboratorio.
- `email_gateway.py`: base SMTP/IMAP con clave de aplicacion.
- `.env.example`: variables exactas que faltan por credencial.
- `token_report.py`: resumen de tokens desde JSONL compartidos.

Lanzar interfaz local de voz:

```powershell
python -m orchestrator_v2.desktop_voice_button
```

Flujo de uso:

- Boton verde: pulsa una vez para empezar a grabar.
- Boton rojo: pulsa otra vez para parar.
- El sistema transcribe y responde por altavoz: "He entendido... voy a utilizar... quieres que lo realice?"
- Vuelve a pulsar, responde por voz "si" o "no", y para la grabacion.

Abrir el panel web:

```powershell
python -m orchestrator_v2.web_ui --open
```

Arranque rapido del paquete:

```powershell
python -m orchestrator_v2 --list-tools
```

Resumen del catalogo de laboratorio:

```powershell
python -m orchestrator_v2.lab_cli catalog
```

Activacion en seco con evidencias:

```powershell
python -m orchestrator_v2.lab_cli activate --max-tasks 4 --speed-seconds 30 --speed-mode jitter
```

Prompt para generar nueva profesion con modelos de excelencia:

```powershell
python -m orchestrator_v2.lab_cli generate-prompt --title "Asesoria fiscal" --description "Profesional que delega revision de documentos, plazos y comunicaciones" --task-count 20
```

Resumen de tokens:

```powershell
python token_report.py orchestrator_v2/runtime/token_usage.jsonl
```

Preparar creacion de los 4 bots del laboratorio con Codex Desktop:

```powershell
python -m orchestrator_v2.desktop_codex_operator --botfather-lab
```

Enviar realmente la orden a Codex Desktop:

```powershell
python -m orchestrator_v2.desktop_codex_operator --botfather-lab --send
```

Modo seguro con revisado visual antes de enviar:

```powershell
python -m orchestrator_v2.desktop_codex_operator --botfather-lab --pause-after-paste --debug-draft
```

Ese modo deja una captura en `orchestrator_v2/runtime/desktop_codex_operator/<timestamp>/draft_screen.png` y no pulsa enviar hasta reanudar la orden de forma manual.

Calibrar los tres clics fijos de Codex Desktop:

```powershell
python -m orchestrator_v2.calibrate_codex_desktop
```

Calibrador guiado por equipo para Codex Desktop:

```powershell
python -m orchestrator_v2.codex_desktop_calibrator
```

Abrir visor vivo de coordenadas del raton:

```powershell
python -m orchestrator_v2.mouse_coordinate_probe
```

Abrir consola de clicks fijos:

```powershell
python -m orchestrator_v2.codex_click_console
```

Perfil actual de clicks:

- `new_chat`: `71,47`
- `initial_input`: `782,491`
- `initial_send`: `1100,516`
- `initial_stop_no_browser`: `1373,988`
- `browser_toggle`: `1900,50`
- `browser_input`: `532,955`
- `browser_send_stop`: `770,989`

Regla operativa: el foco de Codex Desktop se obtiene por titulo de ventana con UI Automation, no por coordenada de barra de tareas. Si el navegador no esta abierto y la tarea lo necesita, se abre desde `browser_toggle`; despues los seguimientos usan siempre `browser_input` y `browser_send_stop`.

Listar ventanas detectables:

```powershell
python -m orchestrator_v2.desktop_codex_operator --list-windows
```
