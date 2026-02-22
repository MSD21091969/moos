"""Unit tests for the in-memory SessionStore."""

from __future__ import annotations

import time

import pytest
from src.core.session_store import SessionStore


@pytest.fixture
def store() -> SessionStore:
    """Fresh SessionStore for each test."""
    return SessionStore()


def test_create_returns_string_session_id(store: SessionStore):
    sid = store.create("prompt", [])
    assert isinstance(sid, str)
    assert len(sid) == 36  # UUID format


def test_create_stores_session(store: SessionStore):
    sid = store.create("my prompt", [{"tool": "a"}])
    entry = store.get(sid)
    assert entry is not None
    assert entry["system_prompt"] == "my prompt"
    assert entry["tool_schemas"] == [{"tool": "a"}]


def test_get_returns_none_for_unknown(store: SessionStore):
    assert store.get("nonexistent-id") is None


def test_get_returns_none_after_ttl_expiry(store: SessionStore):
    sid = store.create_with_ttl("p", [], ttl_seconds=0)
    time.sleep(0.01)
    assert store.get(sid) is None


def test_create_with_ttl_respects_custom_ttl(store: SessionStore):
    sid = store.create_with_ttl("p", [], ttl_seconds=3600)
    entry = store.get(sid)
    assert entry is not None
    assert entry["ttl_seconds"] == 3600


def test_create_with_ttl_stores_extra_metadata(store: SessionStore):
    sid = store.create_with_ttl(
        "p", [], ttl_seconds=3600, extra={"app_id": "abc", "is_root": True}
    )
    entry = store.get(sid)
    assert entry is not None
    assert entry["app_id"] == "abc"
    assert entry["is_root"] is True


def test_create_multiple_sessions_all_retrievable(store: SessionStore):
    ids = [store.create(f"prompt-{i}", []) for i in range(5)]
    for i, sid in enumerate(ids):
        entry = store.get(sid)
        assert entry is not None
        assert entry["system_prompt"] == f"prompt-{i}"


def test_purge_expired_removes_stale_sessions(store: SessionStore):
    # Create an expired session directly by manipulating created_at
    sid = store.create_with_ttl("stale", [], ttl_seconds=1)
    entry = store._sessions[sid]
    entry["created_at"] = time.time() - 10  # force-expire

    # Creating a new session triggers purge
    store.create("fresh", [])

    # Expired session is gone
    assert store.get(sid) is None


def test_session_ids_are_unique(store: SessionStore):
    ids = {store.create("p", []) for _ in range(100)}
    assert len(ids) == 100


def test_root_session_ttl_is_24h(store: SessionStore):
    """Root sessions use 24-hour TTL."""
    sid = store.create_with_ttl("root prompt", [], ttl_seconds=24 * 3600)
    entry = store.get(sid)
    assert entry["ttl_seconds"] == 24 * 3600
