from __future__ import annotations

import argparse
import json
import mimetypes
import threading
from dataclasses import asdict
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import webbrowser

from .catalog_loader import discover_professions, load_catalog, profession_to_dict, task_to_dict
from .task_generator import build_profession_generation_prompt, write_generated_catalog
from .models import TaskRequest
from .orchestrator import GestorOrquestador
from .telegram_lab import TelegramEndpoint
from .voice_io import transcribe_with_fallback


PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parent
RUNTIME_ROOT = PACKAGE_ROOT / "runtime"
UI_STATE_FILE = RUNTIME_ROOT / "web_ui_state.json"
LATEST_VOICE_FILE = RUNTIME_ROOT / "web_ui" / "latest_voice_input"
GENERATED_ROOT = REPO_ROOT / "benchmarks" / "contracts"
LAB_RUNS_ROOT = PACKAGE_ROOT / "runtime" / "lab_runs"
BENCH_RESULTS_ROOT = REPO_ROOT / "benchmarks" / "results"


DEFAULT_STATE = {
    "lab": {
        "profession_id": "office_general",
        "transport": "dry_run",
        "speed_seconds": 30,
        "speed_mode": "jitter",
        "max_tasks": 4,
        "persona_ids": [],
        "task_ids": [],
        "evidence_dir": "",
        "bots": [
            {"token": "", "chat_id": ""},
            {"token": "", "chat_id": ""},
            {"token": "", "chat_id": ""},
            {"token": "", "chat_id": ""},
        ],
    },
    "manager": {
        "user_id": "web",
        "thread_id": "dashboard",
        "always_confirm": True,
    },
}


def ensure_runtime() -> None:
    LATEST_VOICE_FILE.parent.mkdir(parents=True, exist_ok=True)
    UI_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_state() -> dict:
    ensure_runtime()
    if not UI_STATE_FILE.exists():
        return json.loads(json.dumps(DEFAULT_STATE))
    try:
        raw = json.loads(UI_STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return json.loads(json.dumps(DEFAULT_STATE))
    return merge_state(DEFAULT_STATE, raw if isinstance(raw, dict) else {})


def save_state(state: dict) -> None:
    ensure_runtime()
    UI_STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def merge_state(base: dict, override: dict) -> dict:
    merged = json.loads(json.dumps(base))
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_state(merged[key], value)
        else:
            merged[key] = value
    return merged


def latest_run_dir() -> Path | None:
    candidates = [path for path in LAB_RUNS_ROOT.glob("*") if path.is_dir()]
    if not candidates:
        candidates = [path for path in BENCH_RESULTS_ROOT.glob("*") if path.is_dir()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def latest_lab_summary() -> dict:
    run_dir = latest_run_dir()
    if not run_dir:
        return {"run_dir": "", "summary": [], "token_usage": {}}
    summary_path = run_dir / "summary.json"
    token_path = run_dir / "token_usage_summary.json"
    summary = []
    if summary_path.exists():
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            summary = []
    token_usage = {}
    if token_path.exists():
        try:
            token_usage = json.loads(token_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            token_usage = {}
    return {"run_dir": str(run_dir), "summary": summary[:50], "token_usage": token_usage}


def latest_benchmark_summary() -> dict:
    candidates = [path for path in BENCH_RESULTS_ROOT.glob("*") if path.is_dir()]
    if not candidates:
        return {"run_dir": "", "summary": [], "token_usage": {}}
    run_dir = max(candidates, key=lambda path: path.stat().st_mtime)
    summary_path = run_dir / "summary.json"
    token_path = run_dir / "token_usage_summary.json"
    summary = []
    if summary_path.exists():
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            summary = []
    token_usage = {}
    if token_path.exists():
        try:
            token_usage = json.loads(token_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            token_usage = {}
    return {"run_dir": str(run_dir), "summary": summary[:50], "token_usage": token_usage}


def bootstrap_payload() -> dict:
    state = load_state()
    professions = [
        {
            **profession_to_dict(profession),
            "tasks": [task_to_dict(task) for task in load_catalog(profession.id)[1]],
        }
        for profession in discover_professions()
    ]
    current_profession_id = state["lab"].get("profession_id", "office_general")
    try:
        current_profession, current_tasks, current_personas = load_catalog(current_profession_id)
    except Exception:
        current_profession, current_tasks, current_personas = load_catalog("office_general")
    return {
        "state": state,
        "professions": professions,
        "current": {
            "profession": profession_to_dict(current_profession),
            "tasks": [task_to_dict(task) for task in current_tasks],
            "personas": [asdict(persona) for persona in current_personas],
        },
        "lab_run": latest_lab_summary(),
        "benchmark_run": latest_benchmark_summary(),
    }


def run_lab_from_state(state: dict) -> dict:
    lab = state["lab"]
    profession_id = lab.get("profession_id", "office_general")
    profession, tasks, personas = load_catalog(profession_id)
    selected_tasks = [task for task in tasks if not lab.get("task_ids") or task.id in set(lab.get("task_ids", []))]
    selected_personas = [persona for persona in personas if not lab.get("persona_ids") or persona.id in set(lab.get("persona_ids", []))]
    if not selected_personas:
        selected_personas = personas
    if not selected_tasks:
        selected_tasks = tasks
    evidence_dir = Path(lab.get("evidence_dir") or (LAB_RUNS_ROOT / datetime.now().strftime("%Y%m%d_%H%M%S")))
    transport = lab.get("transport", "dry_run")
    endpoints = [
        TelegramEndpoint(token=bot.get("token", ""), chat_id=str(bot.get("chat_id", "")))
        for bot in lab.get("bots", [])
        if bot.get("token") and bot.get("chat_id")
    ]
    if transport == "dry_run":
        from .lab_contracts import LabActivation
        from .lab_scheduler import build_schedule
        from .telegram_lab import execute_dry_run

        activation = LabActivation(
            id="web_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
            profession_id=profession.id,
            task_ids=tuple(task.id for task in selected_tasks),
            persona_ids=tuple(persona.id for persona in selected_personas),
            speed_seconds=float(lab.get("speed_seconds", 30)),
            speed_mode=str(lab.get("speed_mode", "jitter")),
            transport="dry_run",
            max_tasks=int(lab.get("max_tasks", 4)),
            evidence_dir=evidence_dir,
        )
        schedule = build_schedule(activation, personas, tasks)
        written = execute_dry_run(schedule, evidence_dir)
        (evidence_dir / "activation.json").write_text(json.dumps(activation.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return {
            "ok": True,
            "run_dir": str(evidence_dir),
            "profession": profession.id,
            "messages": len(schedule),
            "files": [str(path) for path in written],
        }
    if transport == "telegram_group_bots":
        from .lab_contracts import LabActivation
        from .lab_scheduler import build_schedule
        from .telegram_lab import execute_telegram_group

        activation = LabActivation(
            id="web_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
            profession_id=profession.id,
            task_ids=tuple(task.id for task in selected_tasks),
            persona_ids=tuple(persona.id for persona in selected_personas),
            speed_seconds=float(lab.get("speed_seconds", 30)),
            speed_mode=str(lab.get("speed_mode", "jitter")),
            transport="telegram_group_bots",
            max_tasks=int(lab.get("max_tasks", 4)),
            evidence_dir=evidence_dir,
        )
        schedule = build_schedule(activation, personas, tasks)
        written = execute_telegram_group(schedule, endpoints, evidence_dir)
        (evidence_dir / "activation.json").write_text(json.dumps(activation.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return {
            "ok": True,
            "run_dir": str(evidence_dir),
            "profession": profession.id,
            "messages": len(schedule),
            "files": [str(path) for path in written],
        }
    raise ValueError("telegram_user_sessions still needs a transport implementation.")


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "InspectorDashboard/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            self._send_html(INDEX_HTML)
            return
        if parsed.path == "/api/bootstrap":
            self._send_json(bootstrap_payload())
            return
        if parsed.path == "/api/results/latest":
            self._send_json({"lab_run": latest_lab_summary(), "benchmark_run": latest_benchmark_summary()})
            return
        if parsed.path == "/api/professions":
            self._send_json({"professions": [profession_to_dict(item) for item in discover_professions()]})
            return
        if parsed.path == "/api/state":
            self._send_json(load_state())
            return
        self.send_error(404, "Not found")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b""
        if parsed.path == "/api/lab/config":
            payload = json.loads(body.decode("utf-8") or "{}")
            state = load_state()
            state["lab"] = merge_state(state["lab"], payload if isinstance(payload, dict) else {})
            save_state(state)
            self._send_json({"ok": True, "state": state})
            return
        if parsed.path == "/api/lab/run":
            state = load_state()
            payload = json.loads(body.decode("utf-8") or "{}")
            if isinstance(payload, dict):
                state["lab"] = merge_state(state["lab"], payload)
                save_state(state)
            try:
                result = run_lab_from_state(state)
                self._send_json(result)
            except Exception as exc:
                self._send_json({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, status=500)
            return
        if parsed.path == "/api/profession/generate-prompt":
            payload = json.loads(body.decode("utf-8") or "{}")
            title = str(payload.get("title", "")).strip()
            description = str(payload.get("description", "")).strip()
            task_count = int(payload.get("task_count", 20))
            self._send_json({"prompt": build_profession_generation_prompt(title, description, task_count)})
            return
        if parsed.path == "/api/profession/save":
            payload = json.loads(body.decode("utf-8") or "{}")
            try:
                write_generated_catalog(GENERATED_ROOT, payload)
                self._send_json({"ok": True, "root": str(GENERATED_ROOT / payload.get("profession", {}).get("id", "generated_profession"))})
            except Exception as exc:
                self._send_json({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, status=500)
            return
        if parsed.path == "/api/orchestrator/command":
            payload = json.loads(body.decode("utf-8") or "{}")
            text = str(payload.get("text", "")).strip()
            if not text:
                self._send_json({"ok": False, "error": "Missing text"}, status=400)
                return
            try:
                result = GestorOrquestador().handle(
                    TaskRequest(
                        text=text,
                        user_id="web",
                        thread_id="dashboard",
                        privacy_mode="clear",
                        metadata={"source": "web_ui", "desktop_send": True},
                    )
                )
                self._send_json({"ok": result.ok, "output": result.output, "error": result.error, "tool_id": result.tool_id, "engine": result.engine})
            except Exception as exc:
                self._send_json({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, status=500)
            return
        if parsed.path == "/api/orchestrator/voice":
            content_type = self.headers.get("Content-Type", "audio/webm")
            suffix = mimetypes.guess_extension(content_type.split(";")[0].strip()) or ".webm"
            voice_dir = LATEST_VOICE_FILE.parent
            voice_dir.mkdir(parents=True, exist_ok=True)
            path = voice_dir / f"voice_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}{suffix}"
            path.write_bytes(body)
            try:
                transcript = transcribe_with_fallback(path)
                result = GestorOrquestador().handle(
                    TaskRequest(
                        text=transcript,
                        user_id="web",
                        thread_id="voice",
                        privacy_mode="clear",
                        metadata={"source": "web_voice", "desktop_send": True},
                    )
                )
                self._send_json({"ok": True, "transcript": transcript, "output": result.output, "error": result.error, "tool_id": result.tool_id, "engine": result.engine})
            except Exception as exc:
                self._send_json({"ok": False, "error": f"{type(exc).__name__}: {exc}", "saved_audio": str(path)}, status=500)
            return
        self.send_error(404, "Not found")

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _send_json(self, payload: dict, status: int = 200) -> None:
        raw = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _send_html(self, html: str) -> None:
        raw = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


INDEX_HTML = r"""
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Inspector Dashboard</title>
  <style>
    :root{
      --bg:#0b1220;
      --panel:#111a2b;
      --panel2:#162238;
      --line:#27334b;
      --text:#eef3fb;
      --muted:#aeb9cb;
      --blue:#4ea1ff;
      --cyan:#34d1c8;
      --orange:#ffb15e;
      --red:#ff5b67;
      --green:#61d095;
      --shadow:0 22px 55px rgba(0,0,0,.35);
    }
    *{box-sizing:border-box}
    body{
      margin:0;
      font-family: Inter, Segoe UI, system-ui, -apple-system, sans-serif;
      background:
        radial-gradient(circle at 15% 20%, rgba(78,161,255,.12), transparent 25%),
        radial-gradient(circle at 85% 0%, rgba(52,209,200,.10), transparent 22%),
        linear-gradient(180deg,#07111f 0%, #0b1220 45%, #09111d 100%);
      color:var(--text);
    }
    .app{
      max-width:1500px;
      margin:0 auto;
      padding:24px;
    }
    .hero{
      display:flex;
      gap:16px;
      align-items:stretch;
      margin-bottom:18px;
      flex-wrap:wrap;
    }
    .brand{
      flex:1 1 360px;
      background:linear-gradient(135deg, rgba(17,26,43,.96), rgba(18,32,53,.92));
      border:1px solid var(--line);
      border-radius:22px;
      padding:22px;
      box-shadow:var(--shadow);
    }
    .brand h1{margin:0 0 6px;font-size:28px;letter-spacing:.02em}
    .brand p{margin:0;color:var(--muted);line-height:1.5}
    .pillrow{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}
    .pill{
      padding:8px 12px;border-radius:999px;border:1px solid rgba(255,255,255,.12);
      background:rgba(255,255,255,.03);color:var(--text);font-size:12px;
    }
    .toolbar{
      flex:1 1 420px;
      background:linear-gradient(135deg, rgba(17,26,43,.96), rgba(20,28,44,.95));
      border:1px solid var(--line);
      border-radius:22px;
      padding:18px;
      box-shadow:var(--shadow);
      display:grid;
      gap:10px;
      align-content:start;
    }
    .toolbar .row{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}
    .toolbar input,.toolbar select,.toolbar textarea{
      width:100%;background:var(--panel2);color:var(--text);border:1px solid var(--line);border-radius:12px;padding:11px 12px;
    }
    .toolbar textarea{min-height:120px;resize:vertical}
    button{
      border:none;border-radius:12px;padding:11px 14px;font-weight:700;color:#06111d;background:linear-gradient(135deg,var(--blue),#76c6ff);
      cursor:pointer;box-shadow:0 12px 26px rgba(78,161,255,.22);
    }
    button.secondary{background:linear-gradient(135deg,#243247,#1a2638);color:var(--text);box-shadow:none;border:1px solid var(--line)}
    button.green{background:linear-gradient(135deg,var(--green),#8af0bc);color:#06111d}
    button.orange{background:linear-gradient(135deg,var(--orange),#ffd089);color:#231707}
    .grid{
      display:grid;
      grid-template-columns:1.05fr .95fr 1.1fr;
      gap:16px;
    }
    .card{
      background:rgba(17,26,43,.96);
      border:1px solid var(--line);
      border-radius:22px;
      box-shadow:var(--shadow);
      overflow:hidden;
      min-height:240px;
    }
    .card header{
      padding:16px 18px;
      border-bottom:1px solid rgba(255,255,255,.06);
      display:flex;align-items:center;justify-content:space-between;gap:10px;
      background:linear-gradient(180deg, rgba(255,255,255,.03), transparent);
    }
    .card h2{margin:0;font-size:18px}
    .card .body{padding:18px}
    .tabs{display:flex;gap:8px;flex-wrap:wrap}
    .tab{padding:9px 12px;border-radius:999px;background:#243247;border:1px solid var(--line);color:var(--text);cursor:pointer;font-size:13px}
    .tab.active{background:linear-gradient(135deg,var(--blue),#76c6ff);color:#06111d;border-color:transparent}
    .pane{display:none}
    .pane.active{display:block}
    .stack{display:grid;gap:10px}
    .muted{color:var(--muted);font-size:13px}
    .list{
      display:grid;gap:10px;max-height:360px;overflow:auto;padding-right:2px;
    }
    .item{
      background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);border-radius:16px;padding:14px;
    }
    .item strong{display:block;margin-bottom:6px}
    .table-wrap{overflow:auto;border:1px solid rgba(255,255,255,.06);border-radius:18px}
    table{width:100%;border-collapse:collapse;min-width:640px;background:rgba(255,255,255,.02)}
    th,td{padding:11px 12px;border-bottom:1px solid rgba(255,255,255,.06);text-align:left;font-size:13px}
    th{position:sticky;top:0;background:#152237;z-index:1}
    .split{display:grid;grid-template-columns:1fr 1fr;gap:12px}
    .small{font-size:12px}
    .code{font-family: Consolas, Monaco, monospace; white-space:pre-wrap; background:#09111d; border:1px solid var(--line); border-radius:16px; padding:12px; min-height:140px; max-height:280px; overflow:auto;}
    .floating-voice{
      position:fixed;left:22px;bottom:22px;width:78px;height:78px;border-radius:22px;
      background:linear-gradient(135deg,var(--blue),#78c6ff);display:flex;align-items:center;justify-content:center;
      color:#03101d;font-weight:900;box-shadow:0 18px 40px rgba(78,161,255,.32);cursor:pointer;user-select:none;
      border:1px solid rgba(255,255,255,.22);
    }
    .floating-voice.recording{background:linear-gradient(135deg,#ff6473,#ff9aa4)}
    .badge{padding:5px 8px;border-radius:999px;background:#243247;color:var(--muted);font-size:12px;border:1px solid var(--line)}
    .topline{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}
    @media (max-width: 1180px){ .grid{grid-template-columns:1fr;} .toolbar .row,.split{grid-template-columns:1fr;} }
  </style>
</head>
<body>
  <div class="app">
    <div class="hero">
      <div class="brand">
        <h1>Inspector Dashboard</h1>
        <p>Laboratorio ciego, profesiones, resultados, y gestor visual en una sola carpeta portable. Aqui se configura, se activa y se audita sin salir del navegador.</p>
        <div class="pillrow">
          <span class="pill">Portable por carpeta</span>
          <span class="pill">Telegram bots</span>
          <span class="pill">Dry-run y real</span>
          <span class="pill">Voz local</span>
          <span class="pill">Resultados y tokens</span>
        </div>
      </div>
      <div class="toolbar">
        <div class="topline">
          <strong>Accion rapida</strong>
          <span class="badge" id="connBadge">loading...</span>
        </div>
        <div class="row">
          <button id="saveLabBtn">Guardar laboratorio</button>
          <button class="secondary" id="runLabBtn">Lanzar laboratorio</button>
          <button class="secondary" id="refreshBtn">Refrescar</button>
        </div>
        <div class="row">
          <input id="professionId" placeholder="profession_id" />
          <select id="transport">
            <option value="dry_run">dry_run</option>
            <option value="telegram_group_bots">telegram_group_bots</option>
            <option value="telegram_user_sessions">telegram_user_sessions</option>
          </select>
          <input id="evidenceDir" placeholder="evidence dir (opcional)" />
        </div>
        <div class="row">
          <input id="speedSeconds" type="number" min="0" step="1" placeholder="speed seconds" />
          <input id="maxTasks" type="number" min="1" step="1" placeholder="max tasks" />
          <select id="speedMode">
            <option value="fixed">fixed</option>
            <option value="jitter">jitter</option>
            <option value="burst">burst</option>
          </select>
        </div>
        <div class="small muted">Bots 1 a 4. Si no usas env vars, deja aqui el token y chat_id para que el laboratorio los use desde la propia UI.</div>
      </div>
    </div>

    <div class="card" style="margin-bottom:16px;">
      <header>
        <h2>Navegacion</h2>
        <div class="tabs">
          <button class="tab active" data-tab="lab">Laboratorio</button>
          <button class="tab" data-tab="professions">Profesiones</button>
          <button class="tab" data-tab="results">Resultados</button>
          <button class="tab" data-tab="manager">Gestor</button>
        </div>
      </header>
      <div class="body">
        <div class="pane active" id="pane-lab">
          <div class="grid">
            <div class="card">
              <header><h2>Configuracion de bots</h2><span class="badge">4 slots</span></header>
              <div class="body stack" id="botsForm"></div>
            </div>
            <div class="card">
              <header><h2>Profesion activa</h2><span class="badge" id="activeProfessionBadge">office_general</span></header>
              <div class="body stack" id="professionPicker"></div>
            </div>
            <div class="card">
              <header><h2>Tareas y ejecucion</h2><span class="badge">scheduler</span></header>
              <div class="body stack">
                <div id="taskChecklist" class="list" style="max-height:220px"></div>
                <div class="split">
                  <button class="green" id="activateBtn">Activar desde UI</button>
                  <button class="secondary" id="toggleTaskAllBtn">Marcar/Desmarcar</button>
                </div>
                <div class="code" id="labResult">Sin ejecucion todavia.</div>
              </div>
            </div>
          </div>
        </div>

        <div class="pane" id="pane-professions">
          <div class="grid">
            <div class="card">
              <header><h2>Catalogo de profesiones</h2><span class="badge">discover</span></header>
              <div class="body">
                <div id="professionsList" class="list"></div>
              </div>
            </div>
            <div class="card">
              <header><h2>Generar profesion</h2><span class="badge">prompt</span></header>
              <div class="body stack">
                <input id="genTitle" placeholder="Titulo de la profesion" />
                <textarea id="genDescription" placeholder="Descripcion de la profesion"></textarea>
                <div class="row" style="grid-template-columns:1fr 1fr 1fr;display:grid;gap:10px">
                  <input id="genTaskCount" type="number" min="1" step="1" value="20" />
                  <button class="orange" id="genPromptBtn">Generar prompt</button>
                  <button class="secondary" id="saveGeneratedBtn">Guardar JSON</button>
                </div>
                <textarea id="genPromptOutput" placeholder="Prompt para pedir la profesion a un modelo"></textarea>
                <textarea id="genJsonOutput" placeholder="Pega aqui el JSON final generado por el modelo"></textarea>
              </div>
            </div>
            <div class="card">
              <header><h2>Estructura de la profesion</h2><span class="badge">tasks + assets</span></header>
              <div class="body">
                <div class="code" id="professionDetails"></div>
              </div>
            </div>
          </div>
        </div>

        <div class="pane" id="pane-results">
          <div class="grid">
            <div class="card">
              <header><h2>Ultima corrida del laboratorio</h2><span class="badge">lab</span></header>
              <div class="body">
                <div class="muted" id="labRunDir"></div>
                <div class="table-wrap" style="margin-top:10px">
                  <table id="labResultsTable">
                    <thead><tr><th>#</th><th>Persona</th><th>Tarea</th><th>Archivo</th></tr></thead>
                    <tbody></tbody>
                  </table>
                </div>
              </div>
            </div>
            <div class="card">
              <header><h2>Tokens</h2><span class="badge">usage</span></header>
              <div class="body">
                <div class="code" id="tokenSummary"></div>
              </div>
            </div>
            <div class="card">
              <header><h2>Benchmark reciente</h2><span class="badge">results</span></header>
              <div class="body">
                <div class="muted" id="benchRunDir"></div>
                <div class="code" id="benchSummary"></div>
              </div>
            </div>
          </div>
        </div>

        <div class="pane" id="pane-manager">
          <div class="grid">
            <div class="card">
              <header><h2>Comando</h2><span class="badge">orchestrator v2</span></header>
              <div class="body stack">
                <textarea id="commandText" placeholder="Escribe una instruccion al gestor..."></textarea>
                <div class="split">
                  <button id="sendCommandBtn">Enviar comando</button>
                  <button class="secondary" id="clearCommandBtn">Limpiar</button>
                </div>
                <div class="code" id="commandResult">Sin respuesta.</div>
              </div>
            </div>
            <div class="card">
              <header><h2>Voz</h2><span class="badge">mic + whisper</span></header>
              <div class="body stack">
                <div class="muted">Pulsa el boton azul, habla, y vuelve a pulsar para enviar la nota al gestor.</div>
                <div class="split">
                  <button id="voiceButton" class="orange">Grabar</button>
                  <button class="secondary" id="voiceStopBtn">Parar</button>
                </div>
                <div class="code" id="voiceResult">Sin audio todavia.</div>
              </div>
            </div>
            <div class="card">
              <header><h2>Estado</h2><span class="badge">live</span></header>
              <div class="body">
                <div class="code" id="bootstrapState"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="floating-voice" id="floatingVoice">REC</div>

  <script>
    const state = { bootstrap: null, selectedTasks: new Set(), recording: false, mediaRecorder: null, chunks: [] };

    const $ = (id) => document.getElementById(id);

    function setTab(name){
      document.querySelectorAll('.tab').forEach(btn => btn.classList.toggle('active', btn.dataset.tab === name));
      document.querySelectorAll('.pane').forEach(p => p.classList.remove('active'));
      $('pane-' + name).classList.add('active');
    }

    document.querySelectorAll('.tab').forEach(btn => btn.addEventListener('click', () => setTab(btn.dataset.tab)));

    async function api(path, method='GET', payload=null, isBlob=false){
      const opts = {method, headers:{}};
      if(payload !== null){
        if(isBlob){
          opts.body = payload;
        } else {
          opts.headers['Content-Type']='application/json';
          opts.body = JSON.stringify(payload);
        }
      }
      const res = await fetch(path, opts);
      const txt = await res.text();
      try { return JSON.parse(txt); } catch { return { raw: txt, ok: res.ok }; }
    }

    async function refresh(){
      const data = await api('/api/bootstrap');
      state.bootstrap = data;
      $('bootstrapState').textContent = JSON.stringify(data.state, null, 2);
      $('connBadge').textContent = 'ready';
      renderLab(data);
      renderProfessions(data);
      renderResults(data);
    }

    function renderLab(data){
      const stateLab = data.state.lab;
      $('professionId').value = stateLab.profession_id || 'office_general';
      $('transport').value = stateLab.transport || 'dry_run';
      $('speedSeconds').value = stateLab.speed_seconds ?? 30;
      $('speedMode').value = stateLab.speed_mode || 'jitter';
      $('maxTasks').value = stateLab.max_tasks ?? 4;
      $('evidenceDir').value = stateLab.evidence_dir || '';
      $('activeProfessionBadge').textContent = stateLab.profession_id || 'office_general';

      const bots = stateLab.bots || [];
      const botsForm = $('botsForm');
      botsForm.innerHTML = '';
      for(let i=0;i<4;i++){
        const bot = bots[i] || {token:'',chat_id:''};
        const wrapper = document.createElement('div');
        wrapper.className = 'item';
        wrapper.innerHTML = `
          <strong>Bot ${i+1}</strong>
          <div class="split">
            <input placeholder="TOKEN" value="${bot.token || ''}" data-bot-token="${i}" />
            <input placeholder="CHAT_ID" value="${bot.chat_id || ''}" data-bot-chat="${i}" />
          </div>`;
        botsForm.appendChild(wrapper);
      }

      const professionPicker = $('professionPicker');
      professionPicker.innerHTML = '';
      const professions = data.professions || [];
      const select = document.createElement('select');
      select.id = 'professionSelect';
      professions.forEach(item => {
        const opt = document.createElement('option');
        opt.value = item.id;
        opt.textContent = `${item.id} | ${item.title}`;
        if(item.id === stateLab.profession_id) opt.selected = true;
        select.appendChild(opt);
      });
      professionPicker.appendChild(select);

      const current = data.current || {};
      const tasks = current.tasks || [];
      if (stateLab.task_ids && stateLab.task_ids.length && state.selectedTasks.size === 0) {
        stateLab.task_ids.forEach(taskId => state.selectedTasks.add(taskId));
      }
      const checklist = $('taskChecklist');
      checklist.innerHTML = '';
      tasks.forEach(task => {
        const div = document.createElement('div');
        div.className = 'item';
        div.innerHTML = `
          <label style="display:flex;gap:10px;align-items:flex-start">
            <input type="checkbox" data-task-id="${task.id}" ${state.selectedTasks.has(task.id) ? 'checked' : ''} />
            <span><strong>${task.id} - ${task.title}</strong><span class="muted">${task.level} | ${task.category || ''}</span></span>
          </label>`;
        checklist.appendChild(div);
      });
      checklist.querySelectorAll('input[type="checkbox"]').forEach(el => {
        el.addEventListener('change', () => {
          if(el.checked) state.selectedTasks.add(el.dataset.taskId); else state.selectedTasks.delete(el.dataset.taskId);
        });
      });
    }

    function renderProfessions(data){
      const list = $('professionsList');
      list.innerHTML = '';
      (data.professions || []).forEach(item => {
        const div = document.createElement('div');
        div.className = 'item';
        div.innerHTML = `<strong>${item.id}</strong><div class="muted">${item.title}</div><div class="muted small">${(item.scope || []).join(' | ')}</div>`;
        div.onclick = () => {
          $('professionDetails').textContent = JSON.stringify(item, null, 2);
          $('genTitle').value = item.title || '';
          $('genDescription').value = item.description || '';
        };
        list.appendChild(div);
      });
      if(data.current && data.current.profession){
        $('professionDetails').textContent = JSON.stringify(data.current.profession, null, 2);
      }
    }

    function renderResults(data){
      const lab = data.lab_run || {};
      const bench = data.benchmark_run || {};
      $('labRunDir').textContent = lab.run_dir ? `Run: ${lab.run_dir}` : 'Sin corrida todavia.';
      $('benchRunDir').textContent = bench.run_dir ? `Run: ${bench.run_dir}` : 'Sin benchmark reciente.';
      $('tokenSummary').textContent = JSON.stringify((lab.token_usage || {}), null, 2);
      $('benchSummary').textContent = JSON.stringify((bench.summary || []).slice(0, 8), null, 2);
      const tbody = $('labResultsTable').querySelector('tbody');
      tbody.innerHTML = '';
      (lab.summary || []).forEach((row, idx) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${idx+1}</td>
          <td>${row.persona_name || row.user || ''}</td>
          <td>${row.task_id || row.task || ''}</td>
          <td>${(row.copied_outputs || []).join('<br/>')}</td>`;
        tbody.appendChild(tr);
      });
    }

    async function saveLab(){
      const bots = [];
      for(let i=0;i<4;i++){
        bots.push({
          token: document.querySelector(`[data-bot-token="${i}"]`).value.trim(),
          chat_id: document.querySelector(`[data-bot-chat="${i}"]`).value.trim(),
        });
      }
      const payload = {
        profession_id: $('professionSelect')?.value || $('professionId').value.trim() || 'office_general',
        transport: $('transport').value,
        speed_seconds: Number($('speedSeconds').value || 30),
        speed_mode: $('speedMode').value,
        max_tasks: Number($('maxTasks').value || 4),
        evidence_dir: $('evidenceDir').value.trim(),
        bots: bots,
      };
      const res = await api('/api/lab/config', 'POST', payload);
      $('labResult').textContent = JSON.stringify(res, null, 2);
      await refresh();
    }

    async function runLab(){
      const payload = {
        profession_id: $('professionSelect')?.value || $('professionId').value.trim() || 'office_general',
        transport: $('transport').value,
        speed_seconds: Number($('speedSeconds').value || 30),
        speed_mode: $('speedMode').value,
        max_tasks: Number($('maxTasks').value || 4),
        evidence_dir: $('evidenceDir').value.trim(),
        task_ids: [...state.selectedTasks],
      };
      const res = await api('/api/lab/run', 'POST', payload);
      $('labResult').textContent = JSON.stringify(res, null, 2);
      await refresh();
    }

    async function generatePrompt(){
      const res = await api('/api/profession/generate-prompt', 'POST', {
        title: $('genTitle').value.trim(),
        description: $('genDescription').value.trim(),
        task_count: Number($('genTaskCount').value || 20),
      });
      $('genPromptOutput').value = res.prompt || JSON.stringify(res, null, 2);
    }

    async function saveGenerated(){
      let payload;
      try{ payload = JSON.parse($('genJsonOutput').value); }
      catch(e){ alert('Pega un JSON valido en el cuadro de salida antes de guardar.'); return; }
      const res = await api('/api/profession/save', 'POST', payload);
      $('professionDetails').textContent = JSON.stringify(res, null, 2);
      await refresh();
    }

    async function sendCommand(){
      const text = $('commandText').value.trim();
      if(!text) return;
      const res = await api('/api/orchestrator/command', 'POST', {text});
      $('commandResult').textContent = JSON.stringify(res, null, 2);
    }

    async function captureVoice(){
      const voiceBtn = $('floatingVoice');
      if(!state.recording){
        const stream = await navigator.mediaDevices.getUserMedia({audio:true});
        state.mediaRecorder = new MediaRecorder(stream);
        state.chunks = [];
        state.mediaRecorder.ondataavailable = (e)=>{ if(e.data.size>0) state.chunks.push(e.data); };
        state.mediaRecorder.onstop = async ()=>{
          const blob = new Blob(state.chunks, {type: state.mediaRecorder.mimeType || 'audio/webm'});
          const res = await api('/api/orchestrator/voice', 'POST', blob, true);
          $('voiceResult').textContent = JSON.stringify(res, null, 2);
        };
        state.mediaRecorder.start();
        state.recording = true;
        voiceBtn.classList.add('recording');
        voiceBtn.textContent = 'STOP';
      } else {
        state.recording = false;
        voiceBtn.classList.remove('recording');
        voiceBtn.textContent = 'REC';
        state.mediaRecorder.stop();
      }
    }

    $('saveLabBtn').onclick = saveLab;
    $('runLabBtn').onclick = runLab;
    $('refreshBtn').onclick = refresh;
    $('genPromptBtn').onclick = generatePrompt;
    $('saveGeneratedBtn').onclick = saveGenerated;
    $('sendCommandBtn').onclick = sendCommand;
    $('clearCommandBtn').onclick = () => { $('commandText').value=''; $('commandResult').textContent='Sin respuesta.'; };
    $('voiceButton').onclick = captureVoice;
    $('voiceStopBtn').onclick = () => { if(state.recording) captureVoice(); };
    $('floatingVoice').onclick = captureVoice;
    $('toggleTaskAllBtn').onclick = () => {
      const checks = [...document.querySelectorAll('#taskChecklist input[type="checkbox"]')];
      const allChecked = checks.length && checks.every(x => x.checked);
      checks.forEach(x => { x.checked = !allChecked; if(!allChecked) state.selectedTasks.add(x.dataset.taskId); else state.selectedTasks.delete(x.dataset.taskId); });
    };

    refresh();
  </script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Portable dashboard for orchestrator v2 and the blind lab.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()

    ensure_runtime()
    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    url = f"http://{args.host}:{args.port}"
    if args.open:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    print(f"Inspector dashboard running at {url}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
