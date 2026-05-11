from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from alarms import parse_alarm_request
from config import Settings


ACTION_HELP = "help"
ACTION_STATUS = "status"
ACTION_LIST_ALARMS = "list_alarms"
ACTION_CANCEL_ALARM = "cancel_alarm"
ACTION_CODEX = "codex"
ACTION_CREATE_ALARM = "create_alarm"
ACTION_REMEMBER = "remember"
ACTION_LIST_MEMORIES = "list_memories"
ACTION_ADD_CODEX_DIR = "add_codex_dir"
ACTION_LIST_CODEX_DIRS = "list_codex_dirs"
ACTION_REMOVE_CODEX_DIR = "remove_codex_dir"
ACTION_LIST_THREADS = "list_threads"
ACTION_CURRENT_THREAD = "current_thread"
ACTION_NEW_THREAD = "new_thread"
ACTION_SWITCH_THREAD = "switch_thread"
ACTION_STATUS_DETAIL = "status_detail"
ACTION_LIST_PENDING = "list_pending"
ACTION_RUN_NEXT_PENDING = "run_next_pending"
ACTION_CLEAR_PENDING = "clear_pending"
ACTION_CANCEL_CURRENT_TASK = "cancel_current_task"
ACTION_UNKNOWN = "unknown"

KNOWN_ACTIONS = {
    ACTION_HELP,
    ACTION_STATUS,
    ACTION_LIST_ALARMS,
    ACTION_CANCEL_ALARM,
    ACTION_CODEX,
    ACTION_CREATE_ALARM,
    ACTION_REMEMBER,
    ACTION_LIST_MEMORIES,
    ACTION_ADD_CODEX_DIR,
    ACTION_LIST_CODEX_DIRS,
    ACTION_REMOVE_CODEX_DIR,
    ACTION_LIST_THREADS,
    ACTION_CURRENT_THREAD,
    ACTION_NEW_THREAD,
    ACTION_SWITCH_THREAD,
    ACTION_STATUS_DETAIL,
    ACTION_LIST_PENDING,
    ACTION_RUN_NEXT_PENDING,
    ACTION_CLEAR_PENDING,
    ACTION_CANCEL_CURRENT_TASK,
    ACTION_UNKNOWN,
}


@dataclass(frozen=True)
class Intent:
    action: str
    args: dict[str, Any] = field(default_factory=dict)
    source: str = "local"
    confidence: float = 1.0


class IntentInterpreter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def interpret(self, text: str) -> Intent:
        local = self._local_intent(text)
        if local.action != ACTION_UNKNOWN:
            return local

        if self.settings.google_intent_enabled and self.settings.google_api_key:
            google = self._google_intent(text)
            if google.action != ACTION_UNKNOWN:
                return google

        return local

    def _local_intent(self, text: str) -> Intent:
        stripped = text.strip()
        lower = stripped.lower()

        if lower in {"/start", "/help", "help", "ayuda"}:
            return Intent(ACTION_HELP)
        if lower == "/status":
            return Intent(ACTION_STATUS_DETAIL)
        if lower in {"que estas haciendo", "qué estás haciendo", "que haces", "qué haces", "estas ocupado", "estás ocupado", "/ocupado"}:
            return Intent(ACTION_STATUS_DETAIL)
        if lower in {"/pendientes", "que hay pendiente", "qué hay pendiente", "tareas pendientes"}:
            return Intent(ACTION_LIST_PENDING)
        if lower in {"/siguiente", "/continuar_pendiente", "continua con lo pendiente", "continúa con lo pendiente", "sigue con lo pendiente"}:
            return Intent(ACTION_RUN_NEXT_PENDING)
        if lower in {"/limpiar_pendientes", "borra pendientes", "limpia pendientes"}:
            return Intent(ACTION_CLEAR_PENDING)
        if lower in {
            "/cancelar_tarea",
            "/detener",
            "deten la tarea actual",
            "detén la tarea actual",
            "para la tarea actual",
            "cancela la tarea actual",
            "cancela codex",
            "deten codex",
            "detén codex",
        }:
            return Intent(ACTION_CANCEL_CURRENT_TASK)
        if lower in {"/alarmas", "/alarms"}:
            return Intent(ACTION_LIST_ALARMS)
        if lower in {"/recuerdos", "/memoria", "/memorias"}:
            return Intent(ACTION_LIST_MEMORIES)
        if lower in {"/directorios", "/dirs", "/carpetas"}:
            return Intent(ACTION_LIST_CODEX_DIRS)
        if lower in {"/hilos", "que hilos hay", "qué hilos hay", "lista hilos"}:
            return Intent(ACTION_LIST_THREADS)
        if lower in {"/hilo", "/hilo_actual", "hilo actual"}:
            return Intent(ACTION_CURRENT_THREAD)
        new_thread = extract_new_thread(stripped)
        if new_thread is not None:
            return Intent(ACTION_NEW_THREAD, {"name": new_thread})
        switch_thread = extract_switch_thread(stripped)
        if switch_thread is not None:
            return Intent(ACTION_SWITCH_THREAD, {"name": switch_thread})
        add_dir = extract_codex_dir(stripped)
        if add_dir is not None:
            return Intent(ACTION_ADD_CODEX_DIR, {"path": add_dir})
        remove_dir = extract_remove_codex_dir(stripped)
        if remove_dir is not None:
            return Intent(ACTION_REMOVE_CODEX_DIR, {"path": remove_dir})
        if lower.startswith("/cancelar_alarma ") or lower.startswith("/cancel_alarm "):
            return Intent(ACTION_CANCEL_ALARM, {"alarm_id": stripped.split(maxsplit=1)[1].strip()})

        codex_instruction = extract_codex_instruction(stripped)
        if codex_instruction is not None:
            return Intent(ACTION_CODEX, {"instruction": codex_instruction})

        remember_text = extract_remember_text(stripped)
        if remember_text is not None:
            return Intent(ACTION_REMEMBER, {"text": remember_text})

        if parse_alarm_request(stripped) is not None:
            return Intent(ACTION_CREATE_ALARM, {"text": stripped})

        return Intent(ACTION_UNKNOWN, {"text": stripped}, confidence=0.0)

    def _google_intent(self, text: str) -> Intent:
        prompt = _intent_prompt(text)
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            + urllib.parse.quote(self.settings.google_model, safe="")
            + ":generateContent?key="
            + urllib.parse.quote(self.settings.google_api_key, safe="")
        )
        body = json.dumps(
            {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}],
                    }
                ],
                "generationConfig": {
                    "temperature": 0,
                    "responseMimeType": "application/json",
                },
            },
            ensure_ascii=False,
        ).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.settings.google_intent_timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8", errors="replace"))
        except Exception:
            return Intent(ACTION_UNKNOWN, {"text": text}, source="google_error", confidence=0.0)

        parsed = _extract_google_json(payload)
        action = str(parsed.get("action", ACTION_UNKNOWN)).strip()
        if action not in KNOWN_ACTIONS:
            action = ACTION_UNKNOWN

        args = parsed.get("args")
        if not isinstance(args, dict):
            args = {}

        confidence = parsed.get("confidence", 0.5)
        try:
            confidence_float = float(confidence)
        except (TypeError, ValueError):
            confidence_float = 0.5

        if action == ACTION_CREATE_ALARM:
            args.setdefault("text", text)
        if action == ACTION_CODEX:
            args.setdefault("instruction", text)
        if action == ACTION_REMEMBER:
            args.setdefault("text", text)
        if action in {ACTION_ADD_CODEX_DIR, ACTION_REMOVE_CODEX_DIR}:
            args.setdefault("path", "")
        if action in {ACTION_NEW_THREAD, ACTION_SWITCH_THREAD}:
            args.setdefault("name", "")
        if action == ACTION_CODEX:
            args.setdefault("thread_name", "")

        return Intent(action, args, source="google", confidence=confidence_float)


def extract_codex_instruction(text: str) -> str | None:
    stripped = text.strip()
    for prefix in ("-c ", "/c ", "/codex ", "c "):
        if stripped.lower().startswith(prefix):
            instruction = stripped[len(prefix) :].strip()
            return instruction or None
    return None


def extract_remember_text(text: str) -> str | None:
    patterns = (
        r"^(?:recuerda|recordar|guarda en memoria|guarda|memoriza)\s+(?:que\s+)?(.+)$",
        r"^(?:quiero recordar|ten en cuenta)\s+(?:que\s+)?(.+)$",
    )
    for pattern in patterns:
        match = re.search(pattern, text.strip(), flags=re.IGNORECASE)
        if match:
            value = match.group(1).strip(" .,:;-")
            return value or None
    return None


def extract_codex_dir(text: str) -> str | None:
    patterns = (
        r"^(?:/add_dir|/adddir|/anadir_dir|/añadir_dir)\s+(.+)$",
        r"^(?:anade|añade|agrega|incluye)\s+(?:la\s+)?(?:carpeta|ruta|direccion|dirección|directorio)\s+(.+)$",
        r"^(?:quiero\s+)?(?:trabajar|explorar)\s+(?:en|con)\s+(?:la\s+)?(?:carpeta|ruta|direccion|dirección|directorio)?\s*(.+)$",
    )
    return _first_match(text, patterns)


def extract_remove_codex_dir(text: str) -> str | None:
    patterns = (
        r"^(?:/remove_dir|/removedir|/quitar_dir)\s+(.+)$",
        r"^(?:quita|elimina|borra)\s+(?:la\s+)?(?:carpeta|ruta|direccion|dirección|directorio)\s+(.+)$",
    )
    return _first_match(text, patterns)


def extract_new_thread(text: str) -> str | None:
    patterns = (
        r"^(?:/nuevo_hilo|/new_thread)\s+(.+)$",
        r"^(?:abre|crea|empieza)\s+(?:un\s+)?(?:hilo|tema|conversacion|conversación)\s+(?:nuevo\s+)?(?:sobre|para|llamado|de)?\s*(.+)$",
    )
    return _first_match(text, patterns)


def extract_switch_thread(text: str) -> str | None:
    patterns = (
        r"^(?:/usar_hilo|/switch_thread|/hilo)\s+(.+)$",
        r"^(?:usa|cambia a|ponme en|sigue en|vamos al|ve al)\s+(?:el\s+)?(?:hilo|tema|conversacion|conversación)?\s*(.+)$",
    )
    return _first_match(text, patterns)


def _first_match(text: str, patterns: tuple[str, ...]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text.strip(), flags=re.IGNORECASE)
        if match:
            value = match.group(1).strip(" .,:;")
            return value or None
    return None


def _intent_prompt(text: str) -> str:
    return f"""
Eres el interprete de ordenes de un bot personal por Telegram.
Devuelve solo JSON valido, sin markdown.

Acciones disponibles:
- help: pedir ayuda.
- status: pedir estado.
- list_alarms: listar alarmas.
- cancel_alarm: cancelar una alarma. args: {{"alarm_id":"..."}}
- codex: ejecutar Codex CLI. args: {{"instruction":"..."}}
- create_alarm: crear una alarma o recordatorio temporal. args: {{"text":"frase original o normalizada en espanol"}}
- remember: guardar una memoria persistente. args: {{"text":"contenido a recordar"}}
- list_memories: listar recuerdos.
- add_codex_dir: anadir carpeta adicional para que Codex pueda trabajar alli. args: {{"path":"ruta absoluta"}}
- list_codex_dirs: listar carpetas adicionales de Codex.
- remove_codex_dir: quitar carpeta adicional. args: {{"path":"ruta absoluta"}}
- list_threads: listar hilos.
- current_thread: mostrar hilo activo.
- new_thread: crear hilo nuevo y activarlo. args: {{"name":"nombre_corto"}}
- switch_thread: cambiar al hilo existente o crearlo si no existe. args: {{"name":"nombre_corto"}}
- status_detail: preguntar que esta haciendo, si esta ocupado o estado detallado.
- list_pending: listar tareas Codex pendientes.
- run_next_pending: continuar con la siguiente tarea pendiente.
- clear_pending: borrar tareas pendientes.
- cancel_current_task: detener/cancelar la tarea Codex actual.
- unknown: no se entiende.

Reglas:
- Si el usuario quiere que el sistema haga trabajo de programacion, edicion o investigacion, usa codex.
- Para codex, incluye args.thread_name si el usuario menciona un hilo, tema o proyecto claro.
- Si pide "avisame", "ponme una alarma", "recuerdame manana/dentro de...", usa create_alarm.
- Si dice "recuerda que", "guarda en memoria", "ten en cuenta", usa remember.
- Si pregunta por hilos o quiere cambiar/crear una conversacion, usa list_threads, current_thread, new_thread o switch_thread.
- Si pregunta "que estas haciendo", "estas ocupado" o estado de trabajo, usa status_detail.
- Si pregunta por pendientes o quiere continuar algo pendiente, usa list_pending o run_next_pending.
- Si pide detener, parar o cancelar la tarea actual de Codex, usa cancel_current_task.
- Si pide anadir, agregar, explorar o trabajar con una ruta tipo G:\\..., usa add_codex_dir.
- No inventes fechas completas; conserva la frase temporal en args.text para que el planificador la procese.

Texto del usuario:
{text}

JSON esperado:
{{"action":"...", "confidence":0.0, "args":{{...}}}}
""".strip()


def _extract_google_json(payload: dict[str, Any]) -> dict[str, Any]:
    candidates = payload.get("candidates") or []
    if not candidates:
        return {}
    parts = (((candidates[0] or {}).get("content") or {}).get("parts") or [])
    text = "".join(str(part.get("text", "")) for part in parts if isinstance(part, dict)).strip()
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return {}
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}
    return parsed if isinstance(parsed, dict) else {}
