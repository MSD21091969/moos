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
    
    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "chrome-extension://*"]
    
    class Config:
        env_prefix = "COLLIDER_"
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
