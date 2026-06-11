import subprocess
from pathlib import Path
from ..models import TaskRequest, RouteDecision, OrchestratorResult

def execute_local_command(request: TaskRequest, decision: RouteDecision, cwd: Path) -> OrchestratorResult:
    """Ejecuta un comando rápido de terminal localmente."""
    command = request.text.replace("ejecuta", "").strip()
    if not command:
        return OrchestratorResult(
            ok=False, tool_id=decision.tool_id, tier=decision.tier, output="", 
            error="No se proporcionó un comando.", elapsed_seconds=0, 
            privacy_mode=decision.privacy_mode
        )
        
    try:
        proc = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=str(cwd), timeout=30)
        output = proc.stdout if proc.returncode == 0 else proc.stderr
        ok = proc.returncode == 0
        error = None if ok else f"Code {proc.returncode}"
        
        return OrchestratorResult(
            ok=ok,
            tool_id=decision.tool_id,
            tier=decision.tier,
            output=output.strip() or "[Sin salida]",
            error=error,
            elapsed_seconds=0,
            privacy_mode=decision.privacy_mode
        )
    except subprocess.TimeoutExpired:
         return OrchestratorResult(
            ok=False, tool_id=decision.tool_id, tier=decision.tier, output="", 
            error="Timeout de comando local", elapsed_seconds=0, 
            privacy_mode=decision.privacy_mode
        )
    except Exception as e:
        return OrchestratorResult(
            ok=False, tool_id=decision.tool_id, tier=decision.tier, output="", 
            error=str(e), elapsed_seconds=0, 
            privacy_mode=decision.privacy_mode
        )
