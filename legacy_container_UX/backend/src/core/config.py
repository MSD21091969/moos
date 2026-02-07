"""Application configuration using Pydantic Settings."""

import os
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    app_title: str = "Collider API"
    app_version: str = "2026.1.0"
    app_description: str = "Context-centric AI tool execution platform"
    environment: Literal["development", "staging", "production", "test"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    debug: bool = True

    # Server
    host: str = "127.0.0.1"
    port: int = 8000

    # Firestore
    gcp_project: str | None = Field(default=None, validation_alias="GCP_PROJECT")
    firestore_database: str = "my-tiny-data-collider"  # Firestore database name
    use_firestore_mocks: bool = True

    # Google Cloud Storage
    gcs_bucket_name: str = Field(
        default="my-tiny-data-collider-files",
        validation_alias="GCS_BUCKET_NAME",
    )

    # Secret Management
    use_secret_manager: bool = False  # Enable in production Cloud Run

    # Authentication (Phase 2)
    skip_auth_for_testing: bool = False  # Allow bypassing JWT validation in tests
    SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production-12345678901234567890",
        validation_alias="JWT_SECRET_KEY",  # Accept JWT_SECRET_KEY from env
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    @property
    def JWT_SECRET_KEY(self) -> str:
        """Alias for SECRET_KEY for backward compatibility."""
        return self.SECRET_KEY

    @property
    def JWT_ALGORITHM(self) -> str:
        """Alias for ALGORITHM for backward compatibility."""
        return self.ALGORITHM

    @property
    def JWT_EXPIRATION_SECONDS(self) -> int:
        """JWT expiration in seconds (calculated from minutes)."""
        return self.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    # CORS - Updated for separate frontend deployment
    allowed_origins: list[str] = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8000",  # Backend (for legacy dashboards)
        "https://*.vercel.app",  # Vercel preview deployments
        "https://*.netlify.app",  # Netlify deployments (if used)
    ]

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50  # Increased for concurrent workloads
    REDIS_DEFAULT_TTL: int = 300  # 5 minutes

    # Google OAuth (for Workspace APIs)
    google_oauth_client_id: str = Field(default="", validation_alias="GOOGLE_OAUTH_CLIENT_ID")
    google_oauth_client_secret: str = Field(
        default="", validation_alias="GOOGLE_OAUTH_CLIENT_SECRET"
    )
    google_oauth_redirect_uri: str = Field(
        default="http://localhost:8000/oauth/callback", validation_alias="GOOGLE_OAUTH_REDIRECT_URI"
    )

    # Database connection pooling (performance tuning)
    DATABASE_POOL_SIZE: int = 20  # Max concurrent connections
    DATABASE_POOL_RECYCLE: int = 3600  # Recycle connections every 1 hour
    DATABASE_POOL_TIMEOUT: int = 30  # Connection timeout in seconds

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def docs_enabled(self) -> bool:
        return not self.is_production

    def get_api_key(self, service: str) -> str | None:
        """Get API key from environment or Secret Manager.

        Args:
            service: Service name (e.g., 'openai', 'google', 'logfire')

        Returns:
            API key or None if not configured

        In production with Secret Manager enabled, retrieves from GCP.
        Otherwise uses environment variables.
        """
        env_var = f"{service.upper()}_API_KEY"

        # Check environment first (always works for local dev)
        api_key = os.getenv(env_var)
        if api_key:
            return api_key

        # Use Secret Manager in production if enabled
        if self.use_secret_manager and self.gcp_project:
            from src.core.secrets import get_secret_manager

            sm = get_secret_manager()
            return sm.get_secret(env_var)

        return None


settings = Settings()
