from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from ..config import load_config

logger = logging.getLogger("agent_v2_2.scheduling.codex_quota")


class CodexQuotaMonitor:
    """Monitor de cuota Codex y pie compacto cuando exista snapshot válido."""

    def __init__(self) -> None:
        config = load_config()
        self.snapshot_path = config.workspace_root / "codex_quota.json"
        self._max_monthly_tokens = 1_000_000
        self._state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        if not self.snapshot_path.exists():
            return {"used_tokens": 0, "updated_at": None}
        try:
            payload = json.loads(self.snapshot_path.read_text(encoding="utf-8"))
            return {
                "used_tokens": int(payload.get("used_tokens", 0)),
                "updated_at": payload.get("updated_at"),
            }
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("No se pudo leer la cuota de Codex: %s", exc)
            return {"used_tokens": 0, "updated_at": None}

    def _save_state(self) -> None:
        self.snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        self.snapshot_path.write_text(
            json.dumps(self._state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def record_usage(self, tool_id: str, tokens: int) -> None:
        tokens = max(0, int(tokens))
        logger.info("Registrando %s tokens para %s.", tokens, tool_id)
        self._state["used_tokens"] = min(
            self._max_monthly_tokens,
            int(self._state.get("used_tokens", 0)) + tokens,
        )
        self._state["updated_at"] = tool_id
        self._save_state()

    def get_remaining_quota(self) -> str:
        used = int(self._state.get("used_tokens", 0))
        remaining = max(0, self._max_monthly_tokens - used)
        percent = int(round((remaining / self._max_monthly_tokens) * 100))
        return f"Cuota Codex: {percent}% disponible ({remaining} tokens restantes)."

    def should_reject(self, estimated_tokens: int) -> bool:
        estimated_tokens = max(0, int(estimated_tokens))
        used = int(self._state.get("used_tokens", 0))
        remaining = max(0, self._max_monthly_tokens - used)
        remaining_percent = (remaining / self._max_monthly_tokens) * 100 if self._max_monthly_tokens else 0.0
        minimum_percent = int(load_config().quota.minimum_quota_percent)
        if remaining_percent <= minimum_percent:
            return estimated_tokens > remaining
        return False

    def get_footer(self) -> Optional[str]:
        used = int(self._state.get("used_tokens", 0))
        remaining = max(0, self._max_monthly_tokens - used)
        percent = int(round((remaining / self._max_monthly_tokens) * 100))
        return f"[ Codex: {percent}% disponible ]"
