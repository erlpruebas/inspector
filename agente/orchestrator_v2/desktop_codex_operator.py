from __future__ import annotations

import argparse
import json
import os
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from orchestrator_v2.desktop_calibration_store import (
    DEFAULT_CALIBRATION_FILE,
    DEFAULT_CLICK_PROFILE_FILE,
    machine_calibration_file,
    machine_click_profile_file,
    machine_name,
    tracked_machine_calibration_file,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = PACKAGE_ROOT / "orchestrator_v2" / "runtime" / "desktop_codex_operator"
DEFAULT_WINDOW_RE = r"^Codex$"
CALIBRATION_FILE = machine_calibration_file()
TRACKED_CALIBRATION_FILE = tracked_machine_calibration_file()
CLICK_PROFILE_FILE = machine_click_profile_file()

DEFAULT_CLICK_PROFILE = {
    "new_chat": {"x": 71, "y": 47, "label": "Nueva conversacion"},
    "initial_input": {"x": 782, "y": 491, "label": "Input conversacion nueva"},
    "initial_send": {"x": 1100, "y": 516, "label": "Enviar conversacion nueva"},
    "initial_stop_no_browser": {"x": 1373, "y": 988, "label": "Stop sin navegador"},
    "browser_toggle": {"x": 1900, "y": 50, "label": "Abrir/cerrar navegador"},
    "browser_input": {"x": 532, "y": 955, "label": "Input con navegador"},
    "browser_send_stop": {"x": 770, "y": 989, "label": "Enviar/stop con navegador"},
}


@dataclass(frozen=True)
class DesktopCodexResult:
    ok: bool
    status: str
    prompt_path: Path
    run_dir: Path
    screenshot_path: Path | None = None
    result_path: Path | None = None
    extracted_tokens_path: Path | None = None
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key, value in list(data.items()):
            if isinstance(value, Path):
                data[key] = str(value)
        return data


def build_botfather_prompt(
    bot_names: list[str],
    username_prefix: str,
    lab_label: str = "Inspector Lab",
) -> str:
    desired = []
    for index, name in enumerate(bot_names, start=1):
        username = sanitize_bot_username(f"{username_prefix}_{index}_bot")
        desired.append({"display_name": name.strip() or f"{lab_label} Bot {index}", "username": username})

    bots_json = json.dumps(desired, indent=2, ensure_ascii=False)
    return f"""
Necesito crear 4 bots de Telegram para el laboratorio ciego de Inspector usando BotFather.

Objetivo:
- Abrir Telegram Desktop o Telegram Web si hace falta.
- Ir a BotFather.
- Crear estos bots exactamente:

{bots_json}

Procedimiento esperado:
- Usa /newbot para cada bot.
- Si algun username no esta disponible, prueba una variante cercana manteniendo el prefijo y el numero.
- No publiques ni pegues los tokens en webs externas.
- Cuando termines, deja un resumen final en una tabla con:
  - slot
  - display_name
  - username final
  - token
  - si quedo creado o no
  - incidencia si hubo alguna

Resumen final obligatorio:
Al terminar escribe una seccion llamada "RESULTADO FINAL PARA INSPECTOR" con:
- CREACION_COMPLETADA: si/no/parcial
- BOTS_CREADOS: numero
- TOKENS: lista de variables LAB_BOT_1_TOKEN, LAB_BOT_2_TOKEN, LAB_BOT_3_TOKEN, LAB_BOT_4_TOKEN
- SIGUIENTE_PASO: que debo pegar despues en el panel web de Inspector

Si aparece login, 2FA, captcha, confirmacion de seguridad o una pantalla con datos sensibles, detente y pideme intervencion humana.
""".strip()


def sanitize_bot_username(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", value)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned.lower().endswith("bot"):
        cleaned += "_bot"
    if len(cleaned) < 5:
        cleaned = f"inspector_{cleaned}"
    return cleaned[:32]


def build_lab_bot_names(label: str = "Inspector Lab") -> list[str]:
    return [
        f"{label} Usuario 1",
        f"{label} Usuario 2",
        f"{label} Usuario 3",
        f"{label} Usuario 4",
    ]


def run_desktop_codex_operator(
    prompt: str,
    *,
    send: bool = False,
    new_chat: bool = True,
    wait_seconds: int = 1800,
    window_re: str = DEFAULT_WINDOW_RE,
    debug_draft: bool = False,
    pause_after_paste: bool = False,
    resume_send: bool = False,
) -> DesktopCodexResult:
    run_dir = RUNTIME_ROOT / datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = run_dir / "prompt.md"
    prompt_path.write_text(prompt, encoding="utf-8")
    if not send and not resume_send:
        result = DesktopCodexResult(ok=True, status="dry_run_prompt_ready", prompt_path=prompt_path, run_dir=run_dir)
        (run_dir / "result.json").write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return result

    try:
        _send_prompt_to_codex_desktop(
            prompt,
            new_chat=new_chat,
            window_re=window_re,
            debug_draft=debug_draft,
            pause_after_paste=pause_after_paste,
            resume_send=resume_send,
            run_dir=run_dir,
        )
        if pause_after_paste:
            result = DesktopCodexResult(
                ok=True,
                status="draft_ready_waiting_review",
                prompt_path=prompt_path,
                run_dir=run_dir,
                screenshot_path=run_dir / "draft_screen.png" if (run_dir / "draft_screen.png").exists() else None,
            )
            (run_dir / "result.json").write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
            return result
        screenshot_path = _wait_and_capture(run_dir, wait_seconds=wait_seconds, new_chat=new_chat)
        result_path = run_dir / "resultado.md"
        result_path.write_text(
            "Captura final guardada. Revisa la pantalla o procesa la imagen con OCR/vision para extraer tokens.\n"
            f"Screenshot: {screenshot_path}\n",
            encoding="utf-8",
        )
        extracted_path = _extract_tokens_with_gemini(screenshot_path, run_dir)
        result = DesktopCodexResult(
            ok=True,
            status="sent_and_captured",
            prompt_path=prompt_path,
            run_dir=run_dir,
            screenshot_path=screenshot_path,
            result_path=result_path,
            extracted_tokens_path=extracted_path,
        )
    except Exception as exc:
        result = DesktopCodexResult(
            ok=False,
            status="failed",
            prompt_path=prompt_path,
            run_dir=run_dir,
            error=f"{type(exc).__name__}: {exc}",
        )
    (run_dir / "result.json").write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def capture_desktop_screenshot(path: Path) -> Path:
    image = _grab_screen()
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    return path


def _send_prompt_to_codex_desktop(
    prompt: str,
    *,
    new_chat: bool,
    window_re: str,
    debug_draft: bool = False,
    pause_after_paste: bool = False,
    resume_send: bool = False,
    run_dir: Path | None = None,
) -> None:
    try:
        import pyautogui
    except ImportError as exc:
        raise RuntimeError("pyautogui no esta instalado") from exc

    window = _find_and_activate_window(window_re)
    if debug_draft and run_dir is not None:
        _grab_screen().save(run_dir / "01_focus_screen.png")
    
    _ensure_panels_open()
    
    if new_chat and not resume_send:
        _click_new_chat(window)
        time.sleep(0.8)
        if debug_draft and run_dir is not None:
            _grab_screen().save(run_dir / "02_after_new_chat.png")
    if not resume_send:
        x, y = _input_coordinates(window, new_chat=new_chat)
        pasted = False
        for attempt, point in enumerate(_paste_points(x, y), start=1):
            _set_clipboard(prompt)
            time.sleep(0.15)
            pyautogui.click(*point)
            time.sleep(0.25)
            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.08)
            pyautogui.press("backspace")
            time.sleep(0.08)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.5)
            if debug_draft and run_dir is not None:
                _grab_screen().save(run_dir / f"03_after_paste_attempt_{attempt}.png")
            if _verify_pasted_prompt(prompt):
                pasted = True
                break
        if debug_draft and run_dir is not None:
            _grab_screen().save(run_dir / "03_after_paste_raw.png")
        if not pasted:
            draft_path = run_dir / "draft_screen.png" if run_dir is not None else None
            if draft_path is not None:
                _grab_screen().save(draft_path)
            raise RuntimeError("No pude confirmar que el texto quedo pegado en el campo de Codex.")
        if debug_draft and run_dir is not None:
            draft_path = run_dir / "draft_screen.png"
            _grab_screen().save(draft_path)
            time.sleep(0.5)
        if pause_after_paste:
            return
    if not _click_send_button(window, new_chat=new_chat):
        pyautogui.press("enter")


def _find_and_activate_window(window_re: str):
    pattern = re.compile(window_re, re.IGNORECASE)
    uia_window = _find_uia_window(pattern)
    if uia_window is not None:
        _restore_and_focus_window(uia_window)
        time.sleep(0.6)
        return uia_window
    gui_window = _find_pyautogui_window(pattern)
    if gui_window is not None:
        _restore_and_focus_pyautogui_window(gui_window)
        time.sleep(0.6)
        return gui_window
    visible = "; ".join(list_window_titles(limit=20))
    raise RuntimeError(f"No encontre una ventana que coincida con {window_re!r}. Ventanas visibles: {visible}")


def _find_uia_window(pattern: re.Pattern[str]):
    try:
        from pywinauto import Desktop
    except ImportError:
        return None
    try:
        windows = [win for win in Desktop(backend="uia").windows() if pattern.search(win.window_text() or "")]
    except Exception:
        return None
    if not windows:
        return None
    return max(windows, key=lambda item: item.rectangle().width() * item.rectangle().height())


def _find_pyautogui_window(pattern: re.Pattern[str]):
    try:
        import pyautogui
    except ImportError:
        return None
    try:
        windows = [win for win in pyautogui.getAllWindows() if pattern.search(getattr(win, "title", "") or "")]
    except Exception:
        return None
    if not windows:
        return None
    return max(windows, key=lambda item: int(getattr(item, "width", 0)) * int(getattr(item, "height", 0)))


def _restore_and_focus_window(window) -> None:
    try:
        wrapper = window.wrapper_object()
    except Exception:
        wrapper = window
    try:
        if hasattr(wrapper, "is_minimized") and wrapper.is_minimized():
            wrapper.restore()
            time.sleep(0.4)
    except Exception:
        pass
    try:
        wrapper.set_focus()
        return
    except Exception:
        pass
    try:
        wrapper.move_mouse_input()
        wrapper.click_input()
        time.sleep(0.2)
        wrapper.set_focus()
        return
    except Exception:
        pass
    try:
        window.set_focus()
    except Exception as exc:
        raise RuntimeError(f"No pude poner foco en la ventana Codex: {exc}") from exc


def _restore_and_focus_pyautogui_window(window) -> None:
    try:
        if getattr(window, "isMinimized", False):
            window.restore()
            time.sleep(0.4)
    except Exception:
        pass
    try:
        window.activate()
        return
    except Exception:
        pass
    try:
        import pyautogui

        x = int(getattr(window, "left", 0)) + max(20, int(getattr(window, "width", 200)) // 2)
        y = int(getattr(window, "top", 0)) + 16
        pyautogui.click(x, y)
    except Exception as exc:
        raise RuntimeError(f"No pude activar la ventana Codex por pyautogui: {exc}") from exc


def list_window_titles(limit: int = 50) -> list[str]:
    titles: list[str] = []
    try:
        from pywinauto import Desktop
        for win in Desktop(backend="uia").windows():
            title = (win.window_text() or "").strip()
            if title and title not in titles:
                titles.append(title)
            if len(titles) >= limit:
                break
    except Exception:
        pass
    if len(titles) < limit:
        try:
            import pyautogui

            for win in pyautogui.getAllWindows():
                title = (getattr(win, "title", "") or "").strip()
                if title and title not in titles:
                    titles.append(title)
                if len(titles) >= limit:
                    break
        except Exception:
            pass
    return titles

def _ensure_panels_open() -> None:
    import pyautogui
    import time

    def _check_and_toggle(point_name: str, toggle_name: str) -> None:
        pt_data = _calibrated_point_data(point_name)
        if not pt_data:
            return
        expected_color = pt_data.get("color")
        if not expected_color:
            return
        try:
            r, g, b = pyautogui.pixel(pt_data["x"], pt_data["y"])
            if abs(r - expected_color[0]) > 15 or abs(g - expected_color[1]) > 15 or abs(b - expected_color[2]) > 15:
                toggle = _calibrated_point(toggle_name)
                if toggle:
                    _click_point(toggle)
                    time.sleep(0.8)
        except Exception:
            pass

    _check_and_toggle("new_chat", "sidebar_toggle")
    _check_and_toggle("browser_input", "browser_toggle")


def _click_new_chat(window) -> bool:
    calibrated = _calibrated_point("new_chat")
    if calibrated:
        _click_point(calibrated)
        return True
    profiled = _profile_point("new_chat")
    if profiled:
        _click_point(profiled)
        return True
    try:
        import pyautogui
        for item in window.descendants():
            text = (item.window_text() or "").strip().casefold()
            if text in {"nuevo chat", "new chat"}:
                rect = item.rectangle()
                pyautogui.click(rect.mid_point().x, rect.mid_point().y)
                return True
    except Exception:
        return False
    return False


def _input_coordinates(window, *, new_chat: bool) -> tuple[int, int]:
    for key in ("input_box", "initial_input" if new_chat else "browser_input", "browser_input" if not new_chat else "input_box"):
        calibrated = _calibrated_point(key)
        if calibrated:
            return calibrated
        profiled = _profile_point(key)
        if profiled:
            return profiled
    env_x = os.getenv("CODEX_DESKTOP_INPUT_X", "").strip()
    env_y = os.getenv("CODEX_DESKTOP_INPUT_Y", "").strip()
    if env_x and env_y:
        return int(env_x), int(env_y)
    rect = window.rectangle()
    return rect.left + int(rect.width() * 0.46), rect.top + int(rect.height() * 0.94)


def _click_send_button(window, *, new_chat: bool) -> bool:
    candidates = [
        "send_button",
        "initial_send" if new_chat else "browser_send_stop",
        "initial_stop_no_browser" if new_chat else "browser_send_stop",
    ]
    for key in candidates:
        calibrated = _calibrated_point(key)
        if calibrated:
            _click_point(calibrated)
            return True
        profiled = _profile_point(key)
        if profiled:
            _click_point(profiled)
            return True
    return False


def _click_point(point: tuple[int, int]) -> None:
    import pyautogui

    pyautogui.click(point[0], point[1])


def _paste_points(x: int, y: int) -> list[tuple[int, int]]:
    return [
        (x, y),
        (x + 30, y),
        (x, y - 24),
        (x + 30, y - 24),
        (x, y + 18),
    ]


def _load_calibration() -> dict[str, Any]:
    for path in (CALIBRATION_FILE, TRACKED_CALIBRATION_FILE, DEFAULT_CALIBRATION_FILE):
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict):
            return data
    return {}


def _load_click_profile() -> dict[str, Any]:
    for path in (CLICK_PROFILE_FILE, DEFAULT_CLICK_PROFILE_FILE):
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict):
            return {**DEFAULT_CLICK_PROFILE, **data}
    return DEFAULT_CLICK_PROFILE


def _calibrated_point_data(name: str) -> dict | None:
    data = _load_calibration()
    point = data.get("points", {}).get(name)
    if isinstance(point, dict) and "x" in point and "y" in point:
        return point
    return None

def _calibrated_point(name: str) -> tuple[int, int] | None:
    data = _load_calibration()
    point = _point_from_payload(data, name)
    if point is not None:
        return point
    applications = data.get("applications", {})
    if isinstance(applications, dict):
        codex_app = applications.get("codex_desktop", {})
        if isinstance(codex_app, dict):
            point = _point_from_payload(codex_app, name)
            if point is not None:
                return point
    return None


def _point_from_payload(payload: dict[str, Any], name: str) -> tuple[int, int] | None:
    point = payload.get("points", {}).get(name, {})
    try:
        x = int(point["x"])
        y = int(point["y"])
    except (KeyError, TypeError, ValueError):
        return None
    return x, y


def _profile_point(name: str) -> tuple[int, int] | None:
    point = _load_click_profile().get(name, {})
    try:
        x = int(point["x"])
        y = int(point["y"])
    except (KeyError, TypeError, ValueError):
        return None
    return x, y


def _set_clipboard(text: str) -> None:
    try:
        import pyperclip

        pyperclip.copy(text)
        return
    except Exception:
        pass
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()
        return
    except Exception:
        pass
    try:
        import subprocess

        subprocess.run(["powershell", "-NoProfile", "-Command", "Set-Clipboard -Value $input"], input=text, text=True, check=True)
        return
    except Exception as exc:
        raise RuntimeError("No pude escribir en el portapapeles") from exc


def _get_clipboard() -> str:
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        try:
            value = root.clipboard_get()
        finally:
            root.destroy()
        return value
    except Exception:
        pass
    try:
        import pyperclip

        return pyperclip.paste()
    except Exception as exc:
        raise RuntimeError("No pude leer el portapapeles") from exc


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _verify_pasted_prompt(expected: str) -> bool:
    try:
        try:
            import pyautogui

            sentinel = f"__INSPECTOR_EMPTY_CLIPBOARD_{datetime.now().timestamp()}__"
            _set_clipboard(sentinel)
            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.15)
            pyautogui.hotkey("ctrl", "c")
            time.sleep(0.2)
        except Exception:
            pass
        pasted = _get_clipboard()
    except Exception:
        return False
    if pasted.startswith("__INSPECTOR_EMPTY_CLIPBOARD_"):
        return False
    expected_norm = _normalize_text(expected)
    pasted_norm = _normalize_text(pasted)
    if not expected_norm or not pasted_norm:
        return False
    if expected_norm == pasted_norm:
        return True
    return expected_norm in pasted_norm or pasted_norm in expected_norm


def _wait_and_capture(run_dir: Path, *, wait_seconds: int, new_chat: bool) -> Path:
    import pyautogui
    point_key = "initial_send" if new_chat else "browser_send_stop"
    pt_data = _calibrated_point_data(point_key)

    if pt_data and pt_data.get("color"):
        expected = pt_data["color"]
        x, y = pt_data["x"], pt_data["y"]
        deadline = time.monotonic() + wait_seconds
        
        # Esperamos a que la UI registre el click y empiece a procesar
        time.sleep(2.0)
        
        while time.monotonic() < deadline:
            try:
                r, g, b = pyautogui.pixel(x, y)
                if abs(r - expected[0]) <= 15 and abs(g - expected[1]) <= 15 and abs(b - expected[2]) <= 15:
                    time.sleep(1.5)  # Estabilidad final
                    break
            except Exception:
                pass
            time.sleep(1.0)
    else:
        # Fallback a estabilizacion de pantalla
        deadline = time.monotonic() + max(5, wait_seconds)
        previous = None
        stable_cycles = 0
        while time.monotonic() < deadline:
            screenshot = _grab_screen()
            current = screenshot.tobytes()
            if previous is not None and current == previous:
                stable_cycles += 1
            else:
                stable_cycles = 0
            previous = current
            if stable_cycles >= 2:
                break
            time.sleep(8)
            
    path = run_dir / "final_screen.png"
    _grab_screen().save(path)
    return path


def _grab_screen():
    try:
        from PIL import ImageGrab
    except ImportError as exc:
        raise RuntimeError("Pillow/ImageGrab no esta instalado") from exc
    return ImageGrab.grab()


def _extract_tokens_with_gemini(screenshot_path: Path, run_dir: Path) -> Path | None:
    try:
        import google.generativeai as genai
    except ImportError:
        return None
        
    api_key = os.getenv("ORCH_GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        try:
            creds = Path("D:/credenciales").read_text(encoding="utf-8")
            for line in creds.splitlines():
                if "GOOGLE_API_KEY" in line and "=" in line:
                    api_key = line.split("=", 1)[1].strip().strip("'\"")
                    break
        except Exception:
            pass
            
    if not api_key:
        print("No se encontro GOOGLE_API_KEY para usar Vision.")
        return None
        
    genai.configure(api_key=api_key)
    try:
        import PIL.Image
        img = PIL.Image.open(screenshot_path)
    except Exception:
        return None
        
    model = genai.GenerativeModel('gemini-2.5-flash')
    try:
        prompt = (
            "Analiza esta captura de pantalla de Codex Desktop. "
            "Devuelve un JSON estricto con la siguiente estructura:\n"
            "{\n"
            '  "narrative": "El resumen narrativo de la respuesta que ha dado el asistente.",\n'
            '  "files": ["rutas/a/archivos.txt", "mencionadas/en/la/interfaz.py"]\n'
            "}\n"
            "Si no hay archivos mencionados, la lista de archivos debe estar vacía. "
            "Asegúrate de que la salida sea SÓLO JSON."
        )
        response = model.generate_content([prompt, img])
        response_text = response.text
    except Exception as exc:
        print(f"Error en Gemini Vision: {exc}")
        return None
        
    import re
    import json
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", response_text, re.DOTALL)
    if json_match:
        response_text = json_match.group(1)
        
    try:
        data = json.loads(response_text)
    except Exception:
        data = {"narrative": response_text, "files": []}
        
    path = run_dir / "vision_result.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Operador de Codex Desktop para tareas visuales.")
    parser.add_argument("--botfather-lab", action="store_true", help="Genera la receta para crear 4 bots del laboratorio.")
    parser.add_argument("--list-windows", action="store_true", help="Lista titulos de ventanas visibles para ajustar --window-re.")
    parser.add_argument("--label", default="Inspector Lab")
    parser.add_argument("--username-prefix", default="inspector_lab")
    parser.add_argument("--prompt-text", default="", help="Prompt libre para enviar a Codex Desktop.")
    parser.add_argument("--send", action="store_true", help="Envia realmente el prompt a Codex Desktop.")
    parser.add_argument("--no-new-chat", action="store_true")
    parser.add_argument("--debug-draft", action="store_true", help="Guarda una captura tras pegar el prompt y antes de enviar.")
    parser.add_argument("--pause-after-paste", action="store_true", help="Pega el prompt, guarda captura y detiene el flujo antes de enviar.")
    parser.add_argument("--resume-send", action="store_true", help="Solo pulsa enviar sobre una conversacion ya preparada.")
    parser.add_argument("--wait-seconds", type=int, default=1800)
    parser.add_argument("--window-re", default=DEFAULT_WINDOW_RE)
    args = parser.parse_args()

    if args.list_windows:
        print(json.dumps(list_window_titles(), indent=2, ensure_ascii=False))
        return 0
    if args.prompt_text.strip():
        prompt = args.prompt_text.strip()
    elif args.botfather_lab:
        prompt = build_botfather_prompt(build_lab_bot_names(args.label), args.username_prefix, args.label)
    else:
        raise SystemExit("Usa --botfather-lab o --prompt-text.")
    result = run_desktop_codex_operator(
        prompt,
        send=args.send or args.pause_after_paste or args.resume_send,
        new_chat=not args.no_new_chat,
        wait_seconds=args.wait_seconds,
        window_re=args.window_re,
        debug_draft=args.debug_draft,
        pause_after_paste=args.pause_after_paste,
        resume_send=args.resume_send,
    )
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
