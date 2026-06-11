from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

from ..config import load_config


class AllowedDirectoryStore:
    """Persistent additions to the directories explicitly available to the agent."""

    def __init__(
        self,
        path: Path | None = None,
        configured: Iterable[Path] | None = None,
    ) -> None:
        config = load_config()
        self.path = path or (config.workspace_root / "allowed_directories.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.configured = tuple(
            self._normalize(item)
            for item in (configured if configured is not None else config.allowed_directories)
        )

    def list(self) -> list[Path]:
        values = {*self.configured, *self._load_persistent()}
        return sorted(values, key=lambda item: str(item).casefold())

    def add(self, path: Path) -> Path:
        normalized = self._normalize(path)
        if not normalized.exists() or not normalized.is_dir():
            raise ValueError("El directorio no existe o no es una carpeta.")
        values = self._load_persistent()
        values.add(normalized)
        self._save(values)
        return normalized

    def remove(self, path: Path) -> bool:
        normalized = self._normalize(path)
        values = self._load_persistent()
        if normalized not in values:
            return False
        values.remove(normalized)
        self._save(values)
        return True

    def resolve_references(self, text: str, *, limit: int = 20) -> list[Path]:
        """Resolve only file names or absolute paths explicitly named by the user."""
        roots = self.list()
        if not roots or not text.strip():
            return []
        found: list[Path] = []
        seen: set[Path] = set()

        quoted = re.findall(r'["\']([^"\']+\.[A-Za-z0-9]{1,10})["\']', text)
        windows_paths = re.findall(
            r"\b[A-Za-z]:\\[^\r\n<>|?*]+?\.[A-Za-z0-9]{1,10}\b",
            text,
        )
        candidates = quoted + windows_paths
        file_names = re.findall(
            r"(?<![\\/:])\b[\w.()-]+\.[A-Za-z0-9]{1,10}\b",
            text,
        )

        for raw in candidates:
            candidate = Path(raw.strip()).expanduser()
            if not candidate.is_absolute():
                continue
            self._append_if_allowed(candidate, roots, found, seen, limit)

        for raw_name in file_names:
            name = Path(raw_name.strip()).name
            if not name:
                continue
            for root in roots:
                direct = root / name
                if self._append_if_allowed(direct, roots, found, seen, limit):
                    break
                matches = list(root.rglob(name))[:2]
                if len(matches) == 1:
                    self._append_if_allowed(matches[0], roots, found, seen, limit)
                    break
            if len(found) >= limit:
                break
        return found

    def _load_persistent(self) -> set[Path]:
        if not self.path.exists():
            return set()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return set()
        if not isinstance(payload, list):
            return set()
        return {
            self._normalize(Path(str(item)))
            for item in payload
            if str(item).strip()
        }

    def _save(self, values: set[Path]) -> None:
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(
                [str(item) for item in sorted(values, key=lambda value: str(value).casefold())],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        temporary.replace(self.path)

    def _normalize(self, path: Path) -> Path:
        return Path(path).expanduser().resolve()

    def _append_if_allowed(
        self,
        candidate: Path,
        roots: list[Path],
        found: list[Path],
        seen: set[Path],
        limit: int,
    ) -> bool:
        try:
            resolved = candidate.resolve()
        except OSError:
            return False
        if not resolved.is_file():
            return False
        if not any(resolved == root or root in resolved.parents for root in roots):
            return False
        if resolved not in seen and len(found) < limit:
            seen.add(resolved)
            found.append(resolved)
        return True
