"""Collider Data Server configuration."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/collider"

    # CORS - allow all origins in dev mode (chrome extensions need dynamic matching)
    cors_origins: list[str] = ["*"]

    # Firebase Auth
    firebase_credentials_path: str | None = None  # Path to service account JSON
    firebase_project_id: str | None = None
    firebase_auth_enabled: bool = False  # Set True in production

    class Config:
        env_prefix = "COLLIDER_"
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields from .env


@lru_cache
def get_settings() -> Settings:
    return Settings()
