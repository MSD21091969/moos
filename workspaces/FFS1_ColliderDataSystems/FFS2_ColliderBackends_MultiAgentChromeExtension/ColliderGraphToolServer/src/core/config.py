from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_env_file() -> Path:
    current = Path(__file__).resolve().parent
    for _ in range(10):
        candidate = current / ".env"
        if candidate.exists():
            return candidate
        current = current.parent
    return Path(".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GRAPHTOOL_",
        env_file=str(_find_env_file()),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    port: int = 8001
    default_model: str = "gemini:gemini-3.1-pro"
    vectordb_url: str = "http://localhost:8002"


settings = Settings()
