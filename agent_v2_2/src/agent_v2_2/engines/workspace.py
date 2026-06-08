import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional
from ..config import load_config

class WorkspaceManager:
    def __init__(self, base_dir: Optional[Path] = None):
        config = load_config()
        self.base_dir = (base_dir or config.workspace_root).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.active_workspaces = []

    def create_isolated_workspace(self, prefix: str = "task_") -> Path:
        """Crea un directorio aislado temporal para ejecución segura."""
        temp_dir = tempfile.mkdtemp(prefix=prefix, dir=self.base_dir)
        path = Path(temp_dir).resolve()
        self.active_workspaces.append(path)
        return path

    def cleanup_workspace(self, path: Path):
        """Elimina un workspace aislado y su contenido."""
        if path in self.active_workspaces:
            if path.exists() and path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            self.active_workspaces.remove(path)

    def cleanup_all(self):
        for path in list(self.active_workspaces):
            self.cleanup_workspace(path)
