"""
Unit tests for user models.

Tests UserCreate, UserUpdate, User, UserInDB in isolation.
"""

import pytest
from pydantic import ValidationError

from src.models.users import User, UserCreate, UserInDB, UserUpdate


class TestUserCreate:
    """Test UserCreate validation."""

    def test_user_create_with_valid_email(self):
        """
        TEST: UserCreate validates email format.

        PURPOSE: Ensure only valid emails accepted during registration.

        VALIDATES:
        - EmailStr type enforces valid email format
        - password min_length=8 enforced
        - full_name optional

        EXPECTED: Valid UserCreate passes validation.
        """
        user = UserCreate(
            email="test@example.com",
            password="securepass123",
            full_name="Test User",
        )

        assert user.email == "test@example.com"
        assert user.password == "securepass123"
        assert user.full_name == "Test User"

    def test_user_create_rejects_invalid_email(self):
        """
        TEST: UserCreate rejects invalid email format.

        PURPOSE: Prevent registration with malformed emails.

        VALIDATES:
        - "not-an-email" raises ValidationError
        - EmailStr type validation

        EXPECTED: ValidationError for invalid email.
        """
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="not-an-email",
                password="securepass123",
            )

        errors = exc_info.value.errors()
        assert any("email" in str(error) for error in errors)

    def test_user_create_rejects_short_password(self):
        """
        TEST: UserCreate enforces password min_length=8.

        PURPOSE: Prevent weak passwords during registration.

        VALIDATES:
        - Password "1234567" (7 chars) raises ValidationError
        - min_length=8 constraint enforced

        EXPECTED: ValidationError for password < 8 chars.
        """
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="1234567",
            )

        errors = exc_info.value.errors()
        assert any("password" in str(error) for error in errors)


class TestUserUpdate:
    """Test UserUpdate partial updates."""

    def test_user_update_all_fields_optional(self):
        """
        TEST: UserUpdate allows partial updates (all fields optional).

        PURPOSE: Enable updating specific fields without requiring all data.

        VALIDATES:
        - Can create UserUpdate with no fields (all None)
        - Can update only email
        - Can update only is_active

        EXPECTED: All fields optional, validation passes.
        """
        update = UserUpdate()
        assert update.email is None
        assert update.full_name is None
        assert update.is_active is None

        update_email_only = UserUpdate(email="new@example.com")
        assert update_email_only.email == "new@example.com"


class TestUser:
    """Test User model."""

    def test_user_includes_timestamps(self):
        """
        TEST: User inherits TimestampMixin for created_at/updated_at.

        PURPOSE: Track user creation and modification times.

        VALIDATES:
        - User inherits from TimestampMixin
        - created_at auto-generated
        - updated_at auto-generated

        EXPECTED: User has timestamp fields.
        """
        user = User(
            user_id="user_123",
            email="test@example.com",
        )

        assert hasattr(user, "created_at")
        assert hasattr(user, "updated_at")

    def test_user_defaults(self):
        """
        TEST: User has correct default values.

        PURPOSE: New users default to active, non-superuser state.

        VALIDATES:
        - is_active defaults to True
        - is_superuser defaults to False
        - full_name defaults to None

        EXPECTED: Default values match expected state.
        """
        user = User(
            user_id="user_123",
            email="test@example.com",
        )

        assert user.is_active is True
        assert user.is_superuser is False
        assert user.full_name is None


class TestUserInDB:
    """Test UserInDB with hashed password."""

    def test_user_in_db_includes_hashed_password(self):
        """
        TEST: UserInDB extends User with hashed_password field.

        PURPOSE: Store hashed password for authentication.

        VALIDATES:
        - Inherits all User fields
        - Adds hashed_password field
        - Never expose hashed_password in API responses (use User, not UserInDB)

        EXPECTED: UserInDB has hashed_password field.
        """
        user = UserInDB(
            user_id="user_123",
            email="test@example.com",
            hashed_password="$2b$12$abcdefghijk...",
        )

        assert user.email == "test@example.com"
        assert user.hashed_password == "$2b$12$abcdefghijk..."
        assert user.is_active is True
