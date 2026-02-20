"""Configuration settings for ColliderAgentRunner."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from secrets file + environment.

    Priority (highest first):
      1. Environment variables
      2. D:/FFS0_Factory/secrets/api_keys.env
      3. ../.env (FFS2 shared .env)
      4. .env (local override)
    """

    # LLM
    agent_model: str = "claude-sonnet-4-6"

    # DataServer
    data_server_url: str = "http://localhost:8000"

    # Credentials — required; set in secrets/api_keys.env
    collider_username: str
    collider_password: str
    anthropic_api_key: str

    # Server
    port: int = 8004
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=[
            "D:/FFS0_Factory/secrets/api_keys.env",
            "../.env",
            ".env",
        ],
        env_ignore_empty=True,
        extra="ignore",
    )


settings = Settings()  # type: ignore[call-arg]
