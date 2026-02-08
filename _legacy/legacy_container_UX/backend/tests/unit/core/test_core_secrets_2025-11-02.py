"""Unit tests for src/core/secrets.py

TEST: Secret management
PURPOSE: Validate GCP Secret Manager integration
VALIDATES: SecretManager, get_secret, get_required_secret
EXPECTED: Secrets retrieved from env or GCP
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from src.core.secrets import SecretManager, get_secret_manager, SECRETMANAGER_AVAILABLE


class TestSecretManager:
    """Test SecretManager class."""

    def test_secret_manager_initialization_without_gcp(self):
        """
        TEST: Initialize without Secret Manager
        PURPOSE: Verify env-only fallback
        VALIDATES: Client not created
        EXPECTED: use_secret_manager = False
        """
        with patch.dict(os.environ, {}, clear=True):
            manager = SecretManager()

            assert manager.use_secret_manager is False
            assert manager.client is None

    def test_get_secret_from_environment(self):
        """
        TEST: Get secret from environment
        PURPOSE: Verify env var retrieval
        VALIDATES: Secret returned from env
        EXPECTED: Env value returned
        """
        with patch.dict(os.environ, {"TEST_SECRET": "env_value"}):
            manager = SecretManager()

            result = manager.get_secret("TEST_SECRET")

            assert result == "env_value"

    def test_get_secret_returns_none_if_not_found(self):
        """
        TEST: Get non-existent secret
        PURPOSE: Verify None handling
        VALIDATES: None returned
        EXPECTED: No exception
        """
        with patch.dict(os.environ, {}, clear=True):
            manager = SecretManager()

            result = manager.get_secret("NONEXISTENT_SECRET")

            assert result is None

    @pytest.mark.skipif(
        not SECRETMANAGER_AVAILABLE, reason="google-cloud-secretmanager not installed"
    )
    def test_get_secret_from_gcp_secret_manager(self):
        """
        TEST: Get secret from GCP Secret Manager
        PURPOSE: Verify GCP integration
        VALIDATES: Secret retrieved from GCP
        EXPECTED: Secret value returned
        """
        with patch.dict(os.environ, {"GCP_PROJECT": "test-project", "USE_SECRET_MANAGER": "true"}):
            with patch("src.core.secrets.secretmanager.SecretManagerServiceClient") as MockClient:
                # Mock Secret Manager response
                mock_response = MagicMock()
                mock_response.payload.data = b"gcp_secret_value"
                MockClient.return_value.access_secret_version.return_value = mock_response

                manager = SecretManager(project_id="test-project")
                result = manager.get_secret("API_KEY")

                assert result == "gcp_secret_value"

    def test_get_required_secret_success(self):
        """
        TEST: Get required secret
        PURPOSE: Verify required secret retrieval
        VALIDATES: Secret returned
        EXPECTED: No exception
        """
        with patch.dict(os.environ, {"REQUIRED_SECRET": "value"}):
            manager = SecretManager()

            result = manager.get_required_secret("REQUIRED_SECRET")

            assert result == "value"

    def test_get_required_secret_raises_if_missing(self):
        """
        TEST: Required secret missing
        PURPOSE: Verify error on missing secret
        VALIDATES: ValueError raised
        EXPECTED: Exception with message
        """
        with patch.dict(os.environ, {}, clear=True):
            manager = SecretManager()

            with pytest.raises(ValueError) as exc_info:
                manager.get_required_secret("MISSING_SECRET")

            assert "not found" in str(exc_info.value)


class TestGetSecretManager:
    """Test get_secret_manager singleton."""

    def test_get_secret_manager_returns_singleton(self):
        """
        TEST: Get secret manager singleton
        PURPOSE: Verify global instance
        VALIDATES: Same instance returned
        EXPECTED: Singleton pattern
        """
        manager1 = get_secret_manager()
        manager2 = get_secret_manager()

        assert manager1 is manager2
