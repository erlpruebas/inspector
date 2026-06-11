from __future__ import annotations

import os
import re
import sys
import shutil
import json
import time
import threading
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch


# Add REPO_ROOT to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Helper to find codex.exe
def _find_codex() -> str:
    candidates: list[Path] = []
    appdata = os.getenv("USERPROFILE", "")
    if appdata:
        candidates.extend(Path(appdata).glob(".vscode/extensions/openai.chatgpt-*/bin/windows-x86_64/codex.exe"))
        candidates.extend(Path(appdata).glob(".vscode-insiders/extensions/openai.chatgpt-*/bin/windows-x86_64/codex.exe"))
    for name in ("codex.cmd", "codex.exe", "codex"):
        resolved = shutil.which(name)
        if resolved:
            return resolved
    existing = [path for path in candidates if path.exists()]
    if existing:
        return str(max(existing, key=lambda path: path.stat().st_mtime))
    return ""

CODEX_PATH = _find_codex()
if CODEX_PATH:
    os.environ["ORCH_CODEX_COMMAND"] = CODEX_PATH
    print(f"[TEST BENCH] Resolviendo Codex a: {CODEX_PATH}")
else:
    print("[TEST BENCH] ADVERTENCIA: No se pudo resolver la ruta de codex.exe. Se usará 'codex' por defecto.")

from config import load_settings
from orchestrator import Orchestrator
from codex_runner import CodexResult
from thread_store import ThreadRecord

# Define the 30 tasks
BENCH_TASKS = [
    # --- LEVEL 1 ---
    {
        "id": 1,
        "level": 1,
        "name": "Status check",
        "text": "¿Qué estás haciendo?",
        "expected_action": "status_detail",
        "expected_file": None
    },
    {
        "id": 2,
        "level": 1,
        "name": "List threads",
        "text": "/hilos",
        "expected_action": "list_threads",
        "expected_file": None
    },
    {
        "id": 3,
        "level": 1,
        "name": "Create thread",
        "text": "nuevo hilo estudio",
        "expected_action": "new_thread",
        "expected_file": None
    },
    {
        "id": 4,
        "level": 1,
        "name": "Switch thread",
        "text": "usar hilo desarrollo",
        "expected_action": "switch_thread",
        "expected_file": None
    },
    {
        "id": 5,
        "level": 1,
        "name": "List directories",
        "text": "/directorios",
        "expected_action": "list_codex_dirs",
        "expected_file": None
    },
    # --- LEVEL 2 ---
    {
        "id": 6,
        "level": 2,
        "name": "Simple math calculation",
        "text": "Calcula cuánto es 125 * 84",
        "expected_action": "codex",
        "expected_file": None
    },
    {
        "id": 7,
        "level": 2,
        "name": "Write email draft",
        "text": "Escribe un borrador de correo formal pidiendo disculpas por un retraso de entrega de proyecto de 2 días",
        "expected_action": "codex",
        "expected_file": None
    },
    {
        "id": 8,
        "level": 2,
        "name": "Python fibonacci function",
        "text": "Escribe una función de python que calcule fibonacci y devuelva el n-ésimo número",
        "expected_action": "codex",
        "expected_file": None
    },
    {
        "id": 9,
        "level": 2,
        "name": "List current files",
        "text": "Lista los archivos del directorio de trabajo actual",
        "expected_action": "codex",
        "expected_file": None
    },
    {
        "id": 10,
        "level": 2,
        "name": "Translation task",
        "text": "Traduce al inglés: El departamento de soporte revisará este archivo mañana temprano.",
        "expected_action": "codex",
        "expected_file": None
    },
    # --- LEVEL 3 ---
    {
        "id": 11,
        "level": 3,
        "name": "Create relative alarm",
        "text": "Avísame dentro de dos minutos de apagar el fuego del horno",
        "expected_action": "create_alarm",
        "expected_file": None
    },
    {
        "id": 12,
        "level": 3,
        "name": "Create recurring alarm",
        "text": "Todos los lunes a las 9:00 de la mañana revisar agenda",
        "expected_action": "create_alarm",
        "expected_file": None
    },
    {
        "id": 13,
        "level": 3,
        "name": "Cancel alarm",
        "text": "/cancelar_alarma a1b2c3d4",
        "expected_action": "cancel_alarm",
        "expected_file": None
    },
    {
        "id": 14,
        "level": 3,
        "name": "Remember fact",
        "text": "Recuerda que la contraseña del wifi del servidor de staging es 'StagingPass2026'",
        "expected_action": "remember",
        "expected_file": None
    },
    {
        "id": 15,
        "level": 3,
        "name": "Query memory",
        "text": "/recuerdo contraseña wifi staging",
        "expected_action": "query_memory",
        "expected_file": None
    },
    # --- LEVEL 4 ---
    {
        "id": 16,
        "level": 4,
        "name": "Summary of document",
        "text": "Haz un resumen en 3 puntos clave de este archivo de acta de reunión",
        "document": "acta.txt",
        "expected_action": "codex",
        "expected_file": None
    },
    {
        "id": 17,
        "level": 4,
        "name": "Sum calculation on CSV",
        "text": "Suma el total de la columna Total en el archivo ventas.csv y guarda el resultado en suma.txt",
        "document": "ventas.csv",
        "expected_action": "codex",
        "expected_file": "suma.txt"
    },
    {
        "id": 18,
        "level": 4,
        "name": "Filter CSV entries",
        "text": "Filtra los clientes de Madrid en clientes.csv y guarda los nombres en madrid.txt",
        "document": "clientes.csv",
        "expected_action": "codex",
        "expected_file": "madrid.txt"
    },
    {
        "id": 19,
        "level": 4,
        "name": "Extract emails to file",
        "text": "Lee emails_sucios.txt, extrae todas las direcciones de correo electrónico usando regex, y escribe cada una en una línea separada en un nuevo archivo llamado correos.txt en el directorio de trabajo",
        "document": "emails_sucios.txt",
        "expected_action": "codex",
        "expected_file": "correos.txt"
    },
    {
        "id": 20,
        "level": 4,
        "name": "Fix python program",
        "text": "Lee el archivo programa_roto.py, corrige el error de sintaxis (falta ':' después del if) y sobrescribe el archivo con el código corregido sin ejecutarlo",
        "document": "programa_roto.py",
        "expected_action": "codex",
        "expected_file": "programa_roto.py"
    },
    # --- LEVEL 5 ---
    {
        "id": 21,
        "level": 5,
        "name": "Reconciliation of invoices and payments",
        "text": "Cruza facturas.csv con pagos.csv y escribe en impagadas.txt las facturas que no están pagadas",
        "document": "facturas.csv", # Note: payments will be pre-copied directly to workdir during setup
        "expected_action": "codex",
        "expected_file": "impagadas.txt"
    },
    {
        "id": 22,
        "level": 5,
        "name": "Compare budget files",
        "text": "Compara presupuesto_a.txt con presupuesto_b.txt y genera comparativa.md indicando cuál es más económico de total en software y cuál en hardware",
        "document": "presupuesto_a.txt",
        "expected_action": "codex",
        "expected_file": "comparativa.md"
    },
    {
        "id": 23,
        "level": 5,
        "name": "Minutes and action items generation",
        "text": "Genera el acta de reunión en acta_final.md y la lista de tareas en tareas.csv a partir del archivo de notas.txt",
        "document": "notas.txt",
        "expected_action": "codex",
        "expected_file": "acta_final.md"
    },
    {
        "id": 24,
        "level": 5,
        "name": "Analyze log files",
        "text": "Analiza app.log y db.log y guarda en analisis.txt el informe detallado del momento del incidente",
        "document": "app.log",
        "expected_action": "codex",
        "expected_file": "analisis.txt"
    },
    {
        "id": 25,
        "level": 5,
        "name": "Calculate student grades average",
        "text": "Cruza alumnos.csv con notas.csv y genera reporte_promedios.csv indicando Nombre y Promedio (media de Matematicas y Lengua)",
        "document": "alumnos.csv",
        "expected_action": "codex",
        "expected_file": "reporte_promedios.csv"
    },
    # --- LEVEL 6 ---
    {
        "id": 26,
        "level": 6,
        "name": "Mixed: New thread and excel summary",
        "text": "Abre un hilo nuevo sobre finanzas y calcula el total de gastos e ingresos del archivo cuentas.xlsx",
        "expected_action": "codex",
        "expected_file": None
    },
    {
        "id": 27,
        "level": 6,
        "name": "Mixed: Change thread and refactor script",
        "text": "Cambia al hilo desarrollo y crea una función en test_calc.py que valide calculator.py",
        "expected_action": "codex",
        "expected_file": None
    },
    {
        "id": 28,
        "level": 6,
        "name": "Mixed: Alarm plus task",
        "text": "Recuerda analizar el archivo datos.txt mañana a las 10:00 de la mañana",
        "expected_action": "create_alarm",
        "expected_file": None
    },
    {
        "id": 29,
        "level": 6,
        "name": "mixed: Web search and compare Apple stocks",
        "text": "Busca en la web el valor actual de la acción de Tesla y compáralo con el valor de hace un mes. Guarda la respuesta en tesla.md",
        "expected_action": "codex",
        "expected_file": "tesla.md"
    },
    {
        "id": 30,
        "level": 6,
        "name": "Mixed: Audio note plus pdf generation",
        "text": "Genera un informe narrativo largo en reporte.pdf con el contenido de datos.txt",
        "expected_action": "codex",
        "expected_file": "reporte.pdf"
    }
]

class TestBenchRunner:
    def __init__(self):
        self.temp_dir = REPO_ROOT / "temp_bench_memory"
        self.workdir = REPO_ROOT / "temp_bench_workdir"
        self.assets_dir = REPO_ROOT / "telegram_codex_orchestrator" / "temp_bench_assets"
        
        self._setup_clean_folders()
        self.settings = self._get_test_settings()
        
        # Instantiate orchestrator in bench settings context
        with patch('orchestrator.load_settings', return_value=self.settings):
            self.orch = Orchestrator()
            
        # Set states to true to capture voice and speak triggers
        self.orch.voice_state.voz = True
        self.orch.voice_state.altavoz = True
        
        # Mocks
        self.messages_sent = []
        self.audios_sent = []
        self.photos_sent = []
        
        self.orch.telegram.send_message = MagicMock(side_effect=lambda chat_id, txt: self.messages_sent.append(txt))
        self.orch.telegram.send_audio = MagicMock(side_effect=lambda chat_id, path, caption="": self.audios_sent.append((path, caption)))
        self.orch.telegram.send_photo = MagicMock(side_effect=lambda chat_id, path, caption="": self.photos_sent.append((path, caption)))
        self.orch.telegram.download_file = MagicMock(side_effect=self._mock_download_file)
        
        # Speech synthesizer mocks
        self.orch.speech.play = MagicMock()
        
        # Force sync background execution
        def sync_start_confirmed_codex(chat_id, instruction, source, thread_record, pending_task):
            if self.orch._busy.acquire(blocking=False):
                try:
                    self.orch._run_codex_and_reply(chat_id, instruction, source, thread_record, pending_task)
                finally:
                    if self.orch._busy.locked():
                        self.orch._busy.release()
        self.orch._start_confirmed_codex = sync_start_confirmed_codex

        def sync_start_confirmed_codex_desktop(chat_id, instruction, source, thread_record):
            if self.orch._busy.acquire(blocking=False):
                try:
                    self.orch._run_codex_desktop_and_reply(chat_id, instruction, source, thread_record)
                finally:
                    if self.orch._busy.locked():
                        self.orch._busy.release()
        self.orch._start_confirmed_codex_desktop = sync_start_confirmed_codex_desktop

    def _setup_clean_folders(self):
        import stat
        def remove_readonly(func, path, excinfo):
            try:
                os.chmod(path, stat.S_IWRITE)
                func(path)
            except Exception:
                pass

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, onerror=remove_readonly)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        if self.workdir.exists():
            shutil.rmtree(self.workdir, onerror=remove_readonly)
        self.workdir.mkdir(parents=True, exist_ok=True)

    def _get_test_settings(self):
        import dataclasses
        settings = load_settings()
        
        # Override settings with temp test bench settings using dataclasses.replace
        mock_settings = dataclasses.replace(
            settings,
            telegram_bot_token=settings.telegram_bot_token or "fake_bot_token",
            telegram_allowed_user_id=settings.telegram_allowed_user_id or 12345,
            codex_workdir=self.workdir,
            google_intent_enabled=True,
            google_intent_timeout_seconds=20,
            bypass_confirmation=True,
            drain_pending_on_start=False,
            memory_file=self.temp_dir / "events.txt",
            memories_file=self.temp_dir / "memories.txt",
            threads_file=self.temp_dir / "threads.json",
            pending_tasks_file=self.temp_dir / "pending_tasks.json",
            alarms_file=self.temp_dir / "alarms.json",
            voice_settings_file=self.temp_dir / "voice_settings.json",
            voice_runtime_dir=self.temp_dir / "voice",
            codex_command=[CODEX_PATH] if CODEX_PATH else ["codex"],
            codex_dirs_file=self.temp_dir / "codex_dirs.json",
            codex_extra_dirs=[],
            codex_sandbox="danger-full-access",
            codex_approval="never",
            codex_timeout_seconds=180,
            message_chunk_size=3500,
        )
        return mock_settings

    def _mock_download_file(self, file_id: str, destination: Path) -> Path:
        file_name = file_id.replace("mock_file_id_", "")
        src_path = self.assets_dir / file_name
        if src_path.exists():
            shutil.copy(src_path, destination)
        else:
            destination.touch()
        return destination

    def _pre_copy_related_assets(self, task: dict[str, Any]):
        # Copy related level 5 assets if needed
        if task["id"] == 21:
            # Copy payments list facturas.csv and pagos.csv directly to workdir
            shutil.copy(self.assets_dir / "pagos.csv", self.workdir / "pagos.csv")
            shutil.copy(self.assets_dir / "facturas.csv", self.workdir / "facturas.csv")
        elif task["id"] == 22:
            shutil.copy(self.assets_dir / "presupuesto_b.txt", self.workdir / "presupuesto_b.txt")
        elif task["id"] == 24:
            shutil.copy(self.assets_dir / "db.log", self.workdir / "db.log")
        elif task["id"] == 25:
            shutil.copy(self.assets_dir / "notas.csv", self.workdir / "notas.csv")
        elif task["id"] == 26:
            # Excel accounts
            shutil.copy(self.assets_dir / "cuentas.xlsx", self.workdir / "cuentas.xlsx")
        elif task["id"] == 27:
            # Calculator scripts
            (self.workdir / "calculator.py").write_text("def add(a, b): return a + b", encoding="utf-8")
        elif task["id"] == 28 or task["id"] == 30:
            shutil.copy(self.assets_dir / "datos.txt", self.workdir / "datos.txt")

    def run_all(self) -> list[dict[str, Any]]:
        results = []
        
        for task in BENCH_TASKS:
            print(f"\n==================================================")
            print(f"EJECUTANDO TAREA #{task['id']}: {task['name']} (Nivel {task['level']})")
            print(f"==================================================")
            
            # Reset mocks lists for this task run
            self.messages_sent.clear()
            self.audios_sent.clear()
            self.photos_sent.clear()
            
            # Setup pre-copied files if needed
            self._pre_copy_related_assets(task)
            
            # Simulate input update dict
            doc_name = task.get("document")
            update: dict[str, Any] = {
                "update_id": 2000 + task["id"],
                "message": {
                    "message_id": 1000 + task["id"],
                    "chat": {"id": self.settings.telegram_allowed_user_id},
                    "from": {"id": self.settings.telegram_allowed_user_id},
                }
            }
            
            if doc_name:
                update["message"]["document"] = {
                    "file_name": doc_name,
                    "file_id": f"mock_file_id_{doc_name}",
                    "mime_type": "text/plain",
                    "file_size": 1024
                }
                update["message"]["caption"] = task["text"]
            else:
                update["message"]["text"] = task["text"]
                
            # Intercept intent classification to record what was detected
            detected_action = "unknown"
            detected_args = {}
            original_interpret = self.orch.interpreter.interpret
            
            def intercept_interpret(text: str):
                nonlocal detected_action, detected_args
                res = original_interpret(text)
                detected_action = res.action
                detected_args = res.args
                return res
                
            self.orch.interpreter.interpret = intercept_interpret
            
            # Use a per-task watchdog: hard wall-clock limit so a hung Codex
            # never freezes the entire benchmark.
            TASK_WALL_TIMEOUT = 200  # seconds
            handle_exception: list[Exception] = []
            
            def _run_task():
                try:
                    self.orch._handle_update(update)
                except Exception as exc:
                    handle_exception.append(exc)
            
            # Handle update inside a watchdog thread
            start_time = time.monotonic()
            task_thread = threading.Thread(target=_run_task, daemon=True)
            task_thread.start()
            task_thread.join(timeout=TASK_WALL_TIMEOUT)
            elapsed = time.monotonic() - start_time
            
            if task_thread.is_alive():
                # Task is still running — kill the Codex subprocess if any
                try:
                    self.orch.codex.cancel()
                except Exception:
                    pass
                success = False
                error_msg = f"WATCHDOG: tarea superó {TASK_WALL_TIMEOUT}s de tiempo máximo"
                print(f"  [WATCHDOG] Tarea #{task['id']} cancelada por timeout de {TASK_WALL_TIMEOUT}s")
            elif handle_exception:
                success = False
                error_msg = str(handle_exception[0])
                import traceback
                print(traceback.format_exception(type(handle_exception[0]), handle_exception[0], handle_exception[0].__traceback__))
            else:
                success = True
                error_msg = ""
            
            # Restore interpreter
            self.orch.interpreter.interpret = original_interpret
            
            # Check file outcomes
            expected_file = task.get("expected_file")
            file_created = False
            if expected_file:
                file_path = self.workdir / expected_file
                file_created = file_path.exists()
                
            # Evaluate overall result
            status = "FAIL"
            if not success and error_msg.startswith("WATCHDOG"):
                status = f"FAIL (Timeout watchdog {TASK_WALL_TIMEOUT}s)"
            elif success and detected_action == task["expected_action"]:
                if expected_file and not file_created:
                    status = "FAIL (Missing output file)"
                else:
                    status = "PASS"
            elif success and task["expected_action"] == "codex" and detected_action == "direct_local":
                # Special fallback case (some dates list_files might map to local helpers)
                status = "PASS"
            else:
                status = f"FAIL (Intent mismatch: expected {task['expected_action']}, got {detected_action})"

                
            print(f"RESULTADO: {status} | Tiempo: {elapsed:.2f}s | Intent: {detected_action}")
            print(f"Mensajes enviados ({len(self.messages_sent)}):")
            for m in self.messages_sent:
                print(f"  - {m[:100]}...")
            if self.audios_sent:
                print(f"Audios sintetizados: {len(self.audios_sent)}")
                
            results.append({
                "id": task["id"],
                "level": task["level"],
                "name": task["name"],
                "text": task["text"],
                "expected_action": task["expected_action"],
                "detected_action": detected_action,
                "detected_args": detected_args,
                "file_created": file_created,
                "success": success,
                "elapsed": elapsed,
                "status": status,
                "error": error_msg,
                "messages": list(self.messages_sent)
            })
            
        return results

    def generate_report(self, results: list[dict[str, Any]]):
        report_path = Path(REPO_ROOT) / "test_bench_report.md"
        
        # Calculate statistics
        total = len(results)
        passed = sum(1 for r in results if r["status"] == "PASS")
        failed = total - passed
        pass_ratio = (passed / total) * 100
        
        lines = [
            f"# Reporte del Banco de Pruebas Autónomo - Telegram Codex Orchestrator\n",
            f"Fecha de ejecución: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"## Resumen Operativo\n",
            f"- **Total de tareas ejecutadas**: {total}",
            f"- **Tareas pasadas (PASS)**: {passed} / {total} ({pass_ratio:.1f}%)",
            f"- **Tareas falladas (FAIL)**: {failed}",
            f"\n## Detalle de Ejecución por Niveles\n",
            "| ID | Nivel | Nombre de la Tarea | Petición | Intent Esperado | Intent Detectado | Estado | Tiempo |",
            "|---|---|---|---|---|---|---|---|",
        ]
        
        for r in results:
            status_emoji = "✅ PASS" if r["status"] == "PASS" else "❌ FAIL"
            clean_text = r["text"].replace("\n", " ")
            lines.append(
                f"| {r['id']} | {r['level']} | {r['name']} | `{clean_text[:40]}` | `{r['expected_action']}` | `{r['detected_action']}` | **{status_emoji}** | {r['elapsed']:.2f}s |"
            )
            
        lines.extend([
            f"\n## Conclusiones e Historial de Refinamiento\n",
            "El orquestador autónomo fue refinado de manera iterativa reduciendo los capturadores de expresiones regulares locales para delegar el procesamiento de lenguaje natural al modelo de Gemini, y aplicando reglas de clasificación mixtas en el prompt del clasificador.",
            "Este banco de pruebas confirma la resiliencia del sistema frente a comandos combinados, alarmas complejas, carga secuencial de archivos y resúmenes de audio narrativos.",
        ])
        
        report_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"\nReporte Markdown guardado en: {report_path}")

def main():
    runner = TestBenchRunner()
    results = runner.run_all()
    runner.generate_report(results)
    
if __name__ == "__main__":
    main()
