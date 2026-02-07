"""
TEST: src/services/auth_service.py - Authentication service
PURPOSE: Validate password hashing, JWT token creation, and user authentication
VALIDATES: Password verification, token creation, hardcoded test user auth
EXPECTED: Secure password handling, valid JWT tokens, successful authentication
"""

from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from jose import jwt

from src.core.config import settings
from src.services.auth_service import AuthService


class TestAuthService:
    """Test suite for AuthService."""

    @pytest.fixture
    def auth_service(self):
        """Create AuthService instance with mock firestore."""
        mock_firestore = MagicMock()
        service = AuthService(firestore=mock_firestore)

        # Create a proper mock document with the test password hash
        async def mock_stream():
            mock_doc = MagicMock()
            mock_doc.to_dict.return_value = {
                "user_id": "user_dev_mock_123456",
                "email": "test@test.com",
                "display_name": "Test User",
                "tier": "pro",
                "hashed_password": service.test_password_hash,  # Use the instance's test password hash
            }
            yield mock_doc

        # Mock the query chain
        mock_query = MagicMock()
        mock_query.stream = mock_stream
        mock_users_ref = MagicMock()
        mock_users_ref.where.return_value.limit.return_value = mock_query
        mock_firestore.collection.return_value = mock_users_ref

        return service

    def test_password_hashing(self, auth_service):
        """
        TEST: Hash password with bcrypt
        PURPOSE: Validate password hashing generates unique hashes
        VALIDATES: get_password_hash() produces bcrypt-compatible hash
        EXPECTED: Hash is different from plain text, verifiable
        """
        password = "test_password_123"
        hashed = auth_service.get_password_hash(password)

        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt prefix
        assert auth_service.verify_password(password, hashed)

    def test_password_verification_success(self, auth_service):
        """
        TEST: Verify correct password against hash
        PURPOSE: Validate successful password verification
        VALIDATES: verify_password() returns True for matching password
        EXPECTED: Correct password passes verification
        """
        password = "correct_password"
        hashed = auth_service.get_password_hash(password)

        assert auth_service.verify_password(password, hashed) is True

    def test_password_verification_failure(self, auth_service):
        """
        TEST: Verify incorrect password against hash
        PURPOSE: Validate failed password verification
        VALIDATES: verify_password() returns False for wrong password
        EXPECTED: Incorrect password fails verification
        """
        password = "correct_password"
        hashed = auth_service.get_password_hash(password)

        assert auth_service.verify_password("wrong_password", hashed) is False

    def test_password_truncation_72_bytes(self, auth_service):
        """
        TEST: Password truncation to 72 bytes (bcrypt limit)
        PURPOSE: Validate bcrypt 72-byte password limit enforced
        VALIDATES: Passwords longer than 72 bytes are truncated
        EXPECTED: Only first 72 bytes used for hashing
        """
        # Create password longer than 72 bytes
        long_password = "a" * 100
        hashed = auth_service.get_password_hash(long_password)

        # Verify with first 72 bytes only
        truncated = "a" * 72
        assert auth_service.verify_password(truncated, hashed) is True

        # Verify full password also works (gets truncated internally)
        assert auth_service.verify_password(long_password, hashed) is True

    def test_create_access_token_default_expiration(self, auth_service):
        """
        TEST: Create JWT token with default expiration
        PURPOSE: Validate token creation with default settings
        VALIDATES: create_access_token() produces valid JWT
        EXPECTED: Token contains user data and default expiration
        """
        data = {"sub": "user_123", "tier": "pro"}
        token = auth_service.create_access_token(data)

        # Decode token
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        assert decoded["sub"] == "user_123"
        assert decoded["tier"] == "pro"
        assert "exp" in decoded

    def test_create_access_token_custom_expiration(self, auth_service):
        """
        TEST: Create JWT token with custom expiration
        PURPOSE: Validate token creation with custom expiration time
        VALIDATES: expires_delta parameter sets custom expiration
        EXPECTED: Token expires at specified delta
        """
        data = {"sub": "user_456"}
        custom_delta = timedelta(minutes=5)
        token = auth_service.create_access_token(data, expires_delta=custom_delta)

        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        assert decoded["sub"] == "user_456"
        assert "exp" in decoded

    def test_create_access_token_preserves_data(self, auth_service):
        """
        TEST: Token creation preserves all user data
        PURPOSE: Validate token contains all provided data fields
        VALIDATES: Original data dict not modified, all fields in token
        EXPECTED: Token contains all user data without modification
        """
        data = {
            "sub": "user_789",
            "tier": "enterprise",
            "permissions": ["read", "write"],
            "email": "test@test.com",
        }
        token = auth_service.create_access_token(data)

        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        assert decoded["sub"] == "user_789"
        assert decoded["tier"] == "enterprise"
        assert decoded["permissions"] == ["read", "write"]
        assert decoded["email"] == "test@test.com"

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service):
        """
        TEST: Authenticate test user with correct credentials
        PURPOSE: Validate hardcoded test user authentication
        VALIDATES: authenticate_user() returns UserInDB for correct credentials
        EXPECTED: UserInDB with user_id, email, tier
        """
        user = await auth_service.authenticate_user("test@test.com", "test123")

        assert user is not None
        assert user.user_id == "user_dev_mock_123456"
        assert user.email == "test@test.com"
        assert user.tier == "pro"

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, auth_service):
        """
        TEST: Authenticate with wrong password
        PURPOSE: Validate authentication failure with incorrect password
        VALIDATES: authenticate_user() returns None for wrong password
        EXPECTED: None returned for invalid credentials
        """
        user = await auth_service.authenticate_user("test@test.com", "wrong_password")

        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_unknown_user(self, auth_service):
        """
        TEST: Authenticate unknown user
        PURPOSE: Validate authentication failure for non-existent user
        VALIDATES: authenticate_user() returns None for unknown email
        EXPECTED: None returned for unknown user
        """
        user = await auth_service.authenticate_user("unknown@test.com", "test")

        assert user is None

    def test_password_hash_uniqueness(self, auth_service):
        """
        TEST: Same password generates different hashes (salt)
        PURPOSE: Validate bcrypt salt produces unique hashes
        VALIDATES: Multiple hashes of same password are different
        EXPECTED: Different hashes, all verify correctly
        """
        password = "same_password"
        hash1 = auth_service.get_password_hash(password)
        hash2 = auth_service.get_password_hash(password)

        # Different hashes due to random salt
        assert hash1 != hash2

        # Both verify correctly
        assert auth_service.verify_password(password, hash1)
        assert auth_service.verify_password(password, hash2)
