from __future__ import annotations

import json
from pathlib import Path
from threading import Lock


class CodexDirStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write([])

    def list(self) -> list[Path]:
        with self._lock:
            return self._read()

    def add(self, raw_path: str) -> tuple[bool, str, Path | None]:
        path = Path(raw_path.strip().strip('"')).expanduser()
        try:
            resolved = path.resolve()
        except OSError:
            return False, "No pude resolver esa ruta.", None
        if not resolved.exists() or not resolved.is_dir():
            return False, f"La ruta no existe o no es una carpeta: {resolved}", resolved

        with self._lock:
            paths = self._read()
            if any(str(existing).lower() == str(resolved).lower() for existing in paths):
                return True, "Esa carpeta ya estaba anadida.", resolved
            paths.append(resolved)
            self._write(paths)
        return True, "Carpeta anadida a Codex.", resolved

    def remove(self, raw_path: str) -> bool:
        target = Path(raw_path.strip().strip('"')).expanduser()
        try:
            resolved = target.resolve()
        except OSError:
            resolved = target
        with self._lock:
            paths = self._read()
            kept = [path for path in paths if str(path).lower() != str(resolved).lower()]
            changed = len(kept) != len(paths)
            if changed:
                self._write(kept)
            return changed

    def _read(self) -> list[Path]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8") or "[]")
        except (OSError, json.JSONDecodeError):
            raw = []
        if not isinstance(raw, list):
            return []
        return [Path(value).expanduser().resolve() for value in raw if isinstance(value, str) and value.strip()]

    def _write(self, paths: list[Path]) -> None:
        data = [str(path) for path in paths]
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
