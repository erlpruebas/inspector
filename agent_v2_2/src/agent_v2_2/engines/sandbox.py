from pathlib import Path
from ..config import load_config
import os

class SandboxManager:
    """Implementa el sandbox y límites de workspace."""
    
    def __init__(self):
        config = load_config()
        self.allowed_roots = [
            config.workspace_root.resolve(),
            Path(os.getcwd()).resolve()
        ]
        
    def is_path_allowed(self, path: Path) -> bool:
        resolved = path.resolve()
        for root in self.allowed_roots:
            try:
                # Comprobar si resolved está dentro de root
                if resolved.is_relative_to(root):
                    return True
            except ValueError:
                pass
        return False

    def enforce_sandbox(self, path: Path):
        if not self.is_path_allowed(path):
            raise PermissionError(f"El acceso a la ruta '{path}' está prohibido por las reglas del sandbox.")
