import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    telegram_bot_token: str = ""
    telegram_admin_id: int = 0
    gemini_api_key: str = ""
    default_model: str = "gemini-3.7-flash"
    default_workspace_path: str = str(BASE_DIR)
    host: str = "0.0.0.0"
    port: int = 8000
    confirm_mode: bool = False
    webapp_url: str = ""
    db_path: str = str(BASE_DIR / "data" / "bot.db")
    agy_bin_path: str = ""
    system_context_hint: str = ""
    trusted_proxies: str = "127.0.0.1,::1"
    google_client_id: str = ""
    google_client_secret: str = ""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
