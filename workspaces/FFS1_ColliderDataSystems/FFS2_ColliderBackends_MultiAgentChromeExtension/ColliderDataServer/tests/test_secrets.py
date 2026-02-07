"""Tests for secret injection module."""

import pytest
import os

from src.secrets import (
    inject_secrets,
    EnvironmentSecretStore,
    get_required_secrets,
    mask_secrets,
)


class TestEnvironmentSecretStore:
    """Test EnvironmentSecretStore."""

    @pytest.fixture
    def store(self):
        return EnvironmentSecretStore()

    @pytest.fixture(autouse=True)
    def cleanup_env(self):
        """Clean up test environment variables after each test."""
        yield
        # Remove test env vars
        for key in list(os.environ.keys()):
            if key.startswith("COLLIDER_SECRET_TEST_"):
                del os.environ[key]

    @pytest.mark.asyncio
    async def test_get_returns_none_for_missing(self, store):
        result = await store.get("nonexistent", scope="test")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_and_get(self, store):
        await store.set("mykey", "myvalue", scope="test")

        result = await store.get("mykey", scope="test")

        assert result == "myvalue"

    @pytest.mark.asyncio
    async def test_delete(self, store):
        await store.set("todelete", "value", scope="test")
        await store.delete("todelete", scope="test")

        result = await store.get("todelete", scope="test")

        assert result is None

    @pytest.mark.asyncio
    async def test_list(self, store):
        await store.set("key1", "val1", scope="test")
        await store.set("key2", "val2", scope="test")

        names = await store.list(scope="test")

        assert "key1" in names
        assert "key2" in names


class TestInjectSecrets:
    """Test inject_secrets function."""

    @pytest.fixture
    def store(self):
        return EnvironmentSecretStore()

    @pytest.fixture(autouse=True)
    def setup_secrets(self, store):
        """Set up test secrets."""
        os.environ["COLLIDER_SECRET_APP_TESTAPP_API_KEY"] = "sk-test123"
        os.environ["COLLIDER_SECRET_GLOBAL_SHARED_TOKEN"] = "shared-token"
        yield
        # Cleanup
        for key in [
            "COLLIDER_SECRET_APP_TESTAPP_API_KEY",
            "COLLIDER_SECRET_GLOBAL_SHARED_TOKEN",
        ]:
            if key in os.environ:
                del os.environ[key]

    @pytest.mark.asyncio
    async def test_injects_simple_secret(self, store):
        container = {"config": {"api_key": "${secret:API_KEY}"}}

        result = await inject_secrets(container, app_id="testapp", store=store)

        assert result["config"]["api_key"] == "sk-test123"

    @pytest.mark.asyncio
    async def test_preserves_non_secret_values(self, store):
        container = {
            "name": "test",
            "count": 42,
            "items": ["a", "b"],
        }

        result = await inject_secrets(container, app_id="testapp", store=store)

        assert result["name"] == "test"
        assert result["count"] == 42
        assert result["items"] == ["a", "b"]

    @pytest.mark.asyncio
    async def test_handles_nested_secrets(self, store):
        container = {"level1": {"level2": {"secret": "${secret:API_KEY}"}}}

        result = await inject_secrets(container, app_id="testapp", store=store)

        assert result["level1"]["level2"]["secret"] == "sk-test123"

    @pytest.mark.asyncio
    async def test_handles_secrets_in_lists(self, store):
        container = {"keys": ["${secret:API_KEY}", "static-value"]}

        result = await inject_secrets(container, app_id="testapp", store=store)

        assert result["keys"][0] == "sk-test123"
        assert result["keys"][1] == "static-value"

    @pytest.mark.asyncio
    async def test_missing_secret_returns_placeholder(self, store):
        container = {"key": "${secret:NONEXISTENT}"}

        result = await inject_secrets(container, app_id="testapp", store=store)

        assert "NOT_FOUND" in result["key"]


class TestGetRequiredSecrets:
    """Test get_required_secrets function."""

    @pytest.mark.asyncio
    async def test_finds_all_secret_refs(self):
        container = {
            "api_key": "${secret:OPENAI_KEY}",
            "nested": {"token": "${secret:GITHUB_TOKEN}"},
            "list": ["${secret:OTHER_KEY}"],
        }

        result = await get_required_secrets(container)

        assert set(result) == {"OPENAI_KEY", "GITHUB_TOKEN", "OTHER_KEY"}

    @pytest.mark.asyncio
    async def test_returns_empty_for_no_secrets(self):
        container = {"name": "test", "value": 123}

        result = await get_required_secrets(container)

        assert result == []


class TestMaskSecrets:
    """Test mask_secrets function."""

    def test_masks_secret_references(self):
        text = "Using API key ${secret:API_KEY} for auth"

        result = mask_secrets(text, ["API_KEY"])

        assert "***" in result
        assert "API_KEY" not in result

    def test_preserves_non_secret_text(self):
        text = "Normal text without secrets"

        result = mask_secrets(text, ["API_KEY"])

        assert result == text
