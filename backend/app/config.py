from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Load validated backend configuration from environment variables."""

    app_name: str = "4by4 College Management API"
    environment: str = "development"
    database_url: str
    runtime_database_url: str
    secret_key: str = Field(default="development-only-change-me-at-least-32-bytes", min_length=32)
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    demo_seed_password: str | None = None
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"
    media_storage_path: str = "var/media"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide validated application settings."""

    return Settings()


settings = get_settings()
