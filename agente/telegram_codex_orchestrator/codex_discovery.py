from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def discover_codex_command() -> list[str]:
    env_command = os.getenv("ORCH_CODEX_COMMAND", "").strip()
    if env_command:
        return [env_command]

    executable = discover_codex_executable()
    return [str(executable)] if executable else ["codex"]


def discover_codex_executable() -> Path | None:
    candidates = _candidate_paths()
    runnable = [path for path in candidates if _is_runnable_codex(path)]
    if runnable:
        return runnable[0]
    return None


def _candidate_paths() -> list[Path]:
    candidates: list[Path] = []
    home = Path.home()

    candidates.extend(
        sorted(
            home.glob(".vscode/extensions/openai.chatgpt-*/bin/windows-x86_64/codex.exe"),
            key=lambda path: path.stat().st_mtime if path.exists() else 0,
            reverse=True,
        )
    )
    candidates.extend(
        sorted(
            home.glob(".vscode-insiders/extensions/openai.chatgpt-*/bin/windows-x86_64/codex.exe"),
            key=lambda path: path.stat().st_mtime if path.exists() else 0,
            reverse=True,
        )
    )
    candidates.append(home / ".codex" / ".sandbox-bin" / "codex.exe")

    for name in ("codex.cmd", "codex.exe", "codex"):
        resolved = shutil.which(name)
        if resolved:
            candidates.append(Path(resolved))

    deduped: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path).lower()
        if key not in seen:
            seen.add(key)
            deduped.append(path)
    return deduped


def _is_runnable_codex(path: Path) -> bool:
    if not path.exists() or path.is_dir():
        return False
    try:
        result = subprocess.run(
            [str(path), "--version"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    output = f"{result.stdout}\n{result.stderr}".lower()
    return result.returncode == 0 and "codex" in output
