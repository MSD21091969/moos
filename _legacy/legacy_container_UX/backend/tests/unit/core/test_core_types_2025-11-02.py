"""Unit tests for src/core/types.py

TEST: Custom type definitions
PURPOSE: Validate type aliases and constraints
VALIDATES: UserId, SessionId, Email patterns
EXPECTED: All types defined correctly
"""

import pytest
from pydantic import ValidationError, BaseModel
from src.core.types import (
    UserId,
    SessionId,
    CollectionId,
    ToolId,
    SessionIdStr,
    UserIdStr,
    Email,
    NonEmptyStr,
)


class TestNewTypes:
    """Test NewType definitions."""

    def test_user_id_type(self):
        """
        TEST: UserId type alias
        PURPOSE: Verify type alias works
        VALIDATES: Can create UserId
        EXPECTED: Type wraps string
        """
        user_id = UserId("user_123")

        assert isinstance(user_id, str)
        assert user_id == "user_123"

    def test_session_id_type(self):
        """
        TEST: SessionId type alias
        PURPOSE: Verify type alias works
        VALIDATES: Can create SessionId
        EXPECTED: Type wraps string
        """
        session_id = SessionId("sess_123")

        assert isinstance(session_id, str)
        assert session_id == "sess_123"

    def test_collection_id_type(self):
        """
        TEST: CollectionId type alias
        PURPOSE: Verify type alias works
        VALIDATES: Can create CollectionId
        EXPECTED: Type wraps string
        """
        collection_id = CollectionId("coll_123")

        assert isinstance(collection_id, str)

    def test_tool_id_type(self):
        """
        TEST: ToolId type alias
        PURPOSE: Verify type alias works
        VALIDATES: Can create ToolId
        EXPECTED: Type wraps string
        """
        tool_id = ToolId("tool_123")

        assert isinstance(tool_id, str)


class TestAnnotatedTypes:
    """Test Annotated type constraints."""

    def test_session_id_str_valid(self):
        """
        TEST: SessionIdStr pattern validation
        PURPOSE: Verify session ID format
        VALIDATES: Pattern matches sess_[hex]
        EXPECTED: Valid IDs accepted
        """

        class Model(BaseModel):
            session_id: SessionIdStr

        # Valid format: sess_ + 16 hex chars
        model = Model(session_id="sess_0123456789abcdef")
        assert model.session_id == "sess_0123456789abcdef"

    def test_session_id_str_invalid(self):
        """
        TEST: SessionIdStr pattern rejection
        PURPOSE: Verify invalid format rejected
        VALIDATES: Pattern enforced
        EXPECTED: ValidationError raised
        """

        class Model(BaseModel):
            session_id: SessionIdStr

        with pytest.raises(ValidationError):
            Model(session_id="invalid")

    def test_user_id_str_valid(self):
        """
        TEST: UserIdStr pattern validation
        PURPOSE: Verify user ID format
        VALIDATES: Pattern matches user_[hex]
        EXPECTED: Valid IDs accepted
        """

        class Model(BaseModel):
            user_id: UserIdStr

        model = Model(user_id="user_0123456789abcdef")
        assert model.user_id == "user_0123456789abcdef"

    def test_email_valid(self):
        """
        TEST: Email pattern validation
        PURPOSE: Verify email format
        VALIDATES: Valid emails accepted
        EXPECTED: Standard email format
        """

        class Model(BaseModel):
            email: Email

        model = Model(email="test@example.com")
        assert model.email == "test@example.com"

    def test_email_invalid(self):
        """
        TEST: Email pattern rejection
        PURPOSE: Verify invalid email rejected
        VALIDATES: Pattern enforced
        EXPECTED: ValidationError raised
        """

        class Model(BaseModel):
            email: Email

        with pytest.raises(ValidationError):
            Model(email="not_an_email")

    def test_non_empty_str_valid(self):
        """
        TEST: NonEmptyStr constraint
        PURPOSE: Verify non-empty enforcement
        VALIDATES: String must have content
        EXPECTED: Valid strings accepted
        """

        class Model(BaseModel):
            text: NonEmptyStr

        model = Model(text="Hello")
        assert model.text == "Hello"

    def test_non_empty_str_strips_whitespace(self):
        """
        TEST: NonEmptyStr whitespace stripping
        PURPOSE: Verify whitespace handling
        VALIDATES: Leading/trailing spaces removed
        EXPECTED: Whitespace stripped
        """

        class Model(BaseModel):
            text: NonEmptyStr

        model = Model(text="  Hello  ")
        assert model.text == "Hello"

    def test_non_empty_str_rejects_empty(self):
        """
        TEST: NonEmptyStr empty rejection
        PURPOSE: Verify empty string rejected
        VALIDATES: min_length enforced
        EXPECTED: ValidationError raised
        """

        class Model(BaseModel):
            text: NonEmptyStr

        with pytest.raises(ValidationError):
            Model(text="")
