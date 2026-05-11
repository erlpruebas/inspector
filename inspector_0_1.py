#!/usr/bin/env python3
"""
Inspector 0.1
=============
Vigilante de pantalla con notificaciones Telegram.
Routing automático de órdenes a Claude Code o Cowork.
Soporte multi-proveedor de visión con fallback automático.

Proveedores de visión (por orden de prioridad):
  1. Gemini Flash Lite  — barato, fiable, rápido
  2. Groq               — tier gratuito, muy rápido
  3. OpenRouter         — modelos gratuitos (Gemma, Qwen-VL...)
  4. LM Studio          — local, cualquier modelo cargado

Comandos Telegram:
  /start       Ayuda
  /info        Estado del sistema y proveedores
  /test        Prueba rápida de todos los proveedores de visión
  /orden       Envía una orden a Claude (Code o Cowork, decide solo)
  /monitorizar Inicia vigilancia sin enviar orden
  /parar       Detiene la vigilancia
  /estado      Captura + análisis inmediato
  /captura     Captura de pantalla sin análisis
  /continuar   Reanuda vigilancia tras un AVISO
"""

from __future__ import annotations

import base64
import ctypes
import json
import logging
import math
import os
import re
import ssl
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime
from io import BytesIO
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Callable, Optional

# ─────────────────────────────────────────────────────────────────────────────
#  Encoding seguro en consola Windows
# ─────────────────────────────────────────────────────────────────────────────
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ─────────────────────────────────────────────────────────────────────────────
#  Logging
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)-12s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger("inspector")


# ─────────────────────────────────────────────────────────────────────────────
#  Carga de .env
# ─────────────────────────────────────────────────────────────────────────────
def _load_env() -> None:
    for p in [Path(".env"), Path("D:/variables/.env")]:
        if p.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(dotenv_path=p, override=False)
                log.info("ENV cargado desde %s", p)
                return
            except ImportError:
                pass

_load_env()


def _setup_file_logging() -> None:
    try:
        log_path = Path(os.getenv("INSPECTOR_LOG_FILE", "logs/inspector.log"))
        if not log_path.is_absolute():
            log_path = Path.cwd() / log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)

        max_bytes = int(os.getenv("INSPECTOR_LOG_MAX_BYTES", str(2 * 1024 * 1024)))
        backup_count = int(os.getenv("INSPECTOR_LOG_BACKUP_COUNT", "5"))

        resolved = str(log_path.resolve())
        for handler in log.handlers:
            if isinstance(handler, RotatingFileHandler):
                try:
                    if Path(getattr(handler, "baseFilename", "")).resolve() == log_path.resolve():
                        return
                except Exception:
                    continue

        file_handler = RotatingFileHandler(
            filename=resolved,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(
            fmt="%(asctime)s [%(name)-12s] %(levelname)s %(message)s",
            datefmt="%H:%M:%S",
        ))
        logging.getLogger().addHandler(file_handler)
        log.info("Log persistente en %s", resolved)
    except Exception as exc:
        log.error("No pude configurar logging a archivo: %s", exc)


_setup_file_logging()


# ─────────────────────────────────────────────────────────────────────────────
#  Dependencias opcionales
# ─────────────────────────────────────────────────────────────────────────────
try:
    from PIL import ImageGrab, Image, ImageChops, ImageStat
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    log.warning("Pillow no instalado -> sin captura de pantalla")

try:
    import pyautogui
    import pygetwindow as gw
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.1
    HAS_GUI = True
except ImportError:
    HAS_GUI = False
    log.warning("PyAutoGUI/PyGetWindow no instalados -> sin automatizacion de escritorio")

try:
    from pywinauto import Desktop as UIADesktop
    HAS_UIA = True
except ImportError:
    HAS_UIA = False
    UIADesktop = None
    log.warning("pywinauto no instalado -> sin anclajes UI Automation para Codex")

try:
    from google import genai
    from google.genai import types as google_types
    HAS_GOOGLE_GENAI = True
except ImportError:
    HAS_GOOGLE_GENAI = False
    log.warning("google-genai no instalado -> sin agente Google")


# ─────────────────────────────────────────────────────────────────────────────
#  Configuración
# ─────────────────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_USER_ID:   int = int(os.getenv("TELEGRAM_ALLOWED_USER_ID", "0") or "0")
TELEGRAM_DEFAULT_TEXT_COMMAND: str = (os.getenv("TELEGRAM_DEFAULT_TEXT_COMMAND", "/gorden") or "/gorden").strip()
LMSTUDIO_BASE_URL:  str = os.getenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234").rstrip("/")
MONITOR_INTERVAL:   int = int(os.getenv("INSPECTOR_INTERVAL", "30"))
CODEX_MONITOR_INTERVAL: int = int(os.getenv("CODEX_MONITOR_INTERVAL", "15"))
CODEX_STABLE_THRESHOLD_PCT: float = float(os.getenv("CODEX_STABLE_THRESHOLD_PCT", "5"))
CODEX_STABLE_CYCLES: int = int(os.getenv("CODEX_STABLE_CYCLES", "2"))

GEMINI_API_KEY:    str = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY:      str = os.getenv("GROQ_API_KEY", "")
OPENROUTER_API_KEY:str = os.getenv("OPENROUTER_API_KEY", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
GOOGLE_API_KEY:    str = os.getenv("GOOGLE_API_KEY", "") or GEMINI_API_KEY

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
ANTHROPIC_API = "https://api.anthropic.com/v1/messages"
HTTP_USER_AGENT = "Inspector/0.1 (+Windows; Python urllib)"

# Modelos por proveedor
GEMINI_VISION_MODEL     = "gemini-2.5-flash-lite"
GEMINI_TEXT_MODEL       = "gemini-2.5-flash-lite"
GROQ_VISION_MODEL       = "meta-llama/llama-4-scout-17b-16e-instruct"
OPENROUTER_VISION_MODEL = "meta-llama/llama-3.2-11b-vision-instruct"
ANTHROPIC_COMPUTER_MODEL = os.getenv("ANTHROPIC_COMPUTER_MODEL", "claude-sonnet-4-6")
ANTHROPIC_COMPUTER_BETA  = os.getenv("ANTHROPIC_COMPUTER_BETA", "computer-use-2025-11-24")
ANTHROPIC_MAX_STEPS      = int(os.getenv("ANTHROPIC_COMPUTER_MAX_STEPS", "20"))
ANTHROPIC_MAX_TOKENS     = int(os.getenv("ANTHROPIC_COMPUTER_MAX_TOKENS", "512"))
ANTHROPIC_COOLDOWN_MINUTES = int(os.getenv("ANTHROPIC_COOLDOWN_MINUTES", "15"))
GOOGLE_DESKTOP_MODEL     = os.getenv("GOOGLE_DESKTOP_MODEL", "gemini-2.5-computer-use-preview-10-2025")
GOOGLE_DESKTOP_MAX_STEPS = int(os.getenv("GOOGLE_DESKTOP_MAX_STEPS", "10"))

# Prompts
VISION_SYSTEM = (
    "Eres un inspector de estado de pantalla de ordenador. "
    "Solo puedes responder con una de estas tres palabras: OK, AVISO o FIN. Nada mas."
)
VISION_PROMPT = (
    "Analiza esta captura de pantalla donde se esta ejecutando una tarea.\n\n"
    "Responde SOLO con una palabra:\n"
    "  OK    — tarea en curso sin problemas\n"
    "  AVISO — hay captcha, login requerido, error, alerta o cualquier interrupcion humana\n"
    "  FIN   — la tarea ha finalizado completamente\n\n"
    "Una sola palabra, sin puntuacion ni explicacion."
)
ROUTE_SYSTEM = (
    "Eres un router de tareas para Claude Desktop. "
    "Dado un texto de tarea, responde SOLO con 'CODE' o 'COWORK'. "
    "CODE: tareas de programacion, scripts, depuracion, desarrollo, terminal, git. "
    "COWORK: todo lo demas (navegacion, archivos, investigacion, redaccion, uso general del ordenador). "
    "Una sola palabra."
)
FIND_ELEMENT_SYSTEM = (
    "Eres un localizador de elementos UI. "
    "Responde SOLO con coordenadas 'x,y' (numeros enteros) o la palabra 'none'. "
    "Sin explicacion."
)
CODEX_PROGRESS_SYSTEM = (
    "Eres un inspector del panel Codex de Visual Studio Code. "
    "Debes responder SOLO en JSON con las claves estado y motivo. "
    "estado debe ser uno de: SIGUE, TERMINADO, BLOQUEADO. "
    "SIGUE si Codex aun esta generando, pensando o escribiendo. "
    "TERMINADO si la respuesta ya parece completa y estable. "
    "BLOQUEADO si falta interaccion humana, hay un error visible o no se ve el panel correcto."
)
CODEX_RESULT_SYSTEM = (
    "Eres un extractor de resultados del panel Codex de Visual Studio Code. "
    "Resume SOLO la ultima respuesta visible del asistente, priorizando el bloque mas reciente cercano a la parte inferior del panel. "
    "Ignora instrucciones antiguas, contexto previo y mensajes anteriores salvo que sean imprescindibles para entender esa ultima respuesta. "
    "Si el texto visible es insuficiente, indicalo explicitamente."
)
CODEX_INPUT_SYSTEM = (
    "Eres un inspector de la caja de entrada del panel Codex en Visual Studio Code. "
    "Debes responder SOLO en JSON con las claves estado y motivo. "
    "estado debe ser uno de: INPUT_VISIBLE, BORRADOR, NO_INPUT. "
    "INPUT_VISIBLE si se ve claramente la caja grande de entrada inferior donde el usuario puede escribir, aunque el placeholder Ask for... no sea legible. "
    "BORRADOR si se ve texto del usuario pendiente de enviar dentro de esa caja, incluido texto resaltado o seleccionado. "
    "NO_INPUT si la captura no parece corresponder a la caja correcta."
)
CODEX_SEND_SYSTEM = (
    "Eres un verificador del envio de prompts en el panel Codex de Visual Studio Code. "
    "Debes responder SOLO en JSON con las claves estado y motivo. "
    "estado debe ser uno de: ENVIADO, NO_ENVIADO, DUDOSO. "
    "ENVIADO si la peticion del usuario ya parece enviada al chat, si aparece Awaiting response, si aparece un boton stop o si Codex claramente ya esta respondiendo a ella aunque el texto del prompt no sea visible. "
    "NO_ENVIADO si el texto aun parece estar sin enviar dentro de la caja de entrada. "
    "DUDOSO si no puede decidirse con seguridad."
)
CODEX_ACTIVITY_SYSTEM = (
    "Eres un inspector de actividad del panel Codex en Visual Studio Code. "
    "Debes responder SOLO en JSON con las claves estado y motivo. "
    "estado debe ser uno de: TRABAJANDO, NO_TRABAJANDO, DUDOSO. "
    "TRABAJANDO si se ve el boton stop con un cuadrado negro dentro o una indicacion visual clara de que Codex esta generando. "
    "NO_TRABAJANDO si el boton stop no esta y en su lugar parece haber un boton normal de enviar, flecha o icono equivalente de peticion lista. "
    "DUDOSO si no se ve con suficiente claridad."
)
ANTHROPIC_COMPUTER_SYSTEM = (
    "Eres un operador de escritorio en Windows. "
    "Tu objetivo es ejecutar la orden del usuario de forma segura y autonoma usando el ordenador. "
    "Trabaja paso a paso. Tras cada accion importante, pide una captura con la herramienta de screenshot antes de decidir el siguiente movimiento. "
    "Si necesitas usar Visual Studio Code, busca su ventana ya abierta y utiliza su cuadro de texto inferior si hay un panel de chat visible. "
    "Si la tarea ya ha terminado, responde con un resumen corto en espanol. "
    "Si ves un bloqueo humano real (login, captcha, permiso delicado, 2FA o confirmacion sensible), detente y explica claramente que necesitas ayuda humana."
)
CODEX_LAUNCH_SYSTEM = (
    "Eres un operador de escritorio en Windows. "
    "Tu tarea es preparar una peticion en la extension Codex de Visual Studio Code. "
    "Busca una ventana principal de Visual Studio Code ya abierta. "
    "Asegurate de que el panel Codex o chat de Codex este visible. "
    "Coloca el foco en la caja de texto inferior del panel, deja el prompt limpio si hace falta, pega la peticion exacta y pulsa Enter para enviarla. "
    "Detente en cuanto veas que el mensaje se ha enviado y Codex esta procesando o la peticion ya aparece en el chat. "
    "No cambies archivos del repositorio por tu cuenta; solo prepara y envia la peticion."
)
CODEX_PANEL_LEFT_RATIO = 0.18
CODEX_PANEL_TOP_RATIO = 0.06
CODEX_PANEL_RIGHT_RATIO = 0.96
CODEX_PANEL_BOTTOM_RATIO = 0.96
CODEX_BODY_TOP_IN_PANEL = 0.08
CODEX_BODY_BOTTOM_IN_PANEL = 0.72
CODEX_INPUT_TOP_IN_PANEL = 0.74
CODEX_INPUT_BOTTOM_IN_PANEL = 0.98
CODEX_INPUT_CLICK_X_IN_PANEL = 0.50
CODEX_INPUT_CLICK_Y_IN_PANEL = 0.86
CODEX_SEND_STABILITY_PCT = float(os.getenv("CODEX_SEND_STABILITY_PCT", "0.20"))
CODEX_CONFIRM_FIN_DELAY = float(os.getenv("CODEX_CONFIRM_FIN_DELAY", "6"))


# ─────────────────────────────────────────────────────────────────────────────
#  SSL
# ─────────────────────────────────────────────────────────────────────────────
def _mk_ssl() -> ssl.SSLContext:
    try:
        import truststore
        truststore.inject_into_ssl()
        return ssl.create_default_context()
    except ImportError:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

_SSL = _mk_ssl()


# ─────────────────────────────────────────────────────────────────────────────
#  HTTP helpers
# ─────────────────────────────────────────────────────────────────────────────
def _post_json(url: str, payload: dict, headers: dict | None = None,
               timeout: int = 40, use_ssl: bool = True) -> dict:
    data = json.dumps(payload).encode("utf-8")
    h = {
        "Content-Type": "application/json",
        "User-Agent": HTTP_USER_AGENT,
    }
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    ctx = _SSL if use_ssl else None
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return json.loads(r.read().decode("utf-8"))


def _get_json(url: str, headers: dict | None = None,
              timeout: int = 10, use_ssl: bool = True) -> dict:
    h = {"User-Agent": HTTP_USER_AGENT}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h, method="GET")
    ctx = _SSL if use_ssl else None
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return json.loads(r.read().decode("utf-8"))


# ─────────────────────────────────────────────────────────────────────────────
#  Captura de pantalla
# ─────────────────────────────────────────────────────────────────────────────
MAX_ANALYSIS_WIDTH = 1280   # para análisis (reducido para ahorrar tokens)


def capture_screen(full_res: bool = False) -> Optional[bytes]:
    """
    Captura toda la pantalla.
    full_res=True -> resolución completa (para automatización).
    full_res=False -> reducida a MAX_ANALYSIS_WIDTH (para análisis con IA).
    """
    if not HAS_PIL:
        return None
    try:
        img: Image.Image = ImageGrab.grab(all_screens=True)
        if not full_res and img.width > MAX_ANALYSIS_WIDTH:
            ratio = MAX_ANALYSIS_WIDTH / img.width
            img = img.resize((MAX_ANALYSIS_WIDTH, int(img.height * ratio)), Image.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
    except Exception as exc:
        log.error("Error capturando pantalla: %s", exc)
        return None


def capture_primary_screen(full_res: bool = True) -> Optional[bytes]:
    """
    Captura solo la pantalla principal, usando el mismo espacio de coordenadas
    que PyAutoGUI para evitar desajustes al mover el raton.
    """
    if not HAS_PIL:
        return None
    try:
        img: Image.Image = ImageGrab.grab()
        if not full_res and img.width > MAX_ANALYSIS_WIDTH:
            ratio = MAX_ANALYSIS_WIDTH / img.width
            img = img.resize((MAX_ANALYSIS_WIDTH, int(img.height * ratio)), Image.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
    except Exception as exc:
        log.error("Error capturando pantalla principal: %s", exc)
        return None


def _img_to_b64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
#  Claude Computer Use
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _computer_tool_type() -> str:
    return "computer_20251124" if "2025-11-24" in ANTHROPIC_COMPUTER_BETA else "computer_20250124"


def _screen_size() -> tuple[int, int]:
    if HAS_GUI:
        size = pyautogui.size()
        return int(size.width), int(size.height)
    if HAS_PIL:
        img: Image.Image = ImageGrab.grab()
        return img.width, img.height
    raise RuntimeError("Sin acceso a pantalla")


def _anthropic_scale_factor(width: int, height: int) -> float:
    long_edge = max(width, height)
    total_pixels = width * height
    long_edge_scale = 1568 / long_edge
    total_pixels_scale = math.sqrt(1_150_000 / total_pixels)
    return min(1.0, long_edge_scale, total_pixels_scale)


def _capture_screen_for_computer_use() -> tuple[list[dict], dict]:
    if not HAS_PIL:
        raise RuntimeError("Pillow no disponible para screenshot")

    img: Image.Image = ImageGrab.grab()
    width, height = img.width, img.height
    scale = _anthropic_scale_factor(width, height)
    scaled_w = max(1, int(width * scale))
    scaled_h = max(1, int(height * scale))
    if scale < 0.999:
        img = img.resize((scaled_w, scaled_h), Image.LANCZOS)

    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    image_bytes = buf.getvalue()
    return (
        [{
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": _img_to_b64(image_bytes),
            },
        }],
        {
            "scale": scale,
            "screen_width": width,
            "screen_height": height,
            "display_width_px": scaled_w,
            "display_height_px": scaled_h,
        },
    )


def _scale_coord(value: float, scale: float, upper: int) -> int:
    raw = int(round(value / max(scale, 0.000001)))
    return max(0, min(upper - 1, raw))


def _normalize_key_name(key: str) -> str:
    k = key.strip().lower()
    mapping = {
        "page_down": "pgdn",
        "pagedown": "pgdn",
        "pageup": "pgup",
        "page_up": "pgup",
        "return": "enter",
        "escape": "esc",
        "control": "ctrl",
        "command": "win",
        "cmd": "win",
        "super": "win",
        "option": "alt",
    }
    return mapping.get(k, k)


def _press_key_combo(text: str) -> None:
    parts = [p for p in re.split(r"\s*\+\s*", text.strip()) if p]
    if not parts:
        raise RuntimeError("Combinacion de teclas vacia")
    keys = [_normalize_key_name(p) for p in parts]
    if len(keys) == 1:
        pyautogui.press(keys[0])
    else:
        pyautogui.hotkey(*keys)


def _computer_result_text(text: str) -> list[dict]:
    return [{"type": "text", "text": text}]


def _execute_computer_action(action_input: dict, state: dict) -> list[dict]:
    if not HAS_GUI:
        raise RuntimeError("PyAutoGUI no disponible para Computer Use")

    action = action_input.get("action")
    scale = float(state.get("scale", 1.0))
    screen_w = int(state.get("screen_width", _screen_size()[0]))
    screen_h = int(state.get("screen_height", _screen_size()[1]))

    if action == "screenshot":
        content, screen_state = _capture_screen_for_computer_use()
        state.update(screen_state)
        return content

    if action in {"left_click", "right_click", "middle_click", "double_click", "triple_click", "mouse_move"}:
        coord = action_input.get("coordinate") or [0, 0]
        x = _scale_coord(coord[0], scale, screen_w)
        y = _scale_coord(coord[1], scale, screen_h)
        if action == "mouse_move":
            pyautogui.moveTo(x, y, duration=0.2)
        else:
            clicks = {"left_click": 1, "right_click": 1, "middle_click": 1, "double_click": 2, "triple_click": 3}[action]
            button = "left"
            if action == "right_click":
                button = "right"
            elif action == "middle_click":
                button = "middle"
            pyautogui.click(x, y, clicks=clicks, interval=0.15, button=button)
        return _computer_result_text(f"{action} en {x},{y}")

    if action == "left_click_drag":
        start = action_input.get("start_coordinate") or action_input.get("coordinate") or [0, 0]
        end = action_input.get("end_coordinate") or action_input.get("coordinate_2") or [0, 0]
        x1 = _scale_coord(start[0], scale, screen_w)
        y1 = _scale_coord(start[1], scale, screen_h)
        x2 = _scale_coord(end[0], scale, screen_w)
        y2 = _scale_coord(end[1], scale, screen_h)
        pyautogui.moveTo(x1, y1, duration=0.2)
        pyautogui.dragTo(x2, y2, duration=0.4, button="left")
        return _computer_result_text(f"drag {x1},{y1} -> {x2},{y2}")

    if action == "left_mouse_down":
        pyautogui.mouseDown(button="left")
        return _computer_result_text("left_mouse_down ejecutado")

    if action == "left_mouse_up":
        pyautogui.mouseUp(button="left")
        return _computer_result_text("left_mouse_up ejecutado")

    if action == "scroll":
        amount = int(action_input.get("amount", 0))
        direction = str(action_input.get("direction", "down")).lower()
        signed = amount if direction in {"up", "left"} else -amount
        pyautogui.scroll(signed)
        return _computer_result_text(f"scroll {direction} {amount}")

    if action == "wait":
        seconds = float(action_input.get("duration", 1))
        time.sleep(max(0.0, min(30.0, seconds)))
        return _computer_result_text(f"wait {seconds:.2f}s")

    if action == "type":
        text = str(action_input.get("text", ""))
        pyautogui.write(text, interval=0.01)
        return _computer_result_text(f"type {len(text)} chars")

    if action == "key":
        text = str(action_input.get("text", ""))
        _press_key_combo(text)
        return _computer_result_text(f"key {text}")

    if action == "hold_key":
        text = str(action_input.get("text", ""))
        duration = float(action_input.get("duration", 0.5))
        key = _normalize_key_name(text)
        pyautogui.keyDown(key)
        try:
            time.sleep(max(0.0, min(10.0, duration)))
        finally:
            pyautogui.keyUp(key)
        return _computer_result_text(f"hold_key {text} {duration:.2f}s")

    raise RuntimeError(f"Accion no soportada: {action}")


def _anthropic_message(messages: list[dict], tools: list[dict], system: str = "") -> dict:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("Sin ANTHROPIC_API_KEY")
    _ensure_anthropic_available()
    payload = {
        "model": ANTHROPIC_COMPUTER_MODEL,
        "max_tokens": ANTHROPIC_MAX_TOKENS,
        "messages": messages,
        "tools": tools,
    }
    if system:
        payload["system"] = system
    return _post_json(
        ANTHROPIC_API,
        payload,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "anthropic-beta": ANTHROPIC_COMPUTER_BETA,
        },
        timeout=180,
    )


def _extract_text_blocks(content: list[dict]) -> str:
    texts = []
    for block in content:
        if block.get("type") == "text":
            texts.append(block.get("text", ""))
    return "\n".join(t for t in texts if t).strip()


def _anthropic_cooldown_remaining() -> int:
    remaining = int(max(0, _anthropic_cooldown_until - time.time()))
    return remaining


def _anthropic_limit_message() -> str:
    remaining = _anthropic_cooldown_remaining()
    if remaining <= 0:
        return ""
    minutes = (remaining + 59) // 60
    reason = f" Motivo: {_anthropic_cooldown_reason}." if _anthropic_cooldown_reason else ""
    return f"Anthropic esta temporalmente en cooldown durante unos {minutes} min.{reason}"


def _set_anthropic_cooldown(reason: str, minutes: int | None = None) -> None:
    global _anthropic_cooldown_until, _anthropic_cooldown_reason
    mins = minutes if minutes is not None else ANTHROPIC_COOLDOWN_MINUTES
    _anthropic_cooldown_until = time.time() + max(1, mins) * 60
    _anthropic_cooldown_reason = reason.strip()[:200]
    log.warning("Anthropic cooldown activado por %d min: %s", mins, _anthropic_cooldown_reason)


def _ensure_anthropic_available() -> None:
    msg = _anthropic_limit_message()
    if msg:
        raise RuntimeError(msg)


def _is_anthropic_limit_error(code: int | None, detail: str) -> bool:
    low = (detail or "").lower()
    if code == 429:
        return True
    markers = [
        "rate limit",
        "rate_limit",
        "usage limit",
        "credit balance",
        "quota",
        "exceeded",
        "too many requests",
    ]
    return any(marker in low for marker in markers)


def run_claude_computer_use(order: str, system: str | None = None,
                            max_steps: int | None = None,
                            cancel_evt: threading.Event | None = None) -> tuple[bool, str]:
    """
    Ejecuta una orden usando Claude Computer Use y devuelve (ok, resumen).
    """
    display_w, display_h = _screen_size()
    scale = _anthropic_scale_factor(display_w, display_h)
    tools = [{
        "type": _computer_tool_type(),
        "name": "computer",
        "display_width_px": max(1, int(display_w * scale)),
        "display_height_px": max(1, int(display_h * scale)),
    }]
    messages = [{
        "role": "user",
        "content": (
            "Ejecuta esta orden en el ordenador y termina solo cuando este realmente completada:\n\n"
            f"{order}\n\n"
            "Antes de concluir, verifica visualmente el resultado final con una captura."
        ),
    }]
    state = {
        "scale": scale,
        "screen_width": display_w,
        "screen_height": display_h,
    }

    total_steps = max_steps or ANTHROPIC_MAX_STEPS
    for step in range(1, total_steps + 1):
        if cancel_evt and cancel_evt.is_set():
            return False, "Operacion cancelada por el usuario."
        resp = _anthropic_message(messages, tools, system=system or ANTHROPIC_COMPUTER_SYSTEM)
        content = resp.get("content", [])
        stop_reason = resp.get("stop_reason", "")
        messages.append({"role": "assistant", "content": content})
        log.info("Anthropic paso %d stop_reason=%s", step, stop_reason)

        tool_results = []
        for block in content:
            if block.get("type") != "tool_use":
                continue
            tool_name = block.get("name")
            tool_id = block.get("id")
            tool_input = block.get("input", {})
            try:
                if tool_name != "computer":
                    raise RuntimeError(f"Herramienta no soportada: {tool_name}")
                result_content = _execute_computer_action(tool_input, state)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": result_content,
                })
            except Exception as exc:
                log.error("Error ejecutando tool_use %s: %s", tool_name, exc)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "is_error": True,
                    "content": _computer_result_text(str(exc)),
                })

        if not tool_results:
            final_text = _extract_text_blocks(content) or "Claude finalizo sin texto."
            return True, final_text

        messages.append({"role": "user", "content": tool_results})

    return False, f"Claude no termino tras {total_steps} pasos."


def _google_desktop_ready_reason() -> str:
    if not GOOGLE_API_KEY:
        return "sin GOOGLE_API_KEY o GEMINI_API_KEY"
    if not HAS_GOOGLE_GENAI:
        return "falta google-genai"
    if not HAS_GUI:
        return "falta PyAutoGUI/PyGetWindow"
    if not HAS_PIL:
        return "falta Pillow"
    return "OK"


def _ensure_google_desktop_available() -> None:
    reason = _google_desktop_ready_reason()
    if reason != "OK":
        raise RuntimeError(f"Agente Google no disponible: {reason}")


def _google_extract_text(parts) -> str:
    texts = []
    for part in parts or []:
        text = getattr(part, "text", None)
        if text:
            texts.append(text.strip())
    return "\n".join(t for t in texts if t).strip()


def run_google_desktop_agent(order: str,
                             max_steps: int | None = None,
                             cancel_evt: threading.Event | None = None) -> tuple[bool, str]:
    """
    Ejecuta una orden de escritorio con Gemini usando capturas y funciones
    propias de raton/teclado sobre Windows.
    """
    _ensure_google_desktop_available()
    screen_w, screen_h = _screen_size()
    client = genai.Client(api_key=GOOGLE_API_KEY)

    def _clip_x(x: int) -> int:
        return max(0, min(screen_w - 1, int(x)))

    def _clip_y(y: int) -> int:
        return max(0, min(screen_h - 1, int(y)))

    def mouse_move(x: int, y: int) -> dict:
        """Move the mouse to absolute screen coordinates in pixels."""
        pyautogui.moveTo(_clip_x(x), _clip_y(y), duration=0.12)
        return {"status": "ok", "x": _clip_x(x), "y": _clip_y(y)}

    def mouse_click(x: int, y: int, button: str = "left", clicks: int = 1) -> dict:
        """Click at absolute screen coordinates in pixels."""
        x = _clip_x(x)
        y = _clip_y(y)
        pyautogui.click(x=x, y=y, clicks=max(1, int(clicks)), button=str(button).lower())
        return {"status": "ok", "x": x, "y": y, "button": str(button).lower(), "clicks": max(1, int(clicks))}

    def mouse_double_click(x: int, y: int) -> dict:
        """Double click at absolute screen coordinates in pixels."""
        x = _clip_x(x)
        y = _clip_y(y)
        pyautogui.doubleClick(x=x, y=y)
        return {"status": "ok", "x": x, "y": y}

    def keyboard_type(text: str, press_enter: bool = False) -> dict:
        """Type text in the currently focused input field."""
        pyautogui.write(str(text), interval=0.01)
        if press_enter:
            pyautogui.press("enter")
        return {"status": "ok", "text_len": len(str(text)), "press_enter": bool(press_enter)}

    def keyboard_type_at(x: int, y: int, text: str,
                         press_enter: bool = False,
                         clear_before_typing: bool = False) -> dict:
        """Click an input field and type text there."""
        x = _clip_x(x)
        y = _clip_y(y)
        pyautogui.click(x=x, y=y)
        if clear_before_typing:
            pyautogui.hotkey("ctrl", "a")
            pyautogui.press("backspace")
        pyautogui.write(str(text), interval=0.01)
        if press_enter:
            pyautogui.press("enter")
        return {
            "status": "ok",
            "x": x,
            "y": y,
            "text_len": len(str(text)),
            "press_enter": bool(press_enter),
            "clear_before_typing": bool(clear_before_typing),
        }

    def press_keys(keys: str) -> dict:
        """Press a key or key combination like ctrl+a, alt+tab or enter."""
        parts = [p.strip().lower() for p in re.split(r"\s*\+\s*", str(keys)) if p.strip()]
        if not parts:
            raise RuntimeError("Combinacion de teclas vacia")
        if len(parts) == 1:
            pyautogui.press(parts[0])
        else:
            pyautogui.hotkey(*parts)
        return {"status": "ok", "keys": "+".join(parts)}

    def wheel_scroll(direction: str = "down", amount: int = 600) -> dict:
        """Scroll the mouse wheel up or down by a given amount."""
        direction = str(direction).lower().strip()
        amount = max(50, min(3000, int(amount)))
        if direction == "up":
            pyautogui.scroll(amount)
        elif direction == "down":
            pyautogui.scroll(-amount)
        else:
            raise RuntimeError("La direccion debe ser up o down")
        return {"status": "ok", "direction": direction, "amount": amount}

    def wait_seconds(seconds: float = 1.0) -> dict:
        """Wait a short time to let the UI update."""
        seconds = max(0.1, min(10.0, float(seconds)))
        time.sleep(seconds)
        return {"status": "ok", "waited": seconds}

    tools = [
        mouse_move,
        mouse_click,
        mouse_double_click,
        keyboard_type,
        keyboard_type_at,
        press_keys,
        wheel_scroll,
        wait_seconds,
    ]
    tool_map = {fn.__name__: fn for fn in tools}
    declarations = [
        google_types.FunctionDeclaration.from_callable(client=client, callable=fn)
        for fn in tools
    ]
    excluded_predefined_functions = [
        "open_web_browser",
        "wait_5_seconds",
        "go_back",
        "go_forward",
        "search",
        "navigate",
        "click_at",
        "hover_at",
        "type_text_at",
        "key_combination",
        "scroll_document",
        "scroll_at",
        "drag_and_drop",
    ]
    config = google_types.GenerateContentConfig(
        system_instruction=(
            "Eres un operador de escritorio en Windows. "
            "Debes analizar la captura actual y usar SOLO las funciones disponibles para mover el raton, hacer click, escribir, pulsar teclas, esperar y hacer scroll. "
            "Las coordenadas x,y son ABSOLUTAS en pixeles sobre la pantalla principal. "
            f"La resolucion actual es {screen_w}x{screen_h}. "
            "No inventes estados no visibles. Tras cada accion se te enviara una nueva captura. "
            "Cuando la tarea haya terminado, deja de llamar funciones y responde con un resumen corto en espanol."
        ),
        tools=[
            google_types.Tool(
                computer_use=google_types.ComputerUse(
                    environment=google_types.Environment.ENVIRONMENT_BROWSER,
                    excluded_predefined_functions=excluded_predefined_functions,
                )
            ),
            google_types.Tool(function_declarations=declarations),
        ],
    )
    initial_screen = capture_primary_screen(full_res=True)
    if initial_screen is None:
        raise RuntimeError("No pude capturar la pantalla principal")
    contents = [
        google_types.Content(
            role="user",
            parts=[
                google_types.Part(
                    text=(
                        "Ejecuta esta orden en el ordenador usando solo las funciones disponibles:\n\n"
                        f"{order}\n\n"
                        "Si necesitas verificar el resultado final, espera a tener la nueva captura y entonces responde."
                    )
                ),
                google_types.Part.from_bytes(data=initial_screen, mime_type="image/png"),
            ],
        )
    ]

    total_steps = max_steps or GOOGLE_DESKTOP_MAX_STEPS
    try:
        for step in range(1, total_steps + 1):
            if cancel_evt and cancel_evt.is_set():
                return False, "Operacion cancelada por el usuario."
            response = client.models.generate_content(
                model=GOOGLE_DESKTOP_MODEL,
                contents=contents,
                config=config,
            )
            candidate = response.candidates[0]
            contents.append(candidate.content)
            function_calls = [
                getattr(part, "function_call", None)
                for part in (candidate.content.parts or [])
                if getattr(part, "function_call", None)
            ]
            log.info("Google desktop paso %d function_calls=%d", step, len(function_calls))
            if not function_calls:
                final_text = _google_extract_text(candidate.content.parts)
                return True, final_text or "Google ha terminado sin texto final."

            tool_results = []
            for call in function_calls:
                fn = tool_map.get(call.name)
                try:
                    if fn is None:
                        raise RuntimeError(f"Funcion no soportada: {call.name}")
                    args = dict(call.args or {})
                    result = fn(**args)
                except Exception as exc:
                    log.error("Google desktop funcion %s fallo: %s", call.name, exc)
                    result = {"error": str(exc)}
                tool_results.append(
                    google_types.Part.from_function_response(name=call.name, response=result)
                )

            updated_screen = capture_primary_screen(full_res=True)
            if updated_screen is None:
                raise RuntimeError("No pude capturar la pantalla tras la accion")
            tool_results.append(
                google_types.Part.from_bytes(data=updated_screen, mime_type="image/png")
            )
            contents.append(google_types.Content(role="user", parts=tool_results))
        return False, f"Google no termino tras {total_steps} pasos."
    finally:
        try:
            client.close()
        except Exception:
            pass

# ─────────────────────────────────────────────────────────────────────────────
#  Proveedores de visión
# ─────────────────────────────────────────────────────────────────────────────

def _vision_gemini(image_bytes: bytes, prompt: str, system: str = "",
                   max_tokens: int = 50) -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("Sin GEMINI_API_KEY")
    parts = []
    if system:
        parts.append({"text": system + "\n\n"})
    parts.append({"inline_data": {"mime_type": "image/png", "data": _img_to_b64(image_bytes)}})
    parts.append({"text": prompt})
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{GEMINI_VISION_MODEL}:generateContent?key={GEMINI_API_KEY}")
    resp = _post_json(url, {
        "contents": [{"parts": parts}],
        "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0},
    })
    return resp["candidates"][0]["content"]["parts"][0]["text"].strip()


def _vision_groq(image_bytes: bytes, prompt: str, system: str = "",
                 max_tokens: int = 50) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("Sin GROQ_API_KEY")
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{_img_to_b64(image_bytes)}"}},
        {"type": "text", "text": prompt},
    ]})
    resp = _post_json(
        "https://api.groq.com/openai/v1/chat/completions",
        {"model": GROQ_VISION_MODEL, "messages": messages,
         "max_tokens": max_tokens, "temperature": 0},
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
    )
    return resp["choices"][0]["message"]["content"].strip()


def _vision_openrouter(image_bytes: bytes, prompt: str, system: str = "",
                       max_tokens: int = 50) -> str:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("Sin OPENROUTER_API_KEY")
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{_img_to_b64(image_bytes)}"}},
        {"type": "text", "text": prompt},
    ]})
    resp = _post_json(
        "https://openrouter.ai/api/v1/chat/completions",
        {"model": OPENROUTER_VISION_MODEL, "messages": messages,
         "max_tokens": max_tokens, "temperature": 0},
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://inspector.local",
            "X-Title": "Inspector 0.1",
        },
    )
    return resp["choices"][0]["message"]["content"].strip()


def _vision_lmstudio(image_bytes: bytes, prompt: str, system: str = "",
                     max_tokens: int = 50) -> str:
    models = _lmstudio_models()
    if not models:
        raise RuntimeError("LM Studio sin modelos cargados")
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{_img_to_b64(image_bytes)}"}},
        {"type": "text", "text": prompt},
    ]})
    resp = _post_json(
        f"{LMSTUDIO_BASE_URL}/v1/chat/completions",
        {"model": models[0], "messages": messages,
         "max_tokens": max_tokens, "temperature": 0},
        use_ssl=False,
        timeout=60,
    )
    return resp["choices"][0]["message"]["content"].strip()


def _lmstudio_models() -> list[str]:
    try:
        data = _get_json(f"{LMSTUDIO_BASE_URL}/v1/models", use_ssl=False)
        return [m["id"] for m in data.get("data", [])]
    except Exception:
        return []


# Tabla de proveedores: nombre → función
_VISION_PROVIDERS: list[tuple[str, Callable]] = [
    ("Gemini",      _vision_gemini),
    ("Groq",        _vision_groq),
    ("OpenRouter",  _vision_openrouter),
    ("LM Studio",   _vision_lmstudio),
]


def vision_call(image_bytes: bytes, prompt: str, system: str = "",
                max_tokens: int = 50) -> tuple[str, str]:
    """
    Llama a los proveedores de visión en orden hasta que uno funcione.
    Devuelve (respuesta_texto, nombre_proveedor).
    """
    for name, fn in _VISION_PROVIDERS:
        try:
            result = fn(image_bytes, prompt, system, max_tokens)
            log.info("Vision [%s]: %r", name, result[:60])
            return result, name
        except Exception as exc:
            log.debug("Vision [%s] fallo: %s", name, exc)
    log.error("Todos los proveedores de vision fallaron")
    return "OK", "ninguno"


def analyze_screen(image_bytes: bytes) -> tuple[str, str]:
    """
    Analiza la pantalla para el monitor.
    Devuelve (estado, proveedor): estado es OK | AVISO | FIN.
    """
    raw, provider = vision_call(image_bytes, VISION_PROMPT, VISION_SYSTEM, max_tokens=10)
    raw_up = raw.upper()
    for word in ("FIN", "AVISO", "OK"):
        if word in raw_up:
            return word, provider
    return "OK", provider


def _gemini_progress_json(image_bytes: bytes, prompt: str) -> dict:
    """Pide a Gemini un JSON corto y lo parsea de forma tolerante."""
    raw = _vision_gemini(image_bytes, prompt, system=CODEX_PROGRESS_SYSTEM, max_tokens=120)
    data = _extract_json_block(raw)
    estado = str(data.get("estado", "SIGUE")).upper()
    motivo = str(data.get("motivo", "")).strip()
    if estado not in {"SIGUE", "TERMINADO", "BLOQUEADO"}:
        estado = "SIGUE"
    return {"estado": estado, "motivo": motivo, "raw": raw}


def _extract_json_block(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.I)
        raw = re.sub(r"\s*```$", "", raw)
    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        raise RuntimeError(f"JSON invalido: {raw[:160]}")
    return json.loads(match.group(0))


def _codex_json(image_bytes: bytes, prompt: str, system: str, max_tokens: int = 120) -> dict:
    last_exc: Exception | None = None
    for attempt in range(1, 4):
        try:
            raw = _vision_gemini(image_bytes, prompt, system=system, max_tokens=max_tokens)
            break
        except urllib.error.HTTPError as exc:
            last_exc = exc
            if exc.code not in {429, 500, 503} or attempt >= 3:
                raise
            time.sleep(1.5 * attempt)
        except urllib.error.URLError as exc:
            last_exc = exc
            if attempt >= 3:
                raise
            time.sleep(1.5 * attempt)
    else:
        raise RuntimeError(f"No pude consultar Gemini: {last_exc}")
    data = _extract_json_block(raw)
    data["raw"] = raw
    return data


def _codex_prompt_snippet(text: str, max_chars: int = 80) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def codex_panel_status(image_bytes: bytes) -> tuple[str, str]:
    """
    Evalua el panel de Codex y devuelve (estado, motivo).
    estado es SIGUE | TERMINADO | BLOQUEADO.
    """
    prompt = (
        "Analiza esta captura del panel derecho de Codex en Visual Studio Code. "
        "Decide si Codex sigue generando respuesta, si ya termino o si esta bloqueado."
    )
    data = _gemini_progress_json(image_bytes, prompt)
    return data["estado"], data["motivo"]


def codex_panel_summary(image_bytes: bytes) -> str:
    """Resume la respuesta visible de Codex justo encima de la caja de entrada."""
    prompt = (
        "Resume la respuesta visible de Codex en esta captura, fijandote sobre todo en el texto "
        "que aparece justo encima de la caja inferior de entrada. "
        "Extrae la conclusion, los puntos utiles y cualquier respuesta final visible para el usuario. "
        "No describas iconos, botones ni elementos de interfaz salvo que sean importantes."
    )
    return _vision_gemini(image_bytes, prompt, system=CODEX_RESULT_SYSTEM, max_tokens=220)


def codex_input_status(image_bytes: bytes, prompt_text: str = "") -> tuple[str, str]:
    snippet = _codex_prompt_snippet(prompt_text)
    prompt = (
        "Analiza esta captura de la zona inferior del panel Codex en Visual Studio Code. "
        "Decide si se ve la caja grande de entrada de Codex, si contiene un borrador del usuario o si no es la caja correcta."
    )
    if snippet:
        prompt += f" La peticion esperada empieza por: '{snippet}'."
    data = _codex_json(image_bytes, prompt, CODEX_INPUT_SYSTEM, max_tokens=120)
    estado = str(data.get("estado", "NO_INPUT")).upper()
    if estado not in {"INPUT_VISIBLE", "BORRADOR", "NO_INPUT"}:
        estado = "NO_INPUT"
    return estado, str(data.get("motivo", "")).strip()


def codex_send_status(image_bytes: bytes, prompt_text: str = "") -> tuple[str, str]:
    snippet = _codex_prompt_snippet(prompt_text)
    prompt = (
        "Analiza esta captura completa del panel Codex en Visual Studio Code y decide si la peticion ya ha sido enviada."
    )
    if snippet:
        prompt += f" La peticion del usuario empieza por: '{snippet}'."
    data = _codex_json(image_bytes, prompt, CODEX_SEND_SYSTEM, max_tokens=140)
    estado = str(data.get("estado", "DUDOSO")).upper()
    if estado not in {"ENVIADO", "NO_ENVIADO", "DUDOSO"}:
        estado = "DUDOSO"
    return estado, str(data.get("motivo", "")).strip()


def codex_activity_status(image_bytes: bytes) -> tuple[str, str]:
    prompt = (
        "Analiza esta captura de la zona inferior del panel Codex. "
        "Decide si Codex esta trabajando fijandote especialmente en si aparece el boton stop con un cuadrado negro dentro."
    )
    data = _codex_json(image_bytes, prompt, CODEX_ACTIVITY_SYSTEM, max_tokens=100)
    estado = str(data.get("estado", "DUDOSO")).upper()
    if estado not in {"TRABAJANDO", "NO_TRABAJANDO", "DUDOSO"}:
        estado = "DUDOSO"
    return estado, str(data.get("motivo", "")).strip()


# ─────────────────────────────────────────────────────────────────────────────
#  Routing de órdenes (Code vs Cowork)
# ─────────────────────────────────────────────────────────────────────────────
def codex_ready_for_followup(panel_bytes: bytes, input_bytes: Optional[bytes] = None) -> tuple[bool, str]:
    """
    Detecta si Codex ya no esta trabajando y el compositor vuelve a estar listo
    para recibir una nueva pregunta del usuario.
    """
    actividad, motivo_actividad = codex_activity_status(panel_bytes)
    if actividad == "TRABAJANDO":
        return False, motivo_actividad

    input_bytes = input_bytes or capture_codex_input() or panel_bytes
    input_estado, motivo_input = codex_input_status(input_bytes)
    if input_estado in {"INPUT_VISIBLE", "BORRADOR"}:
        return True, (
            "Codex ya esta listo para una nueva pregunta. "
            + (motivo_input or motivo_actividad)
        ).strip()
    return False, motivo_input or motivo_actividad


_CODE_KEYWORDS = {
    "codigo", "code", "script", "programa", "funcion", "función", "bug",
    "error", "python", "javascript", "js", "html", "css", "api", "database",
    "git", "terminal", "bash", "powershell", "cmd", "compilar", "debugg",
    "instala", "pip", "npm", "clase", "modulo", "módulo", "archivo .py",
    "test", "pytest", "refactor",
}


def _text_route(order: str) -> str:
    """Keyword fallback para routing sin API."""
    low = order.lower()
    if any(kw in low for kw in _CODE_KEYWORDS):
        return "CODE"
    return "COWORK"


def _gemini_text(prompt: str, system: str = "", max_tokens: int = 10) -> str:
    """Llamada de texto puro a Gemini (sin imagen, muy barato)."""
    if not GEMINI_API_KEY:
        raise RuntimeError("Sin GEMINI_API_KEY")
    full = (system + "\n\n" + prompt) if system else prompt
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{GEMINI_TEXT_MODEL}:generateContent?key={GEMINI_API_KEY}")
    resp = _post_json(url, {
        "contents": [{"parts": [{"text": full}]}],
        "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0},
    })
    return resp["candidates"][0]["content"]["parts"][0]["text"].strip()


def route_order(order: str) -> str:
    """Decide si la orden debe ir a Code o Cowork. Devuelve 'CODE' | 'COWORK'."""
    try:
        result = _gemini_text(f"Tarea: {order}", system=ROUTE_SYSTEM, max_tokens=5)
        return "CODE" if "CODE" in result.upper() else "COWORK"
    except Exception as exc:
        log.warning("Routing por API fallo (%s), usando keywords.", exc)
        return _text_route(order)


# ─────────────────────────────────────────────────────────────────────────────
#  Automatización de Claude Desktop
# ─────────────────────────────────────────────────────────────────────────────

def _clipboard_set(text: str) -> bool:
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()
        return True
    except Exception as exc:
        log.error("Error portapapeles: %s", exc)
        return False


def _find_window_by_title_fragments(title_fragments: list[str]):
    """Busca la primera ventana util cuyo titulo contenga alguno de los fragmentos."""
    if not HAS_GUI:
        return None
    try:
        for title_fragment in title_fragments:
            for win in gw.getWindowsWithTitle(title_fragment):
                if not getattr(win, "title", "").strip():
                    continue
                if getattr(win, "width", 0) < 500 or getattr(win, "height", 0) < 350:
                    continue
                log.info("Ventana encontrada: '%s'", win.title)
                return win
    except Exception as exc:
        log.error("Error buscando ventana: %s", exc)
    return None


def _find_claude_window():
    """Busca la ventana de Claude Desktop. Devuelve el objeto ventana o None."""
    return _find_window_by_title_fragments(["Claude", "claude"])


def _find_vscode_window(prefer_codex_target: bool = False):
    """Busca la ventana principal de Visual Studio Code."""
    if not HAS_GUI:
        return None
    try:
        project_tokens = [Path.cwd().name.lower(), "inspector"]
        target_tokens = ["codex", "test", "untitled", "welcome"]
        candidates = []
        for win in gw.getAllWindows():
            title = getattr(win, "title", "").strip()
            if not title:
                continue
            low = title.lower()
            if "visual studio code" not in low and not low.endswith(" - code"):
                continue
            if getattr(win, "width", 0) < 500 or getattr(win, "height", 0) < 350:
                continue
            score = 0
            if getattr(win, "isActive", False):
                score += 20
            if prefer_codex_target:
                for token in target_tokens:
                    if token in low:
                        score += 6
                for token in project_tokens:
                    if token and token in low:
                        score -= 12
            else:
                for token in [*project_tokens, "codex"]:
                    if token and token in low:
                        score += 5
            candidates.append((score, win))
        if candidates:
            candidates.sort(key=lambda item: item[0], reverse=True)
            win = candidates[0][1]
            log.info(
                "Ventana VS Code elegida%s: '%s'",
                " para Codex" if prefer_codex_target else "",
                win.title,
            )
            return win
    except Exception as exc:
        log.error("Error buscando ventana VS Code: %s", exc)
    return _find_window_by_title_fragments([
        "Visual Studio Code",
        " - Visual Studio Code",
        " - Code",
    ])


def _safe_ascii(text: str) -> str:
    return (text or "").encode("ascii", "backslashreplace").decode()


def _find_uia_vscode_window(prefer_codex_target: bool = False):
    if not HAS_UIA:
        return None
    try:
        target = _find_vscode_window(prefer_codex_target=prefer_codex_target)
        target_title = getattr(target, "title", "") if target else ""
        windows = UIADesktop(backend="uia").windows()
        candidates = []
        for win in windows:
            title = win.window_text()
            low = title.lower()
            if "visual studio code" not in low:
                continue
            score = 0
            if target_title and title == target_title:
                score += 100
            if prefer_codex_target:
                if "test" in low or "untitled" in low:
                    score += 15
                if "inspector" in low:
                    score -= 10
            candidates.append((score, win))
        if candidates:
            candidates.sort(key=lambda item: item[0], reverse=True)
            return candidates[0][1]
    except Exception as exc:
        log.warning("No pude localizar ventana UIA de VS Code: %s", exc)
    return None


def _uia_codex_input_anchor() -> Optional[tuple[int, int]]:
    """
    Usa UI Automation para ubicar la fila de controles del compositor de Codex y
    devuelve un punto seguro dentro del area editable justo por encima de esa fila.
    """
    if not HAS_UIA:
        return None
    try:
        win = _find_uia_vscode_window(prefer_codex_target=True)
        if not win:
            return None
        anchors = []
        for label in ("Add files and more", "IDE context", "Plan"):
            matches = [
                d for d in win.descendants()
                if d.element_info.control_type == "Button" and d.window_text() == label
            ]
            if matches:
                anchors.append(matches[0].rectangle())
        if not anchors:
            return None
        left = min(rect.left for rect in anchors)
        top = min(rect.top for rect in anchors)
        return left + 40, top - 28
    except Exception as exc:
        log.warning("No pude calcular anclaje UIA del input de Codex: %s", exc)
        return None


def _uia_click_codex_button(label: str) -> bool:
    if not HAS_UIA:
        return False
    try:
        win = _find_uia_vscode_window(prefer_codex_target=True)
        if not win:
            return False
        matches = [
            d for d in win.descendants()
            if d.element_info.control_type == "Button" and d.window_text() == label
        ]
        if not matches:
            return False
        matches[0].click_input()
        time.sleep(0.6)
        return True
    except Exception as exc:
        log.warning("No pude pulsar por UIA el boton '%s': %s", label, exc)
        return False


def _crop_window_region(win, left_ratio: float, top_ratio: float,
                        right_ratio: float, bottom_ratio: float) -> Optional[bytes]:
    """Captura una region relativa de una ventana concreta."""
    if not HAS_PIL or not win:
        return None
    try:
        img: Image.Image = ImageGrab.grab(all_screens=True)
        left = int(win.left + win.width * left_ratio)
        top = int(win.top + win.height * top_ratio)
        right = int(win.left + win.width * right_ratio)
        bottom = int(win.top + win.height * bottom_ratio)
        right = max(right, left + 10)
        bottom = max(bottom, top + 10)
        crop = img.crop((left, top, right, bottom))
        buf = BytesIO()
        crop.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
    except Exception as exc:
        log.error("Error capturando region de ventana: %s", exc)
        return None


def _window_region_bbox(win, left_ratio: float, top_ratio: float,
                        right_ratio: float, bottom_ratio: float) -> tuple[int, int, int, int]:
    left = int(win.left + win.width * left_ratio)
    top = int(win.top + win.height * top_ratio)
    right = int(win.left + win.width * right_ratio)
    bottom = int(win.top + win.height * bottom_ratio)
    right = max(right, left + 10)
    bottom = max(bottom, top + 10)
    return left, top, right, bottom


def _capture_bbox(bbox: tuple[int, int, int, int]) -> Optional[bytes]:
    if not HAS_PIL:
        return None
    try:
        img: Image.Image = ImageGrab.grab(all_screens=True)
        crop = img.crop(bbox)
        buf = BytesIO()
        crop.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
    except Exception as exc:
        log.error("Error capturando bbox: %s", exc)
        return None


def _codex_region_bbox(win, region: str = "panel") -> tuple[int, int, int, int]:
    panel_bbox = _window_region_bbox(
        win,
        CODEX_PANEL_LEFT_RATIO,
        CODEX_PANEL_TOP_RATIO,
        CODEX_PANEL_RIGHT_RATIO,
        CODEX_PANEL_BOTTOM_RATIO,
    )
    if region == "panel":
        return panel_bbox
    left, top, right, bottom = panel_bbox
    width = right - left
    height = bottom - top
    if region == "body":
        return (
            left,
            top + int(height * CODEX_BODY_TOP_IN_PANEL),
            right,
            top + int(height * CODEX_BODY_BOTTOM_IN_PANEL),
        )
    if region == "input":
        return (
            left,
            top + int(height * CODEX_INPUT_TOP_IN_PANEL),
            right,
            top + int(height * CODEX_INPUT_BOTTOM_IN_PANEL),
        )
    raise ValueError(f"Region Codex desconocida: {region}")


def capture_codex_panel(full_panel: bool = True) -> Optional[bytes]:
    """Captura el panel derecho de Codex en VS Code usando una heuristica estable."""
    win = _find_vscode_window(prefer_codex_target=True)
    if not win:
        return None
    return _capture_bbox(_codex_region_bbox(win, "panel" if full_panel else "body"))


def capture_codex_body() -> Optional[bytes]:
    win = _find_vscode_window(prefer_codex_target=True)
    if not win:
        return None
    return _capture_bbox(_codex_region_bbox(win, "body"))


def capture_codex_input() -> Optional[bytes]:
    win = _find_vscode_window(prefer_codex_target=True)
    if not win:
        return None
    return _capture_bbox(_codex_region_bbox(win, "input"))


def _codex_input_click_point(win) -> tuple[int, int]:
    left, top, right, bottom = _codex_region_bbox(win, "panel")
    width = right - left
    height = bottom - top
    x = left + int(width * CODEX_INPUT_CLICK_X_IN_PANEL)
    y = top + int(height * CODEX_INPUT_CLICK_Y_IN_PANEL)
    return x, y


def _image_change_pct(prev_bytes: bytes, curr_bytes: bytes) -> float:
    """Porcentaje aproximado de cambio entre dos imagenes."""
    prev = Image.open(BytesIO(prev_bytes)).convert("L")
    curr = Image.open(BytesIO(curr_bytes)).convert("L")
    if prev.size != curr.size:
        curr = curr.resize(prev.size, Image.LANCZOS)
    diff = ImageChops.difference(prev, curr)
    mask = diff.point(lambda p: 255 if p > 12 else 0)
    changed_pixels = ImageStat.Stat(mask).sum[0] / 255.0
    total_pixels = max(1, mask.width * mask.height)
    return (changed_pixels / total_pixels) * 100.0


def _find_element_coords(image_bytes: bytes, description: str) -> Optional[tuple[int, int]]:
    """
    Usa un modelo de visión para localizar un elemento UI y devuelve sus coordenadas.
    IMPORTANTE: la imagen debe estar a resolución completa (sin escalar).
    """
    prompt = (
        f"En esta captura de pantalla de Windows, encuentra: '{description}'. "
        f"Responde SOLO con las coordenadas del centro en formato 'x,y' (enteros). "
        f"Si no lo encuentras, responde 'none'."
    )
    raw, _ = vision_call(image_bytes, prompt, system=FIND_ELEMENT_SYSTEM, max_tokens=20)
    raw = raw.strip().lower().replace(" ", "")
    if raw == "none" or "," not in raw:
        return None
    # Extraer primeros dos números
    nums = re.findall(r"\d+", raw)
    if len(nums) >= 2:
        return int(nums[0]), int(nums[1])
    return None


def _find_element_coords_in_crop(image_bytes: bytes, description: str) -> Optional[tuple[int, int]]:
    prompt = (
        f"En esta captura recortada de una interfaz, encuentra: '{description}'. "
        "Responde SOLO con las coordenadas del centro en formato 'x,y' relativas a esta imagen recortada. "
        "El origen 0,0 es la esquina superior izquierda del recorte. "
        "Si no lo encuentras, responde 'none'."
    )
    raw, _ = vision_call(image_bytes, prompt, system=FIND_ELEMENT_SYSTEM, max_tokens=20)
    raw = raw.strip().lower().replace(" ", "")
    if raw == "none" or "," not in raw:
        return None
    nums = re.findall(r"\d+", raw)
    if len(nums) >= 2:
        return int(nums[0]), int(nums[1])
    return None


def _activate_window(win) -> bool:
    """Activa (trae al frente) la ventana dada."""
    try:
        if win.isMinimized:
            win.restore()
            time.sleep(0.5)
        win.activate()
        time.sleep(0.8)
        return True
    except Exception as exc:
        log.error("No se pudo activar la ventana: %s", exc)
        return False


def _find_codex_input_coords(win) -> Optional[tuple[int, int]]:
    image_bytes = capture_primary_screen(full_res=True)
    if not image_bytes:
        return None
    try:
        coords = _find_element_coords(
            image_bytes,
            "la caja inferior Ask Codex anything del panel Codex de Visual Studio Code donde el usuario escribe"
        )
    except Exception as exc:
        log.warning("No pude localizar input de Codex por vision: %s", exc)
        return None
    if not coords:
        return None
    x, y = coords
    if not (win.left <= x <= win.left + win.width and win.top <= y <= win.top + win.height):
        return None
    return x, y


def _focus_codex_input(win, prefer_vision: bool = False) -> tuple[bool, str]:
    coords = _uia_codex_input_anchor()
    if coords:
        px, py = coords
        pyautogui.click(px, py)
        time.sleep(0.35)
        return True, "input clicado por UI Automation"
    if prefer_vision:
        coords = _find_codex_input_coords(win)
        if coords:
            px, py = coords
            pyautogui.click(px, py)
            time.sleep(0.35)
            return True, "input clicado por vision"
    x, y = _codex_input_click_point(win)
    pyautogui.click(x, y)
    time.sleep(0.35)
    return True, "input clicado por heuristica"


def _find_codex_send_button_coords(win) -> Optional[tuple[int, int]]:
    left, top, right, bottom = _codex_region_bbox(win, "input")
    width = right - left
    height = bottom - top
    min_x = left + int(width * 0.78)
    min_y = top + int(height * 0.22)
    max_y = top + int(height * 0.82)

    full_screen = capture_primary_screen(full_res=True)
    if full_screen:
        try:
            coords = _find_element_coords(
                full_screen,
                "el boton circular de enviar con una flecha hacia arriba situado en el extremo derecho de la caja de entrada de Codex en Visual Studio Code",
            )
        except Exception as exc:
            log.warning("No pude localizar el boton de envio de Codex en pantalla completa: %s", exc)
            coords = None
        if coords:
            x, y = coords
            if min_x <= x <= right and min_y <= y <= max_y:
                return x, y

    bbox = (left, top, right, bottom)
    image_bytes = _capture_bbox(bbox)
    if not image_bytes:
        return right - max(32, int(width * 0.04)), top + int(height * 0.55)
    try:
        coords = _find_element_coords_in_crop(
            image_bytes,
            "el boton circular de enviar con una flecha hacia arriba situado en el extremo derecho de la caja de entrada de Codex",
        )
    except Exception as exc:
        log.warning("No pude localizar el boton de envio de Codex: %s", exc)
        coords = None
    if coords:
        x, y = coords
        if 0 <= x <= width and 0 <= y <= height:
            abs_x = left + x
            abs_y = top + y
            if min_x <= abs_x <= right and min_y <= abs_y <= max_y:
                return abs_x, abs_y
        if min_x <= x <= right and min_y <= y <= max_y:
            return x, y
    fallback_x = right - max(32, int(width * 0.04))
    fallback_y = top + int(height * 0.55)
    return fallback_x, fallback_y


def _submit_codex_input(win, method: str = "boton") -> str:
    if method == "boton":
        coords = _find_codex_send_button_coords(win)
        if coords:
            pyautogui.click(*coords)
            time.sleep(1.0)
            return "boton"
        method = "enter"
    if method == "enter":
        pyautogui.press("enter")
        time.sleep(0.8)
        return "enter"
    if method == "ctrl+enter":
        pyautogui.hotkey("ctrl", "enter")
        time.sleep(0.8)
        return "ctrl+enter"
    raise ValueError(f"Metodo de envio Codex desconocido: {method}")


def _paste_into_codex_input(win, text: str) -> tuple[bool, str]:
    if not _clipboard_set(text):
        return False, "Error al copiar al portapapeles"
    if not _activate_window(win):
        return False, "No se pudo reactivar la ventana de VS Code tras copiar al portapapeles"
    _focus_codex_input(win, prefer_vision=False)
    time.sleep(0.15)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.12)
    pyautogui.press("backspace")
    time.sleep(0.18)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.45)
    return True, "texto pegado"


def send_to_codex(text: str) -> tuple[bool, str]:
    if not HAS_GUI:
        return False, "PyAutoGUI no disponible"

    win = _find_vscode_window(prefer_codex_target=True)
    if not win:
        return False, "Visual Studio Code no encontrado"
    if not _activate_window(win):
        return False, "No se pudo activar la ventana de Visual Studio Code"

    current_panel = capture_codex_panel(full_panel=True)
    if current_panel:
        try:
            actividad, motivo = codex_activity_status(current_panel)
            log.info("Codex actividad previa al envio: %s (%s)", actividad, motivo)
            if actividad == "TRABAJANDO":
                return False, "Codex ya esta trabajando; espera a que desaparezca el boton stop antes de enviar otra peticion."
        except Exception as exc:
            log.warning("No pude evaluar actividad previa de Codex: %s", exc)

    last_msg = "No pude enfocar la caja de Codex"

    for attempt in range(1, 4):
        body_before = capture_codex_body()
        ok, msg = _focus_codex_input(win, prefer_vision=(attempt == 1))
        if not ok:
            last_msg = msg
            continue
        log.info("Codex input listo (intento %d): %s", attempt, msg)

        ok, msg = _paste_into_codex_input(win, text)
        if not ok:
            return False, msg

        panel_after_paste = capture_codex_panel(full_panel=True)
        if panel_after_paste:
            try:
                estado, motivo = codex_send_status(panel_after_paste, text)
                log.info("Codex borrador tras pegar: %s (%s)", estado, motivo)
                if estado != "NO_ENVIADO":
                    last_msg = f"No pude confirmar el borrador en Codex: {estado} ({motivo})"
            except Exception as exc:
                log.warning("No pude validar borrador de Codex: %s", exc)
                last_msg = f"Gemini no pudo validar el borrador: {exc}"

        for submit_method in ("enter", "ctrl+enter", "boton"):
            submit_via = _submit_codex_input(win, submit_method)
            log.info("Codex intento de envio mediante: %s", submit_via)

            panel_after_send = capture_codex_panel(full_panel=True)
            body_after_send = capture_codex_body()
            send_ok = False
            body_changed = False
            actividad = "DUDOSO"
            if body_before and body_after_send:
                body_change = _image_change_pct(body_before, body_after_send)
                log.info("Codex envio cambio body=%.4f%%", body_change)
                body_changed = body_change >= CODEX_SEND_STABILITY_PCT
            if panel_after_send:
                try:
                    actividad, motivo = codex_activity_status(panel_after_send)
                    log.info("Codex actividad tras enter: %s (%s)", actividad, motivo)
                    if actividad == "TRABAJANDO":
                        send_ok = True
                except Exception as exc:
                    log.warning("No pude validar actividad de Codex tras enviar: %s", exc)
            if panel_after_send:
                try:
                    estado, motivo = codex_send_status(panel_after_send, text)
                    log.info("Codex send status: %s (%s)", estado, motivo)
                    if estado == "ENVIADO":
                        send_ok = True
                    elif estado == "NO_ENVIADO" and not send_ok and actividad != "TRABAJANDO":
                        send_ok = False
                        last_msg = f"Codex sigue mostrando el prompt sin enviar: {motivo or 'sin motivo'}"
                    elif estado == "DUDOSO" and not send_ok and body_changed:
                        send_ok = True
                    elif estado == "DUDOSO" and not send_ok:
                        last_msg = f"No pude confirmar con seguridad el envio: {motivo or 'sin motivo'}"
                except Exception as exc:
                    log.warning("No pude validar envio a Codex: %s", exc)
            if send_ok:
                return True, "Peticion enviada al panel Codex"
        time.sleep(0.5)

    return False, last_msg or "No pude confirmar visualmente que la peticion se enviara a Codex"


def send_to_claude(text: str, tab: str = "COWORK") -> tuple[bool, str]:
    """
    Envía texto a Claude Desktop en la pestaña indicada (CODE o COWORK).
    Devuelve (exito, mensaje_estado).

    Estrategia:
      1. Encuentra la ventana de Claude Desktop.
      2. La trae al frente.
      3. Captura pantalla completa y usa visión para localizar la pestaña.
      4. Hace clic en la pestaña.
      5. Localiza el campo de texto y hace clic.
      6. Pega el texto y pulsa Enter.
    """
    if not HAS_GUI:
        return False, "PyAutoGUI no disponible"

    win = _find_claude_window()
    if not win:
        return False, "Claude Desktop no encontrado (asegurate de que esta abierto)"

    if not _activate_window(win):
        return False, "No se pudo activar la ventana de Claude"

    tab_label = "Code" if tab == "CODE" else "Cowork"
    log.info("Buscando pestana '%s' en Claude Desktop...", tab_label)

    # Captura a resolución completa para coordenadas precisas
    screenshot = capture_screen(full_res=True)
    if not screenshot:
        return False, "No se pudo capturar la pantalla"

    # Buscar la pestaña con vision
    coords = _find_element_coords(
        screenshot,
        f"boton o pestana '{tab_label}' en la barra superior de la aplicacion Claude Desktop"
    )

    if coords:
        x, y = coords
        log.info("Pestana '%s' encontrada en (%d, %d). Haciendo clic...", tab_label, x, y)
        pyautogui.click(x, y)
        time.sleep(1.2)
    else:
        log.warning("No se encontro la pestana '%s' visualmente. Continuando en pestana actual.", tab_label)

    # Buscar el campo de entrada de texto
    screenshot2 = capture_screen(full_res=True)
    if screenshot2:
        input_coords = _find_element_coords(
            screenshot2,
            "campo de texto de entrada (input) en la parte inferior de Claude Desktop"
        )
        if input_coords:
            ix, iy = input_coords
            log.info("Campo de texto encontrado en (%d, %d). Haciendo clic...", ix, iy)
            pyautogui.click(ix, iy)
            time.sleep(0.4)
        else:
            log.warning("Campo de texto no encontrado. Intentando clic en zona inferior...")
            # Fallback: clic en la parte inferior central de la ventana
            try:
                cx = win.left + win.width // 2
                cy = win.top + int(win.height * 0.92)
                pyautogui.click(cx, cy)
                time.sleep(0.4)
            except Exception:
                pass

    # Pegar texto y enviar
    if not _clipboard_set(text):
        return False, "Error al copiar al portapapeles"

    time.sleep(0.3)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.5)
    pyautogui.press("enter")
    log.info("Orden enviada a Claude Desktop (%s).", tab_label)
    return True, f"Orden enviada a pestaña {tab_label}"


# ─────────────────────────────────────────────────────────────────────────────
#  Telegram — cliente HTTP sin dependencias externas
# ─────────────────────────────────────────────────────────────────────────────

def _tg_post(method: str, payload: dict, timeout: int = 25) -> dict:
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{TELEGRAM_API}/{method}",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout, context=_SSL) as r:
        result = json.loads(r.read().decode("utf-8"))
    if not result.get("ok"):
        raise RuntimeError(result.get("description", "Error Telegram"))
    return result


def send_message(text: str) -> None:
    try:
        _tg_post("sendMessage", {
            "chat_id": str(TELEGRAM_USER_ID),
            "text": text,
        })
    except Exception as exc:
        log.error("Error enviando mensaje Telegram: %s", exc)


def send_photo(image_bytes: bytes, caption: str = "") -> None:
    boundary = f"insp{uuid.uuid4().hex}"
    body = bytearray()

    def field(name: str, value: str) -> None:
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body.extend(value.encode("utf-8"))
        body.extend(b"\r\n")

    field("chat_id", str(TELEGRAM_USER_ID))
    if caption:
        field("caption", caption[:1024])
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(b'Content-Disposition: form-data; name="photo"; filename="captura.png"\r\n')
    body.extend(b"Content-Type: image/png\r\n\r\n")
    body.extend(image_bytes)
    body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())

    req = urllib.request.Request(
        f"{TELEGRAM_API}/sendPhoto",
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60, context=_SSL) as r:
            json.loads(r.read())
    except Exception as exc:
        log.error("Error enviando foto: %s", exc)
        send_message(f"No pude enviar la captura: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
#  Estado del monitor
# ─────────────────────────────────────────────────────────────────────────────
_lock            = threading.Lock()
_monitor_active  = False
_monitor_thread: Optional[threading.Thread] = None
_last_status     = "OK"
_last_provider   = ""
_shutdown_evt    = threading.Event()
_resume_evt      = threading.Event()
_resume_evt.set()
_order_active    = False
_order_thread: Optional[threading.Thread] = None
_order_cancel_evt = threading.Event()
_google_active   = False
_google_thread: Optional[threading.Thread] = None
_google_cancel_evt = threading.Event()
_codex_active    = False
_codex_thread: Optional[threading.Thread] = None
_codex_cancel_evt = threading.Event()
_anthropic_cooldown_until = 0.0
_anthropic_cooldown_reason = ""


def _recover_stale_task_flags() -> None:
    global _order_active, _google_active, _codex_active
    with _lock:
        if _order_active and (_order_thread is None or not _order_thread.is_alive()):
            log.warning("Recuperando flag colgada de /orden.")
            _order_active = False
            _order_cancel_evt.set()
        if _google_active and (_google_thread is None or not _google_thread.is_alive()):
            log.warning("Recuperando flag colgada de /gorden.")
            _google_active = False
            _google_cancel_evt.set()
        if _codex_active and (_codex_thread is None or not _codex_thread.is_alive()):
            log.warning("Recuperando flag colgada de /codex.")
            _codex_active = False
            _codex_cancel_evt.set()


def _wait_interval(seconds: float) -> bool:
    """Espera N segundos interrumpible. Devuelve True si debe parar."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if _shutdown_evt.is_set():
            return True
        _shutdown_evt.wait(timeout=min(0.5, deadline - time.monotonic()))
    return _shutdown_evt.is_set()


def _wait_resume() -> bool:
    """Bloquea hasta /continuar o /parar. Devuelve True si debe parar."""
    while not _resume_evt.is_set():
        if _shutdown_evt.is_set():
            return True
        _shutdown_evt.wait(timeout=0.5)
    return _shutdown_evt.is_set()


# ─────────────────────────────────────────────────────────────────────────────
#  Hilo de monitorización
# ─────────────────────────────────────────────────────────────────────────────
def _monitor_loop() -> None:
    global _monitor_active, _last_status, _last_provider

    with _lock:
        _last_status = "OK"

    cycle = 0
    log.info("Monitor iniciado. Intervalo=%ds", MONITOR_INTERVAL)

    while not _shutdown_evt.is_set():

        # Esperar si estamos pausados por AVISO
        if _wait_resume():
            break

        cycle += 1
        ts = datetime.now().strftime("%H:%M:%S")

        img = capture_screen(full_res=False)
        if img is None:
            log.warning("[%s] Sin captura. Reintentando en %ds.", ts, MONITOR_INTERVAL)
            if _wait_interval(MONITOR_INTERVAL):
                break
            continue

        status, provider = analyze_screen(img)
        log.info("Ciclo %d [%s] -> %s (via %s)", cycle, ts, status, provider)

        with _lock:
            prev           = _last_status
            _last_status   = status
            _last_provider = provider

        if status != prev:
            if status == "FIN":
                send_message(
                    f"Tarea finalizada `[{ts}]`\n\n"
                    f"El proceso ha terminado. Vigilancia detenida.\n"
                    f"_Detectado via {provider}_"
                )
                send_photo(img, caption=f"Captura final ({ts})")
                with _lock:
                    _monitor_active = False
                log.info("FIN detectado. Monitor saliendo.")
                return

            elif status == "AVISO":
                send_message(
                    f"Atencion requerida `[{ts}]`\n\n"
                    f"He detectado un obstaculo (captcha, login, error...).\n"
                    f"Intervene en el ordenador y luego manda */continuar*.\n"
                    f"_Detectado via {provider}_"
                )
                send_photo(img, caption=f"Captura del aviso ({ts})")
                _resume_evt.clear()
                if _wait_resume():
                    break
                with _lock:
                    _last_status = "OK"
                send_message("Reanudando vigilancia...")
                continue   # captura inmediata al reanudar

        if _wait_interval(MONITOR_INTERVAL):
            break

    with _lock:
        _monitor_active = False
    log.info("Monitor detenido.")


def _start_monitor() -> None:
    global _monitor_active, _monitor_thread
    with _lock:
        if _monitor_active:
            send_message("La vigilancia ya esta activa.")
            return
        _monitor_active = True
    _shutdown_evt.clear()
    _resume_evt.set()
    _monitor_thread = threading.Thread(target=_monitor_loop, daemon=True, name="monitor")
    _monitor_thread.start()
    send_message(
        f"Vigilancia iniciada\n\n"
        f"Analizare la pantalla cada {MONITOR_INTERVAL}s.\n"
        f"Te aviso si la tarea termina o necesita ayuda."
    )


def _stop_monitor() -> None:
    global _monitor_active
    _shutdown_evt.set()
    _resume_evt.set()
    with _lock:
        _monitor_active = False


# ─────────────────────────────────────────────────────────────────────────────
#  Comandos Telegram
# ─────────────────────────────────────────────────────────────────────────────
HELP_TEXT = (
    "Inspector 0.1\n\n"
    "Comandos:\n"
    "  /orden `<texto>` - ejecuta la orden con Claude Computer Use\n"
    "  /gorden `<texto>` - ejecuta la orden con Gemini + raton/teclado\n"
    "  /codex `<texto>` - envia una peticion al panel Codex y vigila hasta terminar\n"
    "  /cancelar - intenta cancelar /orden, /gorden o /codex en curso\n"
    "  /monitorizar - inicia vigilancia sin enviar orden\n"
    "  /parar - detiene la vigilancia\n"
    "  /estado - captura + analisis inmediato\n"
    "  /captura - foto de pantalla\n"
    "  /continuar - reanuda tras un AVISO\n"
    "  /test - prueba vision y Anthropic\n"
    "  /info - estado del sistema\n\n"
    f"Texto sin comando: se interpreta por defecto como {TELEGRAM_DEFAULT_TEXT_COMMAND} <texto>\n"
)


def _cmd_info() -> None:
    _recover_stale_task_flags()
    with _lock:
        active   = _monitor_active
        status   = _last_status
        provider = _last_provider
        order_active = _order_active
        google_active = _google_active
        codex_active = _codex_active
    anthropic_cooldown = _anthropic_limit_message() or "No"

    lm_models  = _lmstudio_models()
    lm_status  = lm_models[0] if lm_models else "sin modelos / apagado"

    lines = [
        "Estado del Inspector 0.1\n",
        f"Gemini:      {'OK' if GEMINI_API_KEY else 'sin clave'} ({GEMINI_VISION_MODEL})",
        f"Groq:        {'OK' if GROQ_API_KEY else 'sin clave'} ({GROQ_VISION_MODEL})",
        f"OpenRouter:  {'OK' if OPENROUTER_API_KEY else 'sin clave'} ({OPENROUTER_VISION_MODEL})",
        f"LM Studio:   {lm_status}",
        f"Anthropic:   {'OK' if ANTHROPIC_API_KEY else 'sin clave'} ({ANTHROPIC_COMPUTER_MODEL})",
        f"Google desk: {_google_desktop_ready_reason()} ({GOOGLE_DESKTOP_MODEL})",
        f"Texto libre: {TELEGRAM_DEFAULT_TEXT_COMMAND}",
        f"Claude cooldown: {anthropic_cooldown}",
        f"Captura:     {'OK' if HAS_PIL else 'sin Pillow'}",
        f"Automatiz.:  {'OK' if HAS_GUI else 'sin PyAutoGUI'}",
        f"",
        f"Vigilancia:  {'Activa' if active else 'Inactiva'}",
        f"Orden activa: {'Si' if order_active else 'No'}",
        f"Google activo: {'Si' if google_active else 'No'}",
        f"Codex activo: {'Si' if codex_active else 'No'}",
        f"Ultimo estado: {status} (via {provider or '-'})",
        f"Intervalo:   {MONITOR_INTERVAL}s",
        f"Codex check: {CODEX_MONITOR_INTERVAL}s",
    ]
    send_message("\n".join(lines))


def _cmd_test() -> None:
    """Prueba cada proveedor con la pantalla actual y reporta resultados."""
    send_message("Probando proveedores de vision y Anthropic...")
    img = capture_screen(full_res=False)
    if not img:
        send_message("No se pudo capturar la pantalla.")
        return

    results = []
    for name, fn in _VISION_PROVIDERS:
        try:
            t0 = time.perf_counter()
            result = fn(img, VISION_PROMPT, VISION_SYSTEM, 10)
            elapsed = time.perf_counter() - t0
            results.append(f"OK {name}: '{result[:30]}' ({elapsed:.1f}s)")
            log.info("Test [%s]: %r (%.1fs)", name, result, elapsed)
        except Exception as exc:
            results.append(f"FALLO {name}: {str(exc)[:60]}")
            log.warning("Test [%s] fallo: %s", name, exc)

    try:
        display_w, display_h = _screen_size()
        scale = _anthropic_scale_factor(display_w, display_h)
        tools = [{
            "type": _computer_tool_type(),
            "name": "computer",
            "display_width_px": max(1, int(display_w * scale)),
            "display_height_px": max(1, int(display_h * scale)),
        }]
        resp = _anthropic_message(
            [{"role": "user", "content": "Usa la herramienta computer para hacer una captura y luego responde OK."}],
            tools,
            system=ANTHROPIC_COMPUTER_SYSTEM,
        )
        results.append(f"OK Anthropic: stop_reason={resp.get('stop_reason', '-')}")
    except Exception as exc:
        results.append(f"FALLO Anthropic: {str(exc)[:80]}")
        log.warning("Test [Anthropic] fallo: %s", exc)

    send_message("Resultados de proveedores:\n\n" + "\n".join(results))


def _wait_cancelable(seconds: float, cancel_evt: threading.Event | None = None) -> bool:
    """Espera cancelable y devuelve True si se pidio cancelar."""
    cancel_evt = cancel_evt or threading.Event()
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if cancel_evt.is_set():
            return True
        time.sleep(min(0.5, max(0.0, deadline - time.monotonic())))
    return cancel_evt.is_set()


def _launch_codex_request(request: str) -> tuple[bool, str]:
    """Envio determinista de una peticion al panel Codex en VS Code."""
    return send_to_codex(request)


def _monitor_codex_until_done(cancel_evt: threading.Event | None = None) -> tuple[str, str, Optional[bytes]]:
    """
    Vigila el panel de Codex hasta detectar TERMINADO, BLOQUEADO o cancelacion.
    Devuelve (estado, detalle, captura_final).
    """
    cancel_evt = cancel_evt or _codex_cancel_evt
    prev_region: Optional[bytes] = None
    stable_cycles = 0
    cycle = 0

    while True:
        if cancel_evt.is_set():
            return "CANCELADO", "Operacion cancelada por el usuario.", None

        cycle += 1
        panel = capture_codex_panel(full_panel=True)
        compare_region = capture_codex_body()
        if panel is None or compare_region is None:
            return "BLOQUEADO", "No pude capturar el panel de Codex en VS Code.", None

        if prev_region is None:
            prev_region = compare_region
            log.info("Codex monitor ciclo %d: baseline establecida", cycle)
        else:
            try:
                actividad, motivo_actividad = codex_activity_status(panel)
                log.info("Codex monitor ciclo %d: actividad=%s (%s)", cycle, actividad, motivo_actividad)
                if actividad == "TRABAJANDO":
                    stable_cycles = 0
                    prev_region = compare_region
                    if _wait_cancelable(CODEX_MONITOR_INTERVAL, cancel_evt):
                        return "CANCELADO", "Operacion cancelada por el usuario.", None
                    continue
            except Exception as exc:
                log.warning("No pude evaluar actividad de Codex: %s", exc)
            change_pct = _image_change_pct(prev_region, compare_region)
            prev_region = compare_region
            if change_pct <= CODEX_STABLE_THRESHOLD_PCT:
                stable_cycles += 1
            else:
                stable_cycles = 0
            log.info(
                "Codex monitor ciclo %d: cambio=%.4f%% estables=%d/%d",
                cycle, change_pct, stable_cycles, CODEX_STABLE_CYCLES
            )

            if stable_cycles >= CODEX_STABLE_CYCLES:
                estado, motivo = codex_panel_status(panel)
                log.info("Codex monitor ciclo %d: Gemini => %s (%s)", cycle, estado, motivo)
                ready, ready_motivo = False, ""
                try:
                    ready, ready_motivo = codex_ready_for_followup(panel)
                    log.info("Codex monitor ciclo %d: ready=%s (%s)", cycle, ready, ready_motivo)
                except Exception as exc:
                    log.warning("No pude evaluar si Codex ya estaba listo: %s", exc)
                if estado == "TERMINADO" or ready:
                    if _wait_cancelable(CODEX_CONFIRM_FIN_DELAY, cancel_evt):
                        return "CANCELADO", "Operacion cancelada por el usuario.", None
                    confirm_panel = capture_codex_panel(full_panel=True)
                    confirm_input = capture_codex_input()
                    confirm_body = capture_codex_body()
                    if confirm_panel is None or confirm_body is None:
                        return "BLOQUEADO", "No pude confirmar el estado final de Codex.", panel
                    confirm_change = _image_change_pct(compare_region, confirm_body)
                    log.info("Codex confirmacion final cambio=%.4f%%", confirm_change)
                    if confirm_change <= CODEX_STABLE_THRESHOLD_PCT:
                        estado2, motivo2 = codex_panel_status(confirm_panel)
                        log.info("Codex confirmacion Gemini => %s (%s)", estado2, motivo2)
                        ready2, ready_motivo2 = False, ""
                        try:
                            ready2, ready_motivo2 = codex_ready_for_followup(confirm_panel, confirm_input)
                            log.info("Codex confirmacion ready => %s (%s)", ready2, ready_motivo2)
                        except Exception as exc:
                            log.warning("No pude reevaluar si Codex ya estaba listo: %s", exc)
                        if estado2 == "TERMINADO" or ready2:
                            try:
                                resumen = codex_panel_summary(confirm_body or confirm_panel)
                            except Exception as exc:
                                resumen = f"Codex parece terminado, pero no pude resumir la salida: {exc}"
                            if ready2 and "listo para una nueva pregunta" not in resumen.lower():
                                resumen = resumen.rstrip() + "\n\nCodex ya esta listo para una nueva pregunta."
                            return "TERMINADO", resumen, confirm_panel
                    stable_cycles = 0
                    prev_region = confirm_body
                    continue
                if estado == "BLOQUEADO":
                    return "BLOQUEADO", motivo or "Codex necesita interaccion humana.", panel
                stable_cycles = 0

        if _wait_cancelable(CODEX_MONITOR_INTERVAL, cancel_evt):
            return "CANCELADO", "Operacion cancelada por el usuario.", None


def _cmd_order(order: str) -> None:
    global _order_active

    with _lock:
        if _order_active:
            send_message("Ya hay una orden en ejecucion con Claude Computer Use.")
            return
        _order_active = True
    _order_cancel_evt.clear()

    send_message(
        "Orden recibida. Ejecutando con Claude Computer Use...\n\n"
        f"{order[:500]}"
    )

    try:
        _ensure_anthropic_available()
        ok, summary = run_claude_computer_use(order, cancel_evt=_order_cancel_evt)
        if ok:
            send_message("Claude ha terminado la orden.\n\n" + summary[:3500])
            final_img = capture_screen(full_res=False)
            if final_img:
                send_photo(final_img, caption="Captura final de Claude Computer Use")
        else:
            send_message("La orden no termino correctamente.\n\n" + summary[:3500])
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        if _is_anthropic_limit_error(exc.code, detail):
            _set_anthropic_cooldown(detail or f"HTTP {exc.code}")
        msg = f"Anthropic devolvio HTTP {exc.code}."
        if detail:
            msg += f"\n\n{detail[:3000]}"
        send_message(msg)
    except Exception as exc:
        send_message(f"Fallo ejecutando Claude Computer Use:\n\n{str(exc)[:3500]}")
    finally:
        _order_cancel_evt.set()
        with _lock:
            _order_active = False


def _cmd_gorden(order: str) -> None:
    global _google_active

    with _lock:
        if _google_active or _codex_active:
            send_message("Ya hay una peticion de Codex en curso.")
            return
        _google_active = True
    _google_cancel_evt.clear()

    send_message(
        "Peticion /gorden recibida. Voy a escribirla en la caja Ask for... de Codex y luego vigilar el panel.\n\n"
        f"{order[:500]}"
    )

    try:
        ok, summary = _launch_codex_request(order)
        if not ok:
            send_message("No pude enviar la peticion a Codex.\n\n" + summary[:3500])
            return
        send_message("Peticion enviada a Codex. Empiezo la vigilancia del panel.")
        estado, detalle, final_panel = _monitor_codex_until_done(_google_cancel_evt)
        if estado == "TERMINADO":
            send_message("Codex ha terminado.\n\n" + detalle[:3500])
            if final_panel:
                send_photo(final_panel, caption="Panel final de Codex")
        elif estado == "BLOQUEADO":
            send_message(
                "Codex necesita tu interaccion.\n\n"
                + detalle[:3500]
                + "\n\nCuando quieras que siga, me lo dices por Telegram."
            )
            if final_panel:
                send_photo(final_panel, caption="Codex bloqueado")
        else:
            send_message(detalle[:3500])
    except Exception as exc:
        send_message(f"Fallo en /gorden:\n\n{str(exc)[:3500]}")
    finally:
        _google_cancel_evt.set()
        with _lock:
            _google_active = False


def _cmd_codex(request: str) -> None:
    global _codex_active

    with _lock:
        if _codex_active or _google_active:
            send_message("Ya hay una peticion /codex en curso.")
            return
        _codex_active = True
    _codex_cancel_evt.clear()

    send_message(
        "Peticion /codex recibida. Voy a enviarla a VS Code y luego vigilare el panel cada "
        f"{CODEX_MONITOR_INTERVAL}s.\n\n{request[:500]}"
    )

    try:
        ok, summary = _launch_codex_request(request)
        if not ok:
            send_message("No pude lanzar la peticion en Codex.\n\n" + summary[:3500])
            return

        send_message("Peticion enviada a Codex. Empiezo la vigilancia del panel.")
        estado, detalle, final_panel = _monitor_codex_until_done(_codex_cancel_evt)
        if estado == "TERMINADO":
            send_message("Codex ha terminado y ya esta listo para una nueva pregunta.\n\n" + detalle[:3500])
            if final_panel:
                send_photo(final_panel, caption="Panel final de Codex")
        elif estado == "BLOQUEADO":
            send_message(
                "Codex necesita tu interaccion.\n\n"
                + detalle[:3500]
                + "\n\nCuando quieras que siga, me lo dices por Telegram."
            )
            if final_panel:
                send_photo(final_panel, caption="Codex bloqueado")
        else:
            send_message(detalle[:3500])
    except Exception as exc:
        send_message(f"Fallo en /codex:\n\n{str(exc)[:3500]}")
    finally:
        _codex_cancel_evt.set()
        with _lock:
            _codex_active = False


def handle_command(text: str) -> None:
    global _order_thread, _google_thread, _codex_thread

    _recover_stale_task_flags()

    parts   = text.strip().split(maxsplit=1)
    cmd     = parts[0].lower().split("@")[0]
    args    = parts[1].strip() if len(parts) > 1 else ""
    log.info("CMD: %s  args=%r", cmd, args[:80])

    if cmd in ("/start", "/ayuda", "/help"):
        send_message(HELP_TEXT)

    elif cmd == "/info":
        _cmd_info()

    elif cmd == "/test":
        threading.Thread(target=_cmd_test, daemon=True).start()

    elif cmd == "/orden":
        if not args:
            send_message(
                "Uso: /orden <texto>\n"
                "Ejemplo:\n"
                "/orden Busca precios de alquiler en Madrid y guardalos en Excel"
            )
            return
        _order_thread = threading.Thread(target=_cmd_order, args=(args,), daemon=True)
        _order_thread.start()

    elif cmd == "/gorden":
        if not args:
            send_message(
                "Uso: /gorden <texto>\n"
                "Ejemplo:\n"
                "/gorden Abre el Bloc de notas y escribe hola"
            )
            return
        _google_thread = threading.Thread(target=_cmd_gorden, args=(args,), daemon=True)
        _google_thread.start()

    elif cmd == "/codex":
        if not args:
            send_message(
                "Uso: /codex <texto>\n"
                "Ejemplo:\n"
                "/codex Dime que scripts, ordenes de terminal, APIs MCP y apps web podemos usar en este repositorio"
            )
            return
        _codex_thread = threading.Thread(target=_cmd_codex, args=(args,), daemon=True)
        _codex_thread.start()

    elif cmd == "/cancelar":
        cancelled = False
        with _lock:
            if _order_active:
                _order_cancel_evt.set()
                cancelled = True
            if _google_active:
                _google_cancel_evt.set()
                cancelled = True
            if _codex_active:
                _codex_cancel_evt.set()
                cancelled = True
        if cancelled:
            send_message("He marcado la operacion en curso para cancelacion.")
        else:
            send_message("No habia ninguna operacion /orden, /gorden o /codex en curso.")

    elif cmd == "/monitorizar":
        _start_monitor()

    elif cmd == "/parar":
        with _lock:
            active = _monitor_active
            order_active = _order_active
            codex_active = _codex_active
        if active:
            _stop_monitor()
            send_message("Vigilancia detenida.")
        elif order_active:
            _order_cancel_evt.set()
            send_message("He marcado la orden de Claude para cancelacion.")
        elif codex_active:
            _codex_cancel_evt.set()
            send_message("He marcado la operacion /codex para cancelacion.")
        else:
            send_message("No habia ninguna vigilancia activa.")

    elif cmd == "/estado":
        send_message("Capturando y analizando...")
        img = capture_screen(full_res=False)
        if not img:
            send_message("No se pudo capturar la pantalla.")
            return
        status, provider = analyze_screen(img)
        ts = datetime.now().strftime("%H:%M:%S")
        send_photo(img, caption=f"Estado: {status} via {provider} ({ts})")

    elif cmd == "/captura":
        img = capture_screen(full_res=False)
        if not img:
            send_message("No se pudo capturar la pantalla.")
            return
        ts = datetime.now().strftime("%H:%M:%S")
        send_photo(img, caption=f"Captura manual ({ts})")

    elif cmd == "/continuar":
        with _lock:
            active = _monitor_active
        if not active:
            send_message("La vigilancia no estaba activa. Usa /monitorizar.")
            return
        if _resume_evt.is_set():
            send_message("La vigilancia ya estaba corriendo (no estaba pausada).")
        else:
            _resume_evt.set()
            send_message("Reanudando vigilancia...")

    else:
        send_message(f"Comando desconocido: {cmd}\nUsa /start.")


def telegram_poll_loop() -> None:
    offset  = 0
    backoff = 1.0
    connected = False
    log.info("Telegram polling iniciado.")

    while True:
        try:
            data = _tg_post(
                "getUpdates",
                {"timeout": "30", "offset": str(offset),
                 "allowed_updates": json.dumps(["message"])},
                timeout=45,
            )
            if not connected:
                log.info("Telegram conectado. Esperando mensajes...")
                connected = True
            backoff = 1.0

            for update in data.get("result", []):
                offset  = update["update_id"] + 1
                msg     = update.get("message", {})
                chat_id = msg.get("chat", {}).get("id")
                if chat_id != TELEGRAM_USER_ID:
                    continue
                text = (msg.get("text") or "").strip()
                if not text:
                    continue
                if not text.startswith("/"):
                    default_cmd = TELEGRAM_DEFAULT_TEXT_COMMAND if TELEGRAM_DEFAULT_TEXT_COMMAND.startswith("/") else f"/{TELEGRAM_DEFAULT_TEXT_COMMAND}"
                    text = f"{default_cmd} {text}".strip()
                    log.info("Texto libre de Telegram -> %s", text[:120])
                threading.Thread(
                    target=handle_command, args=(text,), daemon=True
                ).start()

        except KeyboardInterrupt:
            raise
        except Exception as exc:
            connected = False
            wait = int(min(30, backoff))
            log.error("Error polling Telegram: %s | reintentando en %ds", exc, wait)
            time.sleep(wait)
            backoff = min(30.0, backoff * 2.0)


# ─────────────────────────────────────────────────────────────────────────────
#  Arranque
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    print("=" * 60)
    print("  Inspector 0.1")
    print("=" * 60)

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_USER_ID:
        log.error("Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_ALLOWED_USER_ID en el .env")
        sys.exit(1)

    log.info("Telegram user   : %d", TELEGRAM_USER_ID)
    log.info("Texto libre     : %s", TELEGRAM_DEFAULT_TEXT_COMMAND)
    log.info("LM Studio       : %s", LMSTUDIO_BASE_URL)
    log.info("Intervalo       : %ds", MONITOR_INTERVAL)
    log.info("Gemini          : %s", "configurado" if GEMINI_API_KEY else "sin clave")
    log.info("Groq            : %s", "configurado" if GROQ_API_KEY else "sin clave")
    log.info("OpenRouter      : %s", "configurado" if OPENROUTER_API_KEY else "sin clave")
    log.info("Anthropic       : %s", "configurado" if ANTHROPIC_API_KEY else "sin clave")
    log.info("Google desktop  : %s", _google_desktop_ready_reason())
    log.info("LM Studio       : %s", (_lmstudio_models() or ["no disponible"])[0])
    log.info("Pillow          : %s", "OK" if HAS_PIL else "NO instalado")
    log.info("PyAutoGUI       : %s", "OK" if HAS_GUI else "NO instalado")
    print("=" * 60)

    # Mensaje de bienvenida
    lm = (_lmstudio_models() or ["no disponible"])[0]
    send_message(
        f"Inspector 0.1 iniciado\n\n"
        f"Gemini: {'configurado' if GEMINI_API_KEY else 'sin clave'}\n"
        f"Groq: {'configurado' if GROQ_API_KEY else 'sin clave'}\n"
        f"OpenRouter: {'configurado' if OPENROUTER_API_KEY else 'sin clave'}\n"
        f"Anthropic: {'configurado' if ANTHROPIC_API_KEY else 'sin clave'} ({ANTHROPIC_COMPUTER_MODEL})\n"
        f"Google desktop: {_google_desktop_ready_reason()} ({GOOGLE_DESKTOP_MODEL})\n"
        f"LM Studio: {lm}\n\n"
        f"Usa /test para probar todos los proveedores.\n"
        f"Usa /start para ver los comandos."
    )

    try:
        telegram_poll_loop()
    except KeyboardInterrupt:
        log.info("Cerrando Inspector 0.1...")
        _stop_monitor()
        send_message("Inspector 0.1 detenido.")


if __name__ == "__main__":
    main()
