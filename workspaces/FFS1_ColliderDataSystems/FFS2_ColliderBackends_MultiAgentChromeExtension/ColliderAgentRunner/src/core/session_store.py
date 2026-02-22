"""In-memory session store — caches composed agent contexts by session_id."""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

_TTL_SECONDS = 4 * 3600  # 4 hours default


class SessionStore:
    """Maps session_id → composed agent context dict.

    Context dict shape::

        {
            "system_prompt": str,
            "tool_schemas": list[dict],
            "created_at": float,  # unix timestamp
        }

    TTL is 4 hours. Expired entries are purged on every ``create()`` call.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}

    def create(self, system_prompt: str, tool_schemas: list[dict[str, Any]]) -> str:
        """Store a composed context and return its session_id.

        Args:
            system_prompt: Fully built system prompt string.
            tool_schemas: List of AgentToolSchema-compatible dicts.

        Returns:
            A new UUID session_id string.
        """
        return self.create_with_ttl(system_prompt, tool_schemas, _TTL_SECONDS)

    def create_with_ttl(
        self,
        system_prompt: str,
        tool_schemas: list[dict[str, Any]],
        ttl_seconds: int = _TTL_SECONDS,
        extra: dict[str, Any] | None = None,
    ) -> str:
        """Store a composed context with a custom TTL and return its session_id.

        Args:
            system_prompt: Fully built system prompt string.
            tool_schemas: List of AgentToolSchema-compatible dicts.
            ttl_seconds: Session lifetime in seconds (default 4h).
            extra: Optional extra metadata stored alongside the session.

        Returns:
            A new UUID session_id string.
        """
        self._purge_expired()
        session_id = str(uuid4())
        entry: dict[str, Any] = {
            "system_prompt": system_prompt,
            "tool_schemas": tool_schemas,
            "created_at": time.time(),
            "ttl_seconds": ttl_seconds,
        }
        if extra:
            entry.update(extra)
        self._sessions[session_id] = entry
        return session_id

    def get(self, session_id: str) -> dict[str, Any] | None:
        """Return the session context dict or None if not found / expired.

        Args:
            session_id: The UUID returned by ``create()`` or ``create_with_ttl()``.

        Returns:
            Session context dict or None.
        """
        entry = self._sessions.get(session_id)
        if entry is None:
            return None
        ttl = entry.get("ttl_seconds", _TTL_SECONDS)
        if time.time() - entry["created_at"] > ttl:
            del self._sessions[session_id]
            return None
        return entry

    def _purge_expired(self) -> None:
        now = time.time()
        expired = [
            sid
            for sid, entry in self._sessions.items()
            if now - entry["created_at"] > entry.get("ttl_seconds", _TTL_SECONDS)
        ]
        for sid in expired:
            del self._sessions[sid]


# Module-level singleton
session_store = SessionStore()
