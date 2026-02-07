"""Tests for Firebase authentication module."""

import pytest
from unittest.mock import patch, AsyncMock

from src.firebase_auth import (
    verify_firebase_token,
    FirebaseUser,
    AuthError,
    is_firebase_enabled,
)


class TestFirebaseUserFromDevToken:
    """Test FirebaseUser.from_dev_token method."""

    def test_creates_user_from_email(self):
        user = FirebaseUser.from_dev_token("test@example.com")

        assert user.uid == "dev_test_example_com"
        assert user.email == "test@example.com"
        assert user.email_verified is True
        assert user.name == "test"

    def test_creates_user_from_simple_token(self):
        user = FirebaseUser.from_dev_token("testuser")

        assert user.uid == "dev_testuser"
        assert user.email == "testuser"
        assert user.name == "testuser"


class TestFirebaseUserFromDecodedToken:
    """Test FirebaseUser.from_decoded_token method."""

    def test_creates_user_from_full_token(self):
        decoded = {
            "uid": "firebase123",
            "email": "user@example.com",
            "email_verified": True,
            "name": "Test User",
            "picture": "https://example.com/avatar.png",
        }

        user = FirebaseUser.from_decoded_token(decoded)

        assert user.uid == "firebase123"
        assert user.email == "user@example.com"
        assert user.email_verified is True
        assert user.name == "Test User"
        assert user.picture == "https://example.com/avatar.png"

    def test_handles_minimal_token(self):
        decoded = {"uid": "minimal123"}

        user = FirebaseUser.from_decoded_token(decoded)

        assert user.uid == "minimal123"
        assert user.email is None
        assert user.email_verified is False


class TestVerifyFirebaseToken:
    """Test verify_firebase_token function."""

    @pytest.mark.asyncio
    async def test_dev_mode_accepts_email_as_token(self):
        """In dev mode (firebase_auth_enabled=False), email is accepted as token."""
        with patch("src.firebase_auth.get_settings") as mock_settings:
            mock_settings.return_value.firebase_auth_enabled = False

            user = await verify_firebase_token("dev@test.com")

            assert user.email == "dev@test.com"
            assert user.uid.startswith("dev_")

    @pytest.mark.asyncio
    async def test_dev_mode_rejects_short_token(self):
        """Dev mode rejects tokens shorter than 3 characters."""
        with patch("src.firebase_auth.get_settings") as mock_settings:
            mock_settings.return_value.firebase_auth_enabled = False

            with pytest.raises(AuthError) as exc_info:
                await verify_firebase_token("ab")

            assert exc_info.value.code == "invalid_token"

    @pytest.mark.asyncio
    async def test_dev_mode_rejects_empty_token(self):
        """Dev mode rejects empty tokens."""
        with patch("src.firebase_auth.get_settings") as mock_settings:
            mock_settings.return_value.firebase_auth_enabled = False

            with pytest.raises(AuthError) as exc_info:
                await verify_firebase_token("")

            assert exc_info.value.code == "invalid_token"


class TestIsFirebaseEnabled:
    """Test is_firebase_enabled function."""

    def test_returns_false_when_disabled(self):
        with patch("src.firebase_auth.get_settings") as mock_settings:
            mock_settings.return_value.firebase_auth_enabled = False

            assert is_firebase_enabled() is False
