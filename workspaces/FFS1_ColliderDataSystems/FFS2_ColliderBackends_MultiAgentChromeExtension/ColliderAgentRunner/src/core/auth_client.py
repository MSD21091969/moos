"""JWT auth client — logs in to ColliderDataServer and caches tokens per role."""

from __future__ import annotations

import time
from typing import Any

import httpx

from src.core.config import settings

_TOKEN_BUFFER_SECS = 60  # refresh this many seconds before expiry

_ROLE_CREDENTIAL_MAP = {
    "superadmin": ("collider_superadmin_username", "collider_superadmin_password"),
    "collider_admin": ("collider_collider_admin_username", "collider_collider_admin_password"),
    "app_admin": ("collider_app_admin_username", "collider_app_admin_password"),
    "app_user": ("collider_app_user_username", "collider_app_user_password"),
}


class AuthClient:
    """Authenticates to DataServer and maintains valid JWTs per role.

    Usage::

        client = AuthClient()
        token = await client.get_token()              # default credentials
        token = await client.get_token_for_role("app_user")  # role credentials
        user  = client.user                            # last default login user
        user  = client.user_for_role("app_user")       # last role login user
    """

    def __init__(self) -> None:
        # Default (single-role) cache
        self._token: str | None = None
        self._expires_at: float = 0.0
        self._user: dict[str, Any] = {}

        # Per-role cache: role → {token, expires_at, user}
        self._role_cache: dict[str, dict[str, Any]] = {}

    @property
    def user(self) -> dict[str, Any]:
        """Return the last logged-in default user payload."""
        return self._user

    def user_for_role(self, role: str) -> dict[str, Any]:
        """Return the cached user payload for a given role."""
        return self._role_cache.get(role, {}).get("user", {})

    async def get_token(self) -> str:
        """Return the cached default JWT or fetch a fresh one.

        Returns:
            A valid Bearer token string.

        Raises:
            httpx.HTTPStatusError: If login fails.
        """
        if self._token and time.time() < (self._expires_at - _TOKEN_BUFFER_SECS):
            return self._token
        return await self._login(
            settings.collider_username,
            settings.collider_password,
            cache_key=None,
        )

    async def get_token_for_role(self, role: str) -> str:
        """Return a cached JWT for the given role's credentials.

        Falls back to the default credentials if no role-specific credentials
        are configured for the requested role.

        Args:
            role: One of ``superadmin``, ``collider_admin``, ``app_admin``, ``app_user``.

        Returns:
            A valid Bearer token string for that role.

        Raises:
            httpx.HTTPStatusError: If login fails.
        """
        cached = self._role_cache.get(role)
        if cached and time.time() < (cached["expires_at"] - _TOKEN_BUFFER_SECS):
            return cached["token"]

        username, password = self._resolve_credentials(role)
        return await self._login(username, password, cache_key=role)

    def _resolve_credentials(self, role: str) -> tuple[str, str]:
        """Return (username, password) for the given role.

        Uses role-specific credentials from settings if configured, otherwise
        falls back to the default collider_username / collider_password.
        """
        u_field, p_field = _ROLE_CREDENTIAL_MAP.get(
            role, ("collider_username", "collider_password")
        )
        username = getattr(settings, u_field, None) or settings.collider_username
        password = getattr(settings, p_field, None) or settings.collider_password
        return username, password

    async def _login(
        self,
        username: str,
        password: str,
        cache_key: str | None,
    ) -> str:
        """POST /api/v1/auth/login and cache the result.

        Args:
            username: Collider account username.
            password: Collider account password.
            cache_key: If None, stores in the default cache; otherwise
                stores in the per-role cache under this key.

        Returns:
            The access token string.
        """
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.data_server_url}/api/v1/auth/login",
                json={"username": username, "password": password},
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()

        token: str = data["access_token"]
        user: dict[str, Any] = data.get("user", {})
        expires_at = time.time() + 23 * 3600  # 23h (DataServer default 24h)

        if cache_key is None:
            self._token = token
            self._user = user
            self._expires_at = expires_at
        else:
            self._role_cache[cache_key] = {
                "token": token,
                "user": user,
                "expires_at": expires_at,
            }

        return token


# Module-level singleton — shared across request handlers
auth_client = AuthClient()
