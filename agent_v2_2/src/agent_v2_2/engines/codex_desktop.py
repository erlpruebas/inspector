import os
import subprocess
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger("agent_v2_2.engines.codex_desktop")

class CodexDesktopOperator:
    """
    Controlador para ejecutar agentes de programación (como un script externo
    aislado) sobre un directorio, aplazando el control hasta que termine, sin
    afectar al orquestador principal.
    """
    def __init__(self, cli_path: Optional[Path] = None):
        self.cli_path = cli_path or Path(os.getenv("CODEX_CLI_PATH", "codex-cli.exe"))
        
    def execute_task(self, prompt: str, target_dir: Path) -> str:
        """
        Llama al operador de Codex externo.
        """
        if not self.cli_path.exists():
            # Mock para desarrollo si no existe el CLI
            logger.warning(f"Codex CLI no encontrado en {self.cli_path}. Simulando ejecución.")
            return "Simulación: Tarea de codex ejecutada con éxito."
            
        logger.info(f"Ejecutando codex en {target_dir}...")
        
        try:
            result = subprocess.run(
                [str(self.cli_path), "--prompt", prompt, "--dir", str(target_dir)],
                capture_output=True,
                text=True,
                timeout=600 # 10 min max
            )
            
            if result.returncode == 0:
                return f"Codex completó exitosamente:\n{result.stdout}"
            else:
                return f"Error en Codex ({result.returncode}):\n{result.stderr}"
                
        except subprocess.TimeoutExpired:
            return "Timeout: Codex excedió el tiempo máximo de ejecución."
        except Exception as e:
            return f"Excepción ejecutando Codex: {str(e)}"
