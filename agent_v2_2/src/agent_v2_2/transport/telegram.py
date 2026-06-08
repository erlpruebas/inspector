import logging
import time
from typing import Callable, Optional, Dict, Any, List
import requests
from pathlib import Path
from ..config import Config

logger = logging.getLogger("agent_v2_2.transport.telegram")

class TelegramTransport:
    def __init__(self, config: Config):
        self.config = config.telegram
        self.token = self.config.bot_token
        self.allowed_users = set(self.config.allowed_users)
        self.allowed_chats = set(self.config.allowed_chats)
        # La unión de usuarios y chats nos da la lista efectiva de IDs permitidos
        self.allowed_ids = self.allowed_users.union(self.allowed_chats)
        
        self.message_handler: Optional[Callable[[str, int], None]] = None
        self.progress_handler: Optional[Callable[[int, str], None]] = None

    def set_message_handler(self, handler: Callable[[str, int], None]):
        self.message_handler = handler

    def set_progress_handler(self, handler: Callable[[int, str], None]) -> None:
        self.progress_handler = handler

    def _get_updates(self, offset: Optional[int] = None) -> List[Dict]:
        if not self.token:
            return []
        params: Dict[str, Any] = {"timeout": 30, "allowed_updates": ["message", "edited_message"]}
        if offset is not None:
            params["offset"] = offset
        try:
            response = requests.get(
                f"https://api.telegram.org/bot{self.token}/getUpdates", 
                params=params, 
                timeout=40
            )
            response.raise_for_status()
            return response.json().get("result", [])
        except Exception as exc:
            logger.error(f"Telegram getUpdates failed: {exc}")
            return []

    def send_message(self, chat_id: int, text: str) -> bool:
        if not self.token:
            return False
        for chunk in self._chunk_message(text):
            try:
                response = requests.post(
                    f"https://api.telegram.org/bot{self.token}/sendMessage",
                    json={"chat_id": chat_id, "text": chunk},
                    timeout=15,
                )
                response.raise_for_status()
            except Exception as exc:
                logger.error(f"Telegram sendMessage failed: {exc}")
                return False
        return True

    def send_photo(self, chat_id: int, photo_path: Path, caption: str = "") -> bool:
        if not self.token:
            return False
        try:
            with photo_path.open("rb") as handle:
                requests.post(
                    f"https://api.telegram.org/bot{self.token}/sendPhoto",
                    data={"chat_id": chat_id, "caption": caption[:1024]},
                    files={"photo": handle},
                    timeout=60,
                )
            return True
        except Exception as exc:
            logger.error(f"Telegram sendPhoto failed: {exc}")
            return False

    def send_audio(self, chat_id: int, audio_path: Path, caption: str = "") -> bool:
        if not self.token:
            return False
        try:
            with audio_path.open("rb") as handle:
                requests.post(
                    f"https://api.telegram.org/bot{self.token}/sendAudio",
                    data={"chat_id": chat_id, "caption": caption[:1024]},
                    files={"audio": handle},
                    timeout=60,
                )
            return True
        except Exception as exc:
            logger.error(f"Telegram sendAudio failed: {exc}")
            return False

    def send_progress(self, chat_id: int, stage: str, detail: str = "") -> bool:
        label = {
            "received": "Recibido",
            "routed": "Enrutado",
            "executing": "Ejecutando",
            "completed": "Completado",
            "failed": "Falló",
        }.get(stage, stage)
        message = f"Estado: {label}"
        if detail:
            message = f"{message}\n{detail}"
        if self.progress_handler:
            try:
                self.progress_handler(chat_id, stage)
            except Exception as exc:
                logger.warning(f"Progress handler failed: {exc}")
        return self.send_message(chat_id, message)

    def _chunk_message(self, text: str, limit: int = 3500) -> List[str]:
        cleaned = text.strip()
        if not cleaned:
            return [""]
        chunks: List[str] = []
        remaining = cleaned
        while len(remaining) > limit:
            split_at = remaining.rfind("\n", 0, limit)
            if split_at < limit // 2:
                split_at = remaining.rfind(" ", 0, limit)
            if split_at < limit // 2:
                split_at = limit
            chunks.append(remaining[:split_at].strip())
            remaining = remaining[split_at:].strip()
        if remaining:
            chunks.append(remaining)
        return chunks

    def process_update(self, update: Dict) -> None:
        message = update.get("message") or update.get("edited_message") or {}
        chat_id = message.get("chat", {}).get("id")
        if not chat_id:
            return
            
        if self.allowed_ids and chat_id not in self.allowed_ids:
            logger.warning(f"Unauthorized Telegram chat: {chat_id}")
            return
            
        # Intentar extraer texto
        text = (message.get("text") or message.get("caption") or "").strip()
        
        # Intentar extraer media (voz, audio, documento, etc)
        media_file_id = None
        media_type = None
        for key in ["voice", "audio", "document", "photo"]:
            if key in message:
                media_item = message[key]
                # En el caso de photo, suele ser una lista, tomamos la más grande
                if key == "photo" and isinstance(media_item, list):
                    media_item = media_item[-1]
                media_file_id = media_item.get("file_id")
                media_type = key
                break
                
        # Delegar al handler
        if (text or media_file_id) and self.message_handler:
            self.message_handler(text, chat_id, media_file_id=media_file_id, media_type=media_type)

    def download_file(self, file_id: str, target_path: Path) -> Path:
        """Descarga un fichero de Telegram por file_id a la ruta objetivo."""
        if not self.token:
            raise RuntimeError("Cannot download file, missing token")
            
        target_path.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(
            f"https://api.telegram.org/bot{self.token}/getFile",
            params={"file_id": file_id},
            timeout=30,
        )
        response.raise_for_status()
        file_path = response.json().get("result", {}).get("file_path")
        if not file_path:
            raise RuntimeError("Telegram did not return a file path.")
            
        # Ajustamos sufijo según el fichero original si el path no lo tenía claro
        file_name = Path(file_path).name
        
        file_response = requests.get(
            f"https://api.telegram.org/file/bot{self.token}/{file_path}",
            timeout=120,
        )
        file_response.raise_for_status()
        
        output_path = target_path
        if output_path.is_dir():
            output_path = output_path / file_name
            
        output_path.write_bytes(file_response.content)
        return output_path

    def start_polling(self):
        if not self.token:
            logger.error("Missing Telegram token. Polling cannot start.")
            return
        if not self.allowed_ids:
            logger.warning("No allowed Telegram IDs configured. Bot will ignore all messages.")
            
        logger.info("Telegram transport started.")
        offset = None
        while True:
            for update in self._get_updates(offset):
                offset = update["update_id"] + 1
                try:
                    self.process_update(update)
                except Exception as exc:
                    logger.exception(f"Error processing update {update.get('update_id')}: {exc}")
            time.sleep(1)
