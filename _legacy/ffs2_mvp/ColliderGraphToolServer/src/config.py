"""GraphTool Server configuration."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""
    
    host: str = "0.0.0.0"
    port: int = 8001
    debug: bool = True
    
    # LLM
    default_model: str = "gemini:gemini-2.0-flash"
    
    # VectorDB Server
    vectordb_url: str = "http://localhost:8002"
    
    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "chrome-extension://*"]
    
    class Config:
        env_prefix = "GRAPHTOOL_"
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
