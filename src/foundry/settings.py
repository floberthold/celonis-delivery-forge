from functools import lru_cache
import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_local_database_url() -> str:
    local_app_data = os.getenv("LOCALAPPDATA")
    if not local_app_data:
        local_app_data = str(Path.home() / "AppData" / "Local")

    database_path = Path(local_app_data) / "CelonisDeliveryForge" / "foundry-local.db"
    database_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{database_path.as_posix()}"


class Settings(BaseSettings):
    app_name: str = "Celonis Delivery Forge"
    env: str = "dev"
    database_url: str = "sqlite:///./foundry.db"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 720
    celonis_api_token: str = ""
    celonis_timeout_seconds: int = 20
    gitlab_base_url: str = ""
    gitlab_api_token: str = ""
    uploads_dir: str = "./uploads"
    public_base_url: str = ""
    delivery_file_max_upload_bytes: int = 25 * 1024 * 1024
    local_database_url: str = _default_local_database_url()
    database_fallback_to_local: bool = True
    database_connect_timeout_seconds: int = 5
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_starttls: bool = True
    smtp_use_ssl: bool = False
    registration_token_expire_minutes: int = 60
    password_reset_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_prefix="FORGE_", extra="ignore")

    def allows_local_database_fallback(self) -> bool:
        return self.database_fallback_to_local and self.env.lower() in {"dev", "local"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
