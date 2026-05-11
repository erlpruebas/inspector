from __future__ import annotations

import os
import re
import shlex
import json
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
INSPECTOR_ROOT = ROOT.parent


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return

    if path.name.lower() == ".env":
        try:
            from dotenv import load_dotenv

            load_dotenv(dotenv_path=path, override=False)
            return
        except Exception:
            pass

    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_environment() -> None:
    for path in (
        Path("D:/credenciales"),
        INSPECTOR_ROOT / ".env",
        Path("D:/variables/.env"),
        ROOT / ".env",
    ):
        _load_env_file(path)
    _apply_marked_google_key(Path("D:/credenciales"))


def _apply_marked_google_key(path: Path) -> None:
    marked = _find_marked_google_key(path)
    if marked:
        os.environ["ORCH_GOOGLE_API_KEY"] = marked


def _find_marked_google_key(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""

    for line in lines:
        if "erlquimica" not in line.lower() or "google_api_key" not in line.lower():
            continue
        match = re.search(r"GOOGLE_API_KEY\s*=\s*['\"]?([^'\"\s#]+)", line, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def _env_int(*names: str, default: int = 0) -> int:
    for name in names:
        value = os.getenv(name)
        if value:
            try:
                return int(value)
            except ValueError:
                return default
    return default


def _env_path(name: str, default: Path) -> Path:
    value = os.getenv(name)
    if not value:
        return default
    return Path(value).expanduser().resolve()


def _env_path_list(name: str) -> list[Path]:
    value = os.getenv(name, "").strip()
    if not value:
        return []
    return [Path(part.strip()).expanduser().resolve() for part in value.split(";") if part.strip()]


def _json_path_list(path: Path) -> list[Path]:
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(raw, list):
        return []
    paths: list[Path] = []
    for value in raw:
        if isinstance(value, str) and value.strip():
            paths.append(Path(value).expanduser().resolve())
    return paths


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    telegram_allowed_user_id: int
    telegram_poll_timeout: int
    codex_command: list[str]
    codex_workdir: Path
    codex_dirs_file: Path
    codex_extra_dirs: list[Path]
    codex_model: str
    codex_sandbox: str
    codex_approval: str
    codex_timeout_seconds: int
    message_chunk_size: int
    memory_file: Path
    memories_file: Path
    threads_file: Path
    pending_tasks_file: Path
    alarms_file: Path
    voice_settings_file: Path
    voice_runtime_dir: Path
    alarm_check_seconds: int
    google_api_key: str
    google_api_key_source: str
    groq_api_key: str
    google_model: str
    google_intent_enabled: bool
    google_intent_timeout_seconds: int
    hot_reload: bool
    code_watch_seconds: int
    drain_pending_on_start: bool

    @property
    def ready(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_allowed_user_id)


def load_settings() -> Settings:
    load_environment()

    codex_command_text = os.getenv("ORCH_CODEX_COMMAND", "codex").strip() or "codex"
    codex_dirs_file = _env_path("ORCH_CODEX_DIRS_FILE", ROOT / "memory" / "codex_dirs.json")
    memory_file = _env_path("ORCH_MEMORY_FILE", ROOT / "memory" / "events.txt")
    memories_file = _env_path("ORCH_MEMORIES_FILE", ROOT / "memory" / "memories.txt")
    threads_file = _env_path("ORCH_THREADS_FILE", ROOT / "memory" / "threads.json")
    pending_tasks_file = _env_path("ORCH_PENDING_TASKS_FILE", ROOT / "memory" / "pending_tasks.json")
    alarms_file = _env_path("ORCH_ALARMS_FILE", ROOT / "memory" / "alarms.json")
    voice_settings_file = _env_path("ORCH_VOICE_SETTINGS_FILE", ROOT / "memory" / "voice_settings.json")
    voice_runtime_dir = _env_path("ORCH_VOICE_RUNTIME_DIR", ROOT / "runtime" / "voice")
    google_api_key, google_api_key_source = _google_api_key()

    return Settings(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_allowed_user_id=_env_int(
            "ORCH_TELEGRAM_ALLOWED_USER_ID",
            "TELEGRAM_ALLOWED_USER_ID",
            "TELEGRAM_CHAT_ID",
            default=0,
        ),
        telegram_poll_timeout=_env_int("ORCH_TELEGRAM_POLL_TIMEOUT", default=30),
        codex_command=shlex.split(codex_command_text, posix=False),
        codex_workdir=_env_path("ORCH_CODEX_WORKDIR", INSPECTOR_ROOT),
        codex_dirs_file=codex_dirs_file,
        codex_extra_dirs=_dedupe_paths([*_json_path_list(codex_dirs_file), *_env_path_list("ORCH_CODEX_EXTRA_DIRS")]),
        codex_model=os.getenv("ORCH_CODEX_MODEL", "").strip(),
        codex_sandbox=os.getenv("ORCH_CODEX_SANDBOX", "workspace-write").strip(),
        codex_approval=os.getenv("ORCH_CODEX_APPROVAL", "never").strip(),
        codex_timeout_seconds=_env_int("ORCH_CODEX_TIMEOUT_SECONDS", default=1800),
        message_chunk_size=_env_int("ORCH_TELEGRAM_CHUNK_SIZE", default=3500),
        memory_file=memory_file,
        memories_file=memories_file,
        threads_file=threads_file,
        pending_tasks_file=pending_tasks_file,
        alarms_file=alarms_file,
        voice_settings_file=voice_settings_file,
        voice_runtime_dir=voice_runtime_dir,
        alarm_check_seconds=_env_int("ORCH_ALARM_CHECK_SECONDS", default=10),
        google_api_key=google_api_key,
        google_api_key_source=google_api_key_source,
        groq_api_key=os.getenv("GROQ_API_KEY", "").strip(),
        google_model=os.getenv("ORCH_GOOGLE_INTENT_MODEL", os.getenv("GOOGLE_MODEL_ALT", "gemini-2.5-flash-lite")).strip(),
        google_intent_enabled=os.getenv("ORCH_GOOGLE_INTENT_ENABLED", "1").strip().lower() not in {"0", "false", "no"},
        google_intent_timeout_seconds=_env_int("ORCH_GOOGLE_INTENT_TIMEOUT_SECONDS", default=20),
        hot_reload=os.getenv("ORCH_HOT_RELOAD", "1").strip().lower() not in {"0", "false", "no"},
        code_watch_seconds=_env_int("ORCH_CODE_WATCH_SECONDS", default=5),
        drain_pending_on_start=os.getenv("ORCH_DRAIN_PENDING_ON_START", "1").strip().lower() not in {"0", "false", "no"},
    )


def _dedupe_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    result: list[Path] = []
    for path in paths:
        key = str(path).lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result


def _google_api_key() -> tuple[str, str]:
    candidates = (
        ("D:/credenciales use this .erlquimica", os.getenv("ORCH_GOOGLE_API_KEY", "")),
        ("GOOGLE_API_KEY", os.getenv("GOOGLE_API_KEY", "")),
        ("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", "")),
    )
    for source, value in candidates:
        if value:
            return value, source
    return "", "missing"
