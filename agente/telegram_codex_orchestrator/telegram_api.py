from __future__ import annotations

import json
import mimetypes
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any


class TelegramApi:
    def __init__(self, token: str, chunk_size: int = 3500) -> None:
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.chunk_size = chunk_size

    def call(self, method: str, data: dict[str, Any]) -> dict[str, Any]:
        body = urllib.parse.urlencode(data).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/{method}",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = response.read().decode("utf-8", errors="replace")
        parsed = json.loads(payload)
        if not parsed.get("ok"):
            raise RuntimeError(f"Telegram devolvio ok=false en {method}: {payload[:500]}")
        return parsed

    def get_updates(self, offset: int | None, timeout: int) -> list[dict[str, Any]]:
        data: dict[str, Any] = {"timeout": timeout, "allowed_updates": json.dumps(["message"])}
        if offset is not None:
            data["offset"] = offset
        return self.call("getUpdates", data).get("result", [])

    def send_message(self, chat_id: int, text: str) -> None:
        chunks = self._chunks(text or "(sin respuesta)")
        for chunk in chunks:
            self.call(
                "sendMessage",
                {
                    "chat_id": str(chat_id),
                    "text": chunk,
                    "disable_web_page_preview": "true",
                },
            )

    def send_audio(self, chat_id: int, audio_path: Path, caption: str = "") -> None:
        fields = {"chat_id": str(chat_id)}
        if caption:
            fields["caption"] = caption[:1024]
        self._multipart_call("sendAudio", fields, "audio", audio_path)

    def send_photo(self, chat_id: int, photo_path: Path, caption: str = "") -> None:
        fields = {"chat_id": str(chat_id)}
        if caption:
            fields["caption"] = caption[:1024]
        self._multipart_call("sendPhoto", fields, "photo", photo_path)

    def get_file_path(self, file_id: str) -> str:
        payload = self.call("getFile", {"file_id": file_id})
        result = payload.get("result") or {}
        return str(result.get("file_path", ""))

    def download_file(self, file_id: str, destination: Path) -> Path:
        file_path = self.get_file_path(file_id)
        if not file_path:
            raise RuntimeError("Telegram no devolvio file_path")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(f"{self.base_url}/file/{file_path}", timeout=120) as response:
            destination.write_bytes(response.read())
        return destination

    def _multipart_call(self, method: str, fields: dict[str, str], file_field: str, file_path: Path) -> dict[str, Any]:
        boundary = "----codex-telegram-" + uuid.uuid4().hex
        mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        chunks: list[bytes] = []
        for key, value in fields.items():
            chunks.extend(
                [
                    f"--{boundary}\r\n".encode("ascii"),
                    f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"),
                    str(value).encode("utf-8"),
                    b"\r\n",
                ]
            )
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("ascii"),
                (
                    f'Content-Disposition: form-data; name="{file_field}"; '
                    f'filename="{file_path.name}"\r\n'
                ).encode("utf-8"),
                f"Content-Type: {mime_type}\r\n\r\n".encode("ascii"),
                file_path.read_bytes(),
                b"\r\n",
                f"--{boundary}--\r\n".encode("ascii"),
            ]
        )
        request = urllib.request.Request(
            f"{self.base_url}/{method}",
            data=b"".join(chunks),
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = response.read().decode("utf-8", errors="replace")
        parsed = json.loads(payload)
        if not parsed.get("ok"):
            raise RuntimeError(f"Telegram devolvio ok=false en {method}: {payload[:500]}")
        return parsed

    def _chunks(self, text: str) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text]

        chunks: list[str] = []
        remaining = text
        while remaining:
            chunk = remaining[: self.chunk_size]
            split_at = max(chunk.rfind("\n"), chunk.rfind(" "))
            if split_at > self.chunk_size // 2:
                chunk = chunk[:split_at]
            chunks.append(chunk)
            remaining = remaining[len(chunk) :].lstrip()
        return chunks
