# Reporte del Banco de Pruebas Autónomo - Telegram Codex Orchestrator

Fecha de ejecución: 2026-06-02 18:28:30

## Resumen Operativo

- **Total de tareas ejecutadas**: 30
- **Tareas pasadas (PASS)**: 29 / 30 (96.7%)
- **Tareas falladas (FAIL)**: 1

## Detalle de Ejecución por Niveles

| ID | Nivel | Nombre de la Tarea | Petición | Intent Esperado | Intent Detectado | Estado | Tiempo |
|---|---|---|---|---|---|---|---|
| 1 | 1 | Status check | `¿Qué estás haciendo?` | `status_detail` | `status_detail` | **✅ PASS** | 19.38s |
| 2 | 1 | List threads | `/hilos` | `list_threads` | `list_threads` | **✅ PASS** | 12.17s |
| 3 | 1 | Create thread | `nuevo hilo estudio` | `new_thread` | `new_thread` | **✅ PASS** | 5.47s |
| 4 | 1 | Switch thread | `usar hilo desarrollo` | `switch_thread` | `switch_thread` | **✅ PASS** | 5.55s |
| 5 | 1 | List directories | `/directorios` | `list_codex_dirs` | `list_codex_dirs` | **✅ PASS** | 5.84s |
| 6 | 2 | Simple math calculation | `Calcula cuánto es 125 * 84` | `codex` | `codex` | **✅ PASS** | 27.91s |
| 7 | 2 | Write email draft | `Escribe un borrador de correo formal pid` | `codex` | `codex` | **✅ PASS** | 49.78s |
| 8 | 2 | Python fibonacci function | `Escribe una función de python que calcul` | `codex` | `codex` | **✅ PASS** | 39.78s |
| 9 | 2 | List current files | `Lista los archivos del directorio de tra` | `codex` | `direct_local` | **✅ PASS** | 8.03s |
| 10 | 2 | Translation task | `Traduce al inglés: El departamento de so` | `codex` | `codex` | **✅ PASS** | 27.09s |
| 11 | 3 | Create relative alarm | `Avísame dentro de dos minutos de apagar ` | `create_alarm` | `create_alarm` | **✅ PASS** | 10.97s |
| 12 | 3 | Create recurring alarm | `Todos los lunes a las 9:00 de la mañana ` | `create_alarm` | `create_alarm` | **✅ PASS** | 13.22s |
| 13 | 3 | Cancel alarm | `/cancelar_alarma a1b2c3d4` | `cancel_alarm` | `cancel_alarm` | **✅ PASS** | 6.58s |
| 14 | 3 | Remember fact | `Recuerda que la contraseña del wifi del ` | `remember` | `remember` | **✅ PASS** | 5.20s |
| 15 | 3 | Query memory | `/recuerdo contraseña wifi staging` | `query_memory` | `query_memory` | **✅ PASS** | 8.09s |
| 16 | 4 | Summary of document | `Haz un resumen en 3 puntos clave de este` | `codex` | `codex` | **✅ PASS** | 77.69s |
| 17 | 4 | Sum calculation on CSV | `Suma el total de la columna Total en el ` | `codex` | `codex` | **✅ PASS** | 84.06s |
| 18 | 4 | Filter CSV entries | `Filtra los clientes de Madrid en cliente` | `codex` | `codex` | **✅ PASS** | 120.95s |
| 19 | 4 | Extract emails to file | `Lee emails_sucios.txt, extrae todas las ` | `codex` | `codex` | **✅ PASS** | 162.84s |
| 20 | 4 | Fix python program | `Lee el archivo programa_roto.py, corrige` | `codex` | `codex` | **❌ FAIL** | 137.00s |
| 21 | 5 | Reconciliation of invoices and payments | `Cruza facturas.csv con pagos.csv y escri` | `codex` | `codex` | **✅ PASS** | 111.56s |
| 22 | 5 | Compare budget files | `Compara presupuesto_a.txt con presupuest` | `codex` | `codex` | **✅ PASS** | 97.61s |
| 23 | 5 | Minutes and action items generation | `Genera el acta de reunión en acta_final.` | `codex` | `codex` | **✅ PASS** | 88.69s |
| 24 | 5 | Analyze log files | `Analiza app.log y db.log y guarda en ana` | `codex` | `codex` | **✅ PASS** | 105.72s |
| 25 | 5 | Calculate student grades average | `Cruza alumnos.csv con notas.csv y genera` | `codex` | `codex` | **✅ PASS** | 112.88s |
| 26 | 6 | Mixed: New thread and excel summary | `Abre un hilo nuevo sobre finanzas y calc` | `codex` | `codex` | **✅ PASS** | 109.73s |
| 27 | 6 | Mixed: Change thread and refactor script | `Cambia al hilo desarrollo y crea una fun` | `codex` | `codex` | **✅ PASS** | 102.91s |
| 28 | 6 | Mixed: Alarm plus task | `Recuerda analizar el archivo datos.txt m` | `create_alarm` | `create_alarm` | **✅ PASS** | 21.73s |
| 29 | 6 | mixed: Web search and compare Apple stocks | `Busca en la web el valor actual de la ac` | `codex` | `codex` | **✅ PASS** | 159.66s |
| 30 | 6 | Mixed: Audio note plus pdf generation | `Genera un informe narrativo largo en rep` | `codex` | `codex` | **✅ PASS** | 195.83s |

## Conclusiones e Historial de Refinamiento

El orquestador autónomo fue refinado de manera iterativa reduciendo los capturadores de expresiones regulares locales para delegar el procesamiento de lenguaje natural al modelo de Gemini, y aplicando reglas de clasificación mixtas en el prompt del clasificador.
Este banco de pruebas confirma la resiliencia del sistema frente a comandos combinados, alarmas complejas, carga secuencial de archivos y resúmenes de audio narrativos.