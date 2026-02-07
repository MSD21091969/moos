"""Unit tests for OAuthManager.

Tests OAuth credential management in src/core/oauth_manager.py.
"""

from unittest.mock import MagicMock

import pytest
from google.oauth2.credentials import Credentials

from src.core.oauth_manager import OAuthManager
from src.persistence.mock_firestore import MockFirestoreClient


@pytest.fixture
def mock_firestore():
    """Mock Firestore client."""
    return MockFirestoreClient()


@pytest.fixture
def oauth_manager(mock_firestore):
    """OAuthManager with mock Firestore."""
    return OAuthManager(mock_firestore)


@pytest.fixture
def mock_credentials():
    """Mock Google OAuth credentials."""
    creds = MagicMock(spec=Credentials)
    creds.token = "access_token_123"
    creds.refresh_token = "refresh_token_456"
    creds.token_uri = "https://oauth2.googleapis.com/token"
    creds.client_id = "client_id"
    creds.client_secret = "client_secret"
    creds.scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds.expiry = None
    creds.valid = True
    creds.expired = False
    return creds


class TestStoreToken:
    """Tests for store_token()"""

    @pytest.mark.asyncio
    async def test_store_token_new(self, oauth_manager, mock_credentials):
        """
        TEST: Store token creates new document
        PURPOSE: Verify token storage
        VALIDATES: Firestore document created
        EXPECTED: Token saved and retrievable
        """
        user_id = "test_user_oauth_new"
        provider = "google"

        await oauth_manager.store_token(user_id, provider, mock_credentials)

        # Verify stored
        creds = await oauth_manager.get_credentials(user_id, provider)
        assert creds is not None
        assert creds.token == "access_token_123"
        assert creds.refresh_token == "refresh_token_456"

    @pytest.mark.asyncio
    async def test_store_token_update(self, oauth_manager, mock_credentials):
        """
        TEST: Store token updates existing document
        PURPOSE: Verify token refresh
        VALIDATES: Existing token overwritten
        EXPECTED: New token replaces old
        """
        user_id = "test_user_oauth_update"
        provider = "google"

        # Store initial token
        old_creds = MagicMock(spec=Credentials)
        old_creds.token = "old_token"
        old_creds.refresh_token = "old_refresh"
        old_creds.token_uri = "https://oauth2.googleapis.com/token"
        old_creds.client_id = "client_id"
        old_creds.client_secret = "client_secret"
        old_creds.scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        old_creds.expiry = None

        await oauth_manager.store_token(user_id, provider, old_creds)

        # Update with new token
        await oauth_manager.store_token(user_id, provider, mock_credentials)

        # Verify new token stored
        creds = await oauth_manager.get_credentials(user_id, provider)
        assert creds.token == "access_token_123"
        assert creds.token != "old_token"


class TestGetCredentials:
    """Tests for get_credentials()"""

    @pytest.mark.asyncio
    async def test_get_credentials_exists(self, oauth_manager, mock_credentials):
        """
        TEST: Get credentials returns stored credentials
        PURPOSE: Verify credential retrieval
        VALIDATES: Credentials reconstructed from Firestore
        EXPECTED: Valid Credentials object
        """
        user_id = "test_user_oauth_get"
        provider = "google"

        # Store first
        await oauth_manager.store_token(user_id, provider, mock_credentials)

        # Retrieve
        creds = await oauth_manager.get_credentials(user_id, provider)

        assert creds is not None
        assert creds.token == "access_token_123"
        assert creds.refresh_token == "refresh_token_456"

    @pytest.mark.asyncio
    async def test_get_credentials_not_found(self, oauth_manager):
        """
        TEST: Get credentials returns None when not found
        PURPOSE: Verify handling of missing credentials
        VALIDATES: None returned for new user
        EXPECTED: No exception, returns None
        """
        user_id = "new_user_no_oauth"
        provider = "google"

        creds = await oauth_manager.get_credentials(user_id, provider)

        assert creds is None


class TestRevokeToken:
    """Tests for revoke_token()"""

    @pytest.mark.asyncio
    async def test_revoke_token_success(self, oauth_manager, mock_credentials):
        """
        TEST: Revoke token deletes document
        PURPOSE: Verify token removal
        VALIDATES: Firestore document deleted
        EXPECTED: Token no longer retrievable
        """
        user_id = "test_user_oauth_revoke"
        provider = "google"

        # Store token first
        await oauth_manager.store_token(user_id, provider, mock_credentials)

        # Verify exists
        creds = await oauth_manager.get_credentials(user_id, provider)
        assert creds is not None

        # Revoke
        await oauth_manager.revoke_token(user_id, provider)

        # Verify deleted
        creds = await oauth_manager.get_credentials(user_id, provider)
        assert creds is None

    @pytest.mark.asyncio
    async def test_revoke_token_not_exists(self, oauth_manager):
        """
        TEST: Revoke token handles non-existent user
        PURPOSE: Verify graceful handling of missing credentials
        VALIDATES: No exception raised
        EXPECTED: Completes without error
        """
        user_id = "user_never_oauth_connected"
        provider = "google"

        # Should not raise exception
        await oauth_manager.revoke_token(user_id, provider)
