"""Secret management with Cloud Secret Manager integration."""

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from google.cloud import secretmanager

try:
    from google.cloud import secretmanager  # type: ignore[import-not-found]

    SECRETMANAGER_AVAILABLE = True
except ImportError:  # pragma: no cover
    SECRETMANAGER_AVAILABLE = False
    secretmanager = None  # type: ignore[assignment]


class SecretManager:
    """Manages secrets from environment or GCP Secret Manager.

    Falls back to environment variables if Secret Manager unavailable.
    """

    def __init__(self, project_id: str | None = None):
        """Initialize Secret Manager client.

        Args:
            project_id: GCP project ID. If None, uses GCP_PROJECT env var.
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT")
        self.use_secret_manager = (
            SECRETMANAGER_AVAILABLE
            and self.project_id is not None
            and os.getenv("USE_SECRET_MANAGER", "false").lower() == "true"
        )

        if self.use_secret_manager:
            self.client = secretmanager.SecretManagerServiceClient()  # type: ignore[union-attr]
        else:
            self.client = None

    def get_secret(self, secret_name: str, version: str = "latest") -> str | None:
        """Retrieve secret value from Secret Manager or environment.

        Args:
            secret_name: Name of secret (e.g., 'OPENAI_API_KEY')
            version: Secret version (default: 'latest')

        Returns:
            Secret value or None if not found

        Priority:
        1. Environment variable (always checked first)
        2. GCP Secret Manager (if enabled)
        3. None
        """
        # Always check environment first (for local dev)
        env_value = os.getenv(secret_name)
        if env_value:
            return env_value

        # Fall back to Secret Manager in production
        if not self.use_secret_manager:
            return None

        try:
            name = f"projects/{self.project_id}/secrets/{secret_name}/versions/{version}"
            response = self.client.access_secret_version(request={"name": name})  # type: ignore[union-attr]
            return response.payload.data.decode("UTF-8")
        except Exception:  # pragma: no cover
            # Secret not found or access denied - return None
            return None

    def get_required_secret(self, secret_name: str, version: str = "latest") -> str:
        """Get secret value or raise if not found.

        Args:
            secret_name: Name of secret
            version: Secret version (default: 'latest')

        Returns:
            Secret value

        Raises:
            ValueError: If secret not found in environment or Secret Manager
        """
        value = self.get_secret(secret_name, version)
        if value is None:
            raise ValueError(
                f"Required secret '{secret_name}' not found in environment or Secret Manager"
            )
        return value


# Global instance initialized on first import
_secret_manager: SecretManager | None = None


def get_secret_manager() -> SecretManager:
    """Get or create global SecretManager instance."""
    global _secret_manager
    if _secret_manager is None:
        _secret_manager = SecretManager()
    return _secret_manager
