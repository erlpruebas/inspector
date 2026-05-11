from __future__ import annotations

import os
from pathlib import Path


ENV_PATHS = (
    Path("D:/credenciales"),
    Path("D:/variables/.env"),
    Path("D:/inspector/.env"),
    Path("D:/inspector/telegram_codex_orchestrator/.env"),
)


def load_env_files() -> None:
    _ensure_tool_paths()
    for path in ENV_PATHS:
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def google_api_key() -> str:
    return (
        os.getenv("ORCH_GOOGLE_API_KEY", "").strip()
        or os.getenv("GOOGLE_API_KEY", "").strip()
        or os.getenv("GEMINI_API_KEY", "").strip()
    )


def key_status() -> dict[str, bool]:
    load_env_files()
    return {
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY", "").strip()),
        "GROQ_API_KEY": bool(os.getenv("GROQ_API_KEY", "").strip()),
        "OPENROUTER_API_KEY": bool(os.getenv("OPENROUTER_API_KEY", "").strip()),
        "GOOGLE_API_KEY": bool(os.getenv("GOOGLE_API_KEY", "").strip()),
        "GEMINI_API_KEY": bool(os.getenv("GEMINI_API_KEY", "").strip()),
        "ORCH_GOOGLE_API_KEY": bool(os.getenv("ORCH_GOOGLE_API_KEY", "").strip()),
    }


def _ensure_tool_paths() -> None:
    paths = []
    appdata = os.getenv("APPDATA", "")
    if appdata:
        paths.append(str(Path(appdata) / "npm"))
    paths.extend(
        [
            "C:/Program Files/nodejs",
            "C:/Program Files/ripgrep",
        ]
    )
    localappdata = os.getenv("LOCALAPPDATA", "")
    if localappdata:
        winget_root = Path(localappdata) / "Microsoft" / "WinGet" / "Packages"
        if winget_root.exists():
            paths.extend(str(path.parent) for path in winget_root.rglob("rg.exe"))
    current = os.getenv("PATH", "")
    current_parts = [part for part in current.split(os.pathsep) if part]
    normalized = {part.rstrip("\\/").casefold() for part in current_parts}
    for path in paths:
        if Path(path).exists() and path.rstrip("\\/").casefold() not in normalized:
            current_parts.insert(0, path)
            normalized.add(path.rstrip("\\/").casefold())
    os.environ["PATH"] = os.pathsep.join(current_parts)
