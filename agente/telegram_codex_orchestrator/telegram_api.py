from __future__ import annotations

import json
import mimetypes
import urllib.error
import urllib.parse
import urllib.request
import uuid
import os
import time
import shutil
from pathlib import Path
from typing import Any


class TelegramApi:
    def __init__(self, token: str, chunk_size: int = 3500) -> None:
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.chunk_size = chunk_size
        # Detect if we should use local filesystem mock or real Telegram HTTP API
        self.is_local = os.getenv("TELEGRAM_TRANSPORT", "telegram").strip().lower() == "local"
        self.bus_dir = Path("d:/local_telegram_bus")

    def call(self, method: str, data: dict[str, Any]) -> dict[str, Any]:
        if self.is_local:
            # Shim for local mode if call() is invoked directly for getMe etc.
            if method == "getMe":
                return {
                    "ok": True,
                    "result": {
                        "id": 8529933109,
                        "is_bot": True,
                        "first_name": "Openzxzxzx",
                        "username": "Openzxzxzxbot"
                    }
                }
            return {"ok": True, "result": {}}

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
        if self.is_local:
            updates_dir = self.bus_dir / "updates_controller"
            updates_dir.mkdir(parents=True, exist_ok=True)
            
            def fetch_local_updates():
                local_updates = []
                for f in updates_dir.glob("update_*.json"):
                    try:
                        uid_str = f.stem.replace("update_", "")
                        uid = int(uid_str)
                        if offset is None or uid >= offset:
                            update_data = json.loads(f.read_text(encoding="utf-8"))
                            local_updates.append((uid, update_data))
                    except Exception:
                        pass
                local_updates.sort(key=lambda x: x[0])
                return [x[1] for x in local_updates]

            # Long polling simulation
            start_time = time.monotonic()
            while True:
                results = fetch_local_updates()
                if results:
                    return results
                
                if time.monotonic() - start_time >= timeout:
                    break
                
                time.sleep(0.5)
            return []
        else:
            data: dict[str, Any] = {"timeout": timeout, "allowed_updates": json.dumps(["message"])}
            if offset is not None:
                data["offset"] = offset
            return self.call("getUpdates", data).get("result", [])

    def send_message(self, chat_id: int, text: str) -> None:
        if self.is_local:
            updates_agent_dir = self.bus_dir / "updates_agent"
            updates_agent_dir.mkdir(parents=True, exist_ok=True)
            
            counter_file = self.bus_dir / "counters" / "agent_id.txt"
            counter_file.parent.mkdir(parents=True, exist_ok=True)
            
            next_id = 2000
            if counter_file.exists():
                try:
                    next_id = int(counter_file.read_text().strip())
                except Exception:
                    pass
            counter_file.write_text(str(next_id + 1))
            
            payload = {
                "update_id": next_id,
                "message": {
                    "message_id": next_id,
                    "from": {
                        "id": 8529933109,
                        "is_bot": True,
                        "first_name": "Openzxzxzx",
                        "username": "Openzxzxzxbot"
                    },
                    "chat": {
                        "id": chat_id,
                        "type": "supergroup"
                    },
                    "text": text,
                    "date": int(time.time())
                }
            }
            
            dest_file = updates_agent_dir / f"update_{next_id}.json"
            dest_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        else:
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
        if self.is_local:
            files_dir = self.bus_dir / "files"
            files_dir.mkdir(parents=True, exist_ok=True)
            
            dest_file = files_dir / audio_path.name
            shutil.copy(audio_path, dest_file)
            
            updates_agent_dir = self.bus_dir / "updates_agent"
            counter_file = self.bus_dir / "counters" / "agent_id.txt"
            
            next_id = 2000
            if counter_file.exists():
                try:
                    next_id = int(counter_file.read_text().strip())
                except Exception:
                    pass
            counter_file.write_text(str(next_id + 1))
            
            payload = {
                "update_id": next_id,
                "message": {
                    "message_id": next_id,
                    "from": {
                        "id": 8529933109,
                        "is_bot": True,
                        "first_name": "Openzxzxzx",
                        "username": "Openzxzxzxbot"
                    },
                    "chat": {
                        "id": chat_id,
                        "type": "supergroup"
                    },
                    "audio": {
                        "file_id": audio_path.name,
                        "file_name": audio_path.name,
                        "file_size": audio_path.stat().st_size
                    },
                    "caption": caption,
                    "date": int(time.time())
                }
            }
            dest_file_json = updates_agent_dir / f"update_{next_id}.json"
            dest_file_json.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        else:
            fields = {"chat_id": str(chat_id)}
            if caption:
                fields["caption"] = caption[:1024]
            self._multipart_call("sendAudio", fields, "audio", audio_path)

    def send_photo(self, chat_id: int, photo_path: Path, caption: str = "") -> None:
        if self.is_local:
            files_dir = self.bus_dir / "files"
            files_dir.mkdir(parents=True, exist_ok=True)
            
            dest_file = files_dir / photo_path.name
            shutil.copy(photo_path, dest_file)
            
            updates_agent_dir = self.bus_dir / "updates_agent"
            counter_file = self.bus_dir / "counters" / "agent_id.txt"
            
            next_id = 2000
            if counter_file.exists():
                try:
                    next_id = int(counter_file.read_text().strip())
                except Exception:
                    pass
            counter_file.write_text(str(next_id + 1))
            
            payload = {
                "update_id": next_id,
                "message": {
                    "message_id": next_id,
                    "from": {
                        "id": 8529933109,
                        "is_bot": True,
                        "first_name": "Openzxzxzx",
                        "username": "Openzxzxzxbot"
                    },
                    "chat": {
                        "id": chat_id,
                        "type": "supergroup"
                    },
                    "photo": [
                        {
                            "file_id": photo_path.name,
                            "file_size": photo_path.stat().st_size,
                            "width": 800,
                            "height": 600
                        }
                    ],
                    "caption": caption,
                    "date": int(time.time())
                }
            }
            dest_file_json = updates_agent_dir / f"update_{next_id}.json"
            dest_file_json.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        else:
            fields = {"chat_id": str(chat_id)}
            if caption:
                fields["caption"] = caption[:1024]
            self._multipart_call("sendPhoto", fields, "photo", photo_path)

    def get_file_path(self, file_id: str) -> str:
        if self.is_local:
            return str(self.bus_dir / "files" / file_id)
        payload = self.call("getFile", {"file_id": file_id})
        result = payload.get("result") or {}
        return str(result.get("file_path", ""))

    def download_file(self, file_id: str, destination: Path) -> Path:
        if self.is_local:
            src_file = self.bus_dir / "files" / file_id
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src_file, destination)
            return destination
        else:
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
