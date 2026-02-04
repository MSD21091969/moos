"""VectorDB Server configuration."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""
    
    host: str = "0.0.0.0"
    port: int = 8002
    debug: bool = True
    
    # ChromaDB
    chroma_persist_dir: str = "./chroma_data"
    
    # CORS
    cors_origins: list[str] = ["http://localhost:8000", "http://localhost:3000"]
    
    class Config:
        env_prefix = "VECTORDB_"
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
