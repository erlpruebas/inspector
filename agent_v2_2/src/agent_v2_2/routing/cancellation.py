from typing import Dict
import uuid

class CancellationManager:
    """Gestiona la cancelación de una operación en curso."""
    
    def __init__(self):
        self._cancellations: Dict[str, bool] = {}

    def is_cancelled(self, execution_id: str) -> bool:
        return self._cancellations.get(execution_id, False)

    def cancel(self, execution_id: str):
        self._cancellations[execution_id] = True

    def clear(self, execution_id: str):
        self._cancellations.pop(execution_id, None)
