"""JWT auth client — logs in to ColliderDataServer and caches the token."""

from __future__ import annotations

import time
from typing import Any

import httpx

from src.core.config import settings

_TOKEN_BUFFER_SECS = 60  # refresh this many seconds before expiry


class AuthClient:
    """Authenticates to DataServer and maintains a valid JWT.

    Usage::

        client = AuthClient()
        token = await client.get_token()   # cached; refreshes automatically
        user  = client.user                 # {id, username, system_role, ...}
    """

    def __init__(self) -> None:
        self._token: str | None = None
        self._expires_at: float = 0.0
        self._user: dict[str, Any] = {}

    @property
    def user(self) -> dict[str, Any]:
        """Return the last logged-in user payload."""
        return self._user

    async def get_token(self) -> str:
        """Return the cached JWT or fetch a fresh one from DataServer.

        Returns:
            A valid Bearer token string.

        Raises:
            httpx.HTTPStatusError: If login fails.
        """
        if self._token and time.time() < (self._expires_at - _TOKEN_BUFFER_SECS):
            return self._token
        return await self._login()

    async def _login(self) -> str:
        """POST /api/v1/auth/login and cache the result.

        Returns:
            The access token string.
        """
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.data_server_url}/api/v1/auth/login",
                json={
                    "username": settings.collider_username,
                    "password": settings.collider_password,
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()

        self._token = data["access_token"]
        self._user = data.get("user", {})
        # DataServer tokens expire in 24h by default; record issue time + 23h
        self._expires_at = time.time() + 23 * 3600
        return self._token  # type: ignore[return-value]


# Module-level singleton — shared across request handlers
auth_client = AuthClient()
