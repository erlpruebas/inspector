from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import os
import time
from urllib import request as urllib_request
from urllib.parse import urlencode

from .lab_contracts import ScheduledLabMessage


@dataclass(frozen=True)
class TelegramEndpoint:
    token: str
    chat_id: str

    @classmethod
    def from_env(cls, token_env: str, chat_id_env: str) -> "TelegramEndpoint":
        token = os.getenv(token_env, "")
        chat_id = os.getenv(chat_id_env, "")
        if not token or not chat_id:
            raise RuntimeError(f"Faltan variables {token_env} y/o {chat_id_env}.")
        return cls(token=token, chat_id=chat_id)


class TelegramLabTransport:
    def __init__(self, endpoint: TelegramEndpoint):
        self.endpoint = endpoint

    def send_message(self, text: str) -> dict:
        url = f"https://api.telegram.org/bot{self.endpoint.token}/sendMessage"
        payload = urlencode({"chat_id": self.endpoint.chat_id, "text": text})
        req = urllib_request.Request(url, data=payload.encode("utf-8"), method="POST")
        with urllib_request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))

    def send_document(self, path: Path, caption: str = "") -> dict:
        try:
            import requests
        except ImportError as exc:
            raise RuntimeError("requests no esta instalado; no puedo enviar documentos por Telegram.") from exc
        url = f"https://api.telegram.org/bot{self.endpoint.token}/sendDocument"
        with path.open("rb") as handle:
            response = requests.post(
                url,
                data={"chat_id": self.endpoint.chat_id, "caption": caption},
                files={"document": (path.name, handle, "application/octet-stream")},
                timeout=120,
            )
        response.raise_for_status()
        return response.json()


def load_round_robin_endpoints(prefix: str = "LAB_BOT", count: int = 4) -> list[TelegramEndpoint]:
    endpoints: list[TelegramEndpoint] = []
    for index in range(1, count + 1):
        token = os.getenv(f"{prefix}_{index}_TOKEN", "")
        chat_id = os.getenv(f"{prefix}_{index}_CHAT_ID", os.getenv("LAB_TELEGRAM_CHAT_ID", ""))
        if token and chat_id:
            endpoints.append(TelegramEndpoint(token=token, chat_id=chat_id))
    return endpoints


def render_lab_message(item: ScheduledLabMessage) -> str:
    files = "\n".join(f"- {path.name}" for path in item.task.required_files) or "- sin archivos"
    return f"""
Persona: {item.persona.name}
Profesion: {item.persona.profession}
Tono: {item.persona.tone}

Peticion:
{item.task.prompt}

Archivos que deberian adjuntarse:
{files}
""".strip()


def write_dry_run_evidence(item: ScheduledLabMessage, evidence_dir: Path) -> Path:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    path = evidence_dir / f"{item.sequence:03d}_{item.persona.id}_{item.task.id}.json"
    payload = item.to_evidence()
    payload["rendered_message"] = render_lab_message(item)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def execute_dry_run(schedule: list[ScheduledLabMessage], evidence_dir: Path) -> list[Path]:
    written: list[Path] = []
    for item in schedule:
        if item.delay_seconds:
            time.sleep(min(item.delay_seconds, 0.1))
        written.append(write_dry_run_evidence(item, evidence_dir))
    return written


def execute_telegram_group(schedule: list[ScheduledLabMessage], endpoints: list[TelegramEndpoint], evidence_dir: Path) -> list[Path]:
    if not endpoints:
        raise RuntimeError("No hay endpoints Telegram. Define LAB_BOT_1_TOKEN y LAB_TELEGRAM_CHAT_ID.")
    written: list[Path] = []
    for index, item in enumerate(schedule):
        if item.delay_seconds:
            time.sleep(item.delay_seconds)
        endpoint = endpoints[index % len(endpoints)]
        transport = TelegramLabTransport(endpoint)
        rendered = render_lab_message(item)
        transport.send_message(rendered)
        for file_path in item.task.required_files:
            if file_path.exists():
                transport.send_document(file_path, caption=f"{item.task.id}: {file_path.name}")
        written.append(write_dry_run_evidence(item, evidence_dir))
    return written
