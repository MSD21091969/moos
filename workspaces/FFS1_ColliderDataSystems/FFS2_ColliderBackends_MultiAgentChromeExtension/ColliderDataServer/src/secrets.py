"""
Secret Injection System
Securely injects secrets into containers at runtime.

Secrets are stored encrypted in the database and only decrypted
when needed for workflow execution. The system supports:

- Application-level secrets (available to all nodes)
- User-level secrets (per-user API keys, etc.)
- Environment variable fallbacks
- Secret references: ${secret:NAME}
"""

import os
import base64
import logging
from typing import Any
from functools import lru_cache

logger = logging.getLogger(__name__)

# For MVP, we use a simple approach. In production, use:
# - AWS Secrets Manager
# - Azure Key Vault
# - HashiCorp Vault
# - Google Secret Manager

# Encryption key from environment (generate with: openssl rand -base64 32)
_ENCRYPTION_KEY = os.environ.get("COLLIDER_SECRET_KEY", "dev-key-do-not-use-in-prod")


class SecretStore:
    """
    Abstract interface for secret storage.
    Implementations can use database, vault, env vars, etc.
    """

    async def get(self, name: str, scope: str = "app") -> str | None:
        """Get a secret by name and scope."""
        raise NotImplementedError

    async def set(self, name: str, value: str, scope: str = "app") -> None:
        """Set a secret."""
        raise NotImplementedError

    async def delete(self, name: str, scope: str = "app") -> None:
        """Delete a secret."""
        raise NotImplementedError

    async def list(self, scope: str = "app") -> list[str]:
        """List secret names (not values) in a scope."""
        raise NotImplementedError


class EnvironmentSecretStore(SecretStore):
    """
    Simple secret store using environment variables.
    Format: COLLIDER_SECRET_{SCOPE}_{NAME}

    Example:
        COLLIDER_SECRET_APP_OPENAI_API_KEY=sk-...
        COLLIDER_SECRET_USER_123_GITHUB_TOKEN=ghp_...
    """

    def _env_key(self, name: str, scope: str) -> str:
        """Build environment variable name."""
        safe_scope = scope.upper().replace("-", "_")
        safe_name = name.upper().replace("-", "_")
        return f"COLLIDER_SECRET_{safe_scope}_{safe_name}"

    async def get(self, name: str, scope: str = "app") -> str | None:
        return os.environ.get(self._env_key(name, scope))

    async def set(self, name: str, value: str, scope: str = "app") -> None:
        os.environ[self._env_key(name, scope)] = value

    async def delete(self, name: str, scope: str = "app") -> None:
        key = self._env_key(name, scope)
        if key in os.environ:
            del os.environ[key]

    async def list(self, scope: str = "app") -> list[str]:
        prefix = f"COLLIDER_SECRET_{scope.upper().replace('-', '_')}_"
        names = []
        for key in os.environ:
            if key.startswith(prefix):
                name = key[len(prefix) :].lower().replace("_", "-")
                names.append(name)
        return names


class DatabaseSecretStore(SecretStore):
    """
    Secret store using the database with encryption.
    Requires a Secrets table in the database.
    """

    def __init__(self, db_session):
        self.db = db_session

    async def get(self, name: str, scope: str = "app") -> str | None:
        # TODO: Implement with database table
        # For now, fall back to environment
        env_store = EnvironmentSecretStore()
        return await env_store.get(name, scope)

    async def set(self, name: str, value: str, scope: str = "app") -> None:
        # TODO: Implement with encryption
        pass

    async def delete(self, name: str, scope: str = "app") -> None:
        pass

    async def list(self, scope: str = "app") -> list[str]:
        return []


# Default store
_default_store: SecretStore = EnvironmentSecretStore()


def get_secret_store() -> SecretStore:
    """Get the default secret store."""
    return _default_store


async def inject_secrets(
    container: dict,
    app_id: str,
    user_id: str | None = None,
    store: SecretStore | None = None,
) -> dict:
    """
    Inject secrets into a container, replacing ${secret:NAME} references.

    Args:
        container: The container dict with potential secret refs
        app_id: Application ID for app-scoped secrets
        user_id: User ID for user-scoped secrets (optional)
        store: Secret store to use (defaults to environment)

    Returns:
        Container with secrets injected
    """
    if store is None:
        store = get_secret_store()

    return await _inject_recursive(container, app_id, user_id, store)


async def _inject_recursive(
    obj: Any,
    app_id: str,
    user_id: str | None,
    store: SecretStore,
) -> Any:
    """Recursively inject secrets into an object."""

    if isinstance(obj, str):
        if obj.startswith("${secret:") and obj.endswith("}"):
            secret_name = obj[9:-1]
            return await _resolve_secret(secret_name, app_id, user_id, store)
        return obj

    if isinstance(obj, dict):
        return {
            k: await _inject_recursive(v, app_id, user_id, store)
            for k, v in obj.items()
        }

    if isinstance(obj, list):
        return [await _inject_recursive(item, app_id, user_id, store) for item in obj]

    return obj


async def _resolve_secret(
    name: str,
    app_id: str,
    user_id: str | None,
    store: SecretStore,
) -> str:
    """
    Resolve a secret by name.

    Priority:
    1. User-scoped secret (if user_id provided)
    2. App-scoped secret
    3. Global secret
    4. Return placeholder if not found
    """
    # Try user scope first
    if user_id:
        value = await store.get(name, scope=f"user-{user_id}")
        if value:
            return value

    # Try app scope
    value = await store.get(name, scope=f"app-{app_id}")
    if value:
        return value

    # Try global scope
    value = await store.get(name, scope="global")
    if value:
        return value

    # Not found - log warning and return placeholder
    logger.warning(f"Secret not found: {name} (app={app_id}, user={user_id})")
    return f"[SECRET:{name}:NOT_FOUND]"


def mask_secrets(text: str, secret_names: list[str]) -> str:
    """
    Mask known secrets in text for logging.

    Args:
        text: Text that may contain secrets
        secret_names: List of secret names to look for

    Returns:
        Text with secrets masked as ***
    """
    result = text
    # This is a simple implementation - in production, track actual values
    for name in secret_names:
        # Mask common patterns
        patterns = [
            f"${{{name}}}",
            f"${{secret:{name}}}",
        ]
        for pattern in patterns:
            result = result.replace(pattern, "***")
    return result


async def get_required_secrets(container: dict) -> list[str]:
    """
    Get list of secret names required by a container.

    Scans all string values for ${secret:NAME} patterns.
    """
    secrets = set()
    _find_secret_refs(container, secrets)
    return list(secrets)


def _find_secret_refs(obj: Any, refs: set) -> None:
    """Recursively find secret references."""
    if isinstance(obj, str):
        if obj.startswith("${secret:") and obj.endswith("}"):
            refs.add(obj[9:-1])
    elif isinstance(obj, dict):
        for value in obj.values():
            _find_secret_refs(value, refs)
    elif isinstance(obj, list):
        for item in obj:
            _find_secret_refs(item, refs)
