import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel
from dotenv import load_dotenv

# Cargar variables del .env si existe
load_dotenv()

class TelegramConfig(BaseModel):
    bot_token: str
    allowed_users: List[int] = []
    allowed_chats: List[int] = []

class QuotaConfig(BaseModel):
    minimum_quota_percent: int = 25
    minimum_weekly_percent: int = 0
    max_snapshot_age_seconds: int = 120
    retry_margin_seconds: int = 300

class Config(BaseModel):
    telegram: TelegramConfig
    quota: QuotaConfig
    workspace_root: Path
    allowed_directories: List[Path] = []

def parse_int_list(value: str) -> List[int]:
    if not value:
        return []
    return [int(x.strip()) for x in value.split(",") if x.strip().isdigit()]

def parse_path_list(value: str) -> List[Path]:
    if not value:
        return []
    return [Path(x.strip()) for x in value.split(",") if x.strip()]

def load_config() -> Config:
    workspace_root_env = os.getenv("AGENT_WORKSPACE_ROOT")
    workspace_root = Path(workspace_root_env) if workspace_root_env else Path.cwd() / "runtime" / "workspace"
    
    return Config(
        telegram=TelegramConfig(
            bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            allowed_users=parse_int_list(os.getenv("TELEGRAM_ALLOWED_USERS", "")),
            allowed_chats=parse_int_list(os.getenv("TELEGRAM_ALLOWED_CHATS", "")),
        ),
        quota=QuotaConfig(
            minimum_quota_percent=int(os.getenv("CODEX_MINIMUM_QUOTA_PERCENT", "25")),
            minimum_weekly_percent=int(os.getenv("CODEX_MINIMUM_WEEKLY_PERCENT", "0")),
            max_snapshot_age_seconds=int(os.getenv("CODEX_QUOTA_MAX_AGE_SECONDS", "120")),
            retry_margin_seconds=int(os.getenv("CODEX_RETRY_MARGIN_SECONDS", "300")),
        ),
        workspace_root=workspace_root,
        allowed_directories=parse_path_list(os.getenv("ALLOWED_ADDITIONAL_DIRECTORIES", "")),
    )
