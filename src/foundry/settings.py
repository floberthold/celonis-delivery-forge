from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Celonis Delivery Forge"
    env: str = "dev"
    database_url: str = "sqlite:///./foundry.db"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 720
    celonis_api_token: str = ""
    celonis_timeout_seconds: int = 20

    model_config = SettingsConfigDict(env_file=".env", env_prefix="FORGE_", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
