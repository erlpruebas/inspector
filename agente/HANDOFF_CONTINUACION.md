# HANDOFF: Continuación del Proyecto Inspector-Agent + GAIA Benchmark

**Fecha de cierre de sesión**: 2026-06-03 17:47 (hora local: UTC+2)  
**Cuaderno de actualización completo**: `d:/cuaderno_actualizaciones.md`

---

## 1. ¿Qué es este proyecto?

Un agente de IA autónomo que funciona vía Telegram, accede a Codex CLI para resolver tareas complejas (código, archivos, audio, imágenes, web), y está siendo evaluado con el **benchmark GAIA** (Global Agentic Intelligence Assessment) de Hugging Face.

### Componentes principales

| Componente | Ruta | Descripción |
|---|---|---|
| **Agente (Orquestador)** | `d:/inspector/agente/telegram_codex_orchestrator/orchestrator.py` | Bot de Telegram que recibe instrucciones, las clasifica y las despacha a Codex CLI. |
| **Configuración del agente** | `d:/inspector/agente/telegram_codex_orchestrator/config.py` | Carga variables de entorno y construye el objeto `Settings`. |
| **Credenciales / entorno** | `d:/inspector/.env`, `d:/variables/.env`, `d:/credenciales` | Tokens y claves API. |
| **Gaiabench** | `d:/gaiabench/` | Servidor web (FastAPI/Uvicorn, puerto 8080) que ejecuta las tareas de GAIA y evalúa las respuestas del agente. |
| **Bus de comunicación local** | `d:/local_telegram_bus/` | Sistema de archivos JSON que emula la API de Telegram localmente (evita la restricción bot-a-bot). |
| **Historial de pruebas** | `d:/gaiabench/config.json` | Guarda el resultado (Correct/Incorrect) de cada tarea ejecutada. |
| **Dataset GAIA** | `d:/gaiabench/data/2023/validation/metadata.parquet` | 165 tareas oficiales: 53 Nivel 1, 86 Nivel 2, 26 Nivel 3. |

---

## 2. Estado actual del código (post-sesión)

### Modo Laboratorio implementado y funcional

El **Lab Mode** es un flag especial que activa el entorno de evaluación automática. Está controlado por la variable `ORCH_LAB_MODE=1`.

**Lo que hace Lab Mode:**
- `hot_reload = False` → No se reinicia el orquestador al cambiar archivos.
- `bypass_confirmation = True` → No pide confirmación antes de ejecutar Codex.
- `codex_timeout_seconds = 600` → Timeout estricto de 10 minutos por tarea.
- El orquestador **espera bloqueante** si Codex ya está ocupado (no responde "ocupado" ni encola).
- Si Codex supera los 10 minutos, devuelve exactamente: `"La tarea no se ha podido realizar por timeout de 10 minutos."`.
- `/restart` queda desactivado en lab mode.

**Comando dinámico desde Telegram:**
```
/lab_mode on   → activa lab mode, guarda en .env del workspace
/lab_mode off  → desactiva lab mode
/lab_mode      → muestra el estado actual
```

---

## 3. Cómo arrancar el sistema

### Paso 1: Limpiar el bus local (SIEMPRE antes de un nuevo run)
```powershell
D:\inspector\.venv\Scripts\python.exe d:\gaiabench\scratch\clear_bus.py
```

### Paso 2: Arrancar el Orquestador del Agente en modo laboratorio
```powershell
$env:ORCH_LAB_MODE='1'
$env:TELEGRAM_TRANSPORT='local'
$env:TELEGRAM_ALLOWED_USER_ID='-1004226057414'
D:\inspector\.venv\Scripts\python.exe d:\inspector\agente\telegram_codex_orchestrator\orchestrator.py
```

### Paso 3: Arrancar Gaiabench (en otra terminal)
```powershell
# La venv del inspector tiene httpx y otras deps necesarias
# El sistema python de Windows también funciona (tiene uvicorn instalado)
cd d:\gaiabench
python -m uvicorn main:app --host 127.0.0.1 --port 8080
```

### Paso 4: Re-ejecutar solo las tareas fallidas del Nivel 1
```powershell
python d:\gaiabench\run_failed_tasks.py
```

### Paso 5: Ejecutar todas las tareas del Nivel 1 (si se quiere resetear)
```powershell
D:\inspector\.venv\Scripts\python.exe d:\gaiabench\run_level_1.py
```

### Paso 6: Generar el informe HTML
```powershell
python d:\gaiabench\generate_report.py
start d:\gaiabench\report.html
```

---

## 4. Resultados actuales del benchmark (Nivel 1)

**Estado**: `d:/gaiabench/config.json` — 55 tareas ejecutadas.

| Métrica | Valor |
|---|---|
| Tareas ejecutadas | 55 |
| **Correctas** | **26 (47.3%)** |
| **Incorrectas** | **29 (52.7%)** |
| Timeout reales | 1 (tarea de ajedrez cca530fc, >7 minutos) |
| Fallos en cascada | 11 tareas (respondieron "Codex ocupado" — BUG ya corregido) |

**Informe visual completo**: `d:/gaiabench/report.html`

### Tareas pendientes de re-ejecución (29 Incorrectas)

Las tareas marcadas "Codex está ocupado" se deben a un bug ya corregido. Hay dos categorías:

**Categoría A — Fallos reales del agente** (necesitan análisis):
- `27d5d136` — Equivalencias lógicas (Respuesta incorrecta)
- `3cef3a44` — Vegetales en lista de compras (Respuesta incorrecta)
- `46719c30` — Título de paper académico (Respuesta incorrecta)
- `5cfb274c` — Hamiltonian path en hoja Excel (Respuesta incorrecta)
- `7673d772` — Palabra reservada Python (respondió "except" en vez de otra)
- `7bd855d8` — Suma de ventas en Excel (valores incorrectos)
- `8e867cd7` — Conteo en problema lógico (Respuesta incorrecta)
- `9318445f` — Fracciones en imagen PNG (Respuesta incorrecta)
- `99c9cc74` — Ingredientes de receta en audio (Respuesta incorrecta)
- `a3fbeb63` — Pregunta sobre paper (Respuesta incorrecta)
- `c365c1c7` — Pregunta geográfica (Respuesta incorrecta)
- `cca530fc` — Posición ajedrez en imagen (Timeout >10 min — difícil)

**Categoría B — "Comando no reconocido"** (clasificador de intents):
- `4b650a35`, `5d0080cb`, `65afbc8a`, `72e110e7`, `840bfca7`, `a1e91b78`

**Categoría C — "Codex ocupado" (BUG ya corregido)**:
- `cf106601`, `cffe0e32`, `d0633230`, `dc22a632`, `dc28cf18`, `e142056d`, `e1fc63a2`, `ec09fa32`, `f918266a`

---

## 5. Problemas conocidos y próximos pasos

### Problema 1: Clasificador de intents (Categoría B)
Las tareas en Categoría B devuelven "Comando no reconocido" — esto significa que el clasificador de intents (`d:/inspector/agente/telegram_codex_orchestrator/intent.py`) está rechazando el mensaje como un comando válido para Codex.

**Causa probable**: El mensaje no lleva el prefijo esperado (ej. `/codex` o `Cd`) y el clasificador de Google (Gemini) no lo está clasificando como `codex_task`.

**Solución sugerida**: En modo laboratorio, añadir un fallback en el orquestador para que cualquier mensaje que llegue del chat_id del laboratorio (= `TELEGRAM_ALLOWED_USER_ID`) se envíe directamente a Codex sin pasar por el clasificador.

### Problema 2: Tarea de ajedrez (cca530fc)
Requiere analizar una imagen de tablero de ajedrez y calcular el mejor movimiento. La tarea tardó más de 7 minutos en la sesión anterior. Con el nuevo timeout de 10 minutos debería completarse, pero es la tarea más difícil del Nivel 1.

### Problema 3: Niveles 2 y 3
Las 86 tareas de Nivel 2 y 26 de Nivel 3 aún no se han ejecutado.

---

## 6. Arquitectura del Bus Local (Mock Telegram)

```
d:/local_telegram_bus/
  ├── updates_controller/   ← Gaiabench escribe aquí (mensajes al agente)
  │     update_1001.json    ← format: Telegram update estándar (JSON)
  │     update_1002.json
  ├── updates_agent/        ← El agente escribe aquí (respuestas al bench)
  │     update_2001.json
  ├── files/                ← Archivos adjuntos transferidos (xlsx, mp3, png...)
  └── counters/
        agent_id.txt        ← Próximo ID para mensajes del agente (int)
        controller_id.txt   ← Próximo ID para mensajes del controlador (int)
```

**Activación**: `TELEGRAM_TRANSPORT=local` (en .env de gaiabench y como variable del orquestador).

El agente (`telegram_api.py`) y Gaiabench (`main.py`) leen esta variable y conmutan el transporte de red al transporte de archivos de forma transparente.

---

## 7. Tokens y Credenciales

| Variable | Valor | Bot |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | `***` | `@Openzxzxzxbot` (el agente) |
| `CONTROLLER_BOT_TOKEN` | `***` | `@AiBenchAgentbot` (el lab) |
| `TARGET_BOT_USERNAME` | `-1004226057414` | ID del supergrupo compartido |
| `HF_TOKEN` | `***` | Hugging Face (dataset GAIA) |

---

## 8. Archivos clave a conocer

| Archivo | Propósito |
|---|---|
| `d:/inspector/agente/telegram_codex_orchestrator/orchestrator.py` | Núcleo del agente. |
| `d:/inspector/agente/telegram_codex_orchestrator/intent.py` | Clasificador de intents (Google Gemini + fallbacks locales). |
| `d:/inspector/agente/telegram_codex_orchestrator/codex_runner.py` | Ejecuta Codex CLI como subproceso con timeout. |
| `d:/inspector/agente/telegram_codex_orchestrator/telegram_api.py` | API Telegram real + local bus mock. |
| `d:/gaiabench/main.py` | Servidor FastAPI de Gaiabench + bucle de ejecución de tests. |
| `d:/gaiabench/generate_report.py` | Genera el informe HTML desde config.json. |
| `d:/gaiabench/run_failed_tasks.py` | Re-ejecuta solo las tareas fallidas del Nivel 1. |
| `d:/gaiabench/run_level_1.py` | Ejecuta TODAS las tareas del Nivel 1 (incluidas las correctas). |
| `d:/gaiabench/scratch/clear_bus.py` | Limpia el bus local antes de un nuevo run. |
| `d:/gaiabench/config.json` | Historial de resultados de todas las tareas ejecutadas. |
| `d:/gaiabench/report.html` | Último informe visual generado. |
| `d:/cuaderno_actualizaciones.md` | Diario cronológico de todas las sesiones. |

---

## 9. Secuencia recomendada para la siguiente sesión

```
1. Leer este documento y el cuaderno de actualizaciones.
2. Arrancar el bus limpio:
   python d:\gaiabench\scratch\clear_bus.py
3. Arrancar el orquestador en modo lab:
   (configurar ORCH_LAB_MODE=1, TELEGRAM_TRANSPORT=local, TELEGRAM_ALLOWED_USER_ID=-1004226057414)
   D:\inspector\.venv\Scripts\python.exe d:\inspector\agente\telegram_codex_orchestrator\orchestrator.py
4. Arrancar Gaiabench en otra terminal:
   cd d:\gaiabench && python -m uvicorn main:app --host 127.0.0.1 --port 8080
5. Esperar ~5 segundos a que ambos servicios estén listos.
6. Correr las tareas fallidas:
   python d:\gaiabench\run_failed_tasks.py
7. Monitorear el progreso en el log del orquestador o en la UI de Gaiabench (http://127.0.0.1:8080).
8. Al finalizar, generar el informe:
   python d:\gaiabench\generate_report.py
   start d:\gaiabench\report.html
9. Documentar en d:/cuaderno_actualizaciones.md.
```

---

*Generado automáticamente — Antigravity AI — Sesión 2026-06-03*
