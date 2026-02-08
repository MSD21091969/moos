"""
Unit tests for custom exception hierarchy.

Tests exception instantiation, inheritance, and error details in isolation.
"""

import pytest

from src.core.exceptions import (
    AuthenticationError,
    ColliderException,
    FirestoreError,
    InsufficientQuotaError,
    NotFoundError,
    PermissionDeniedError,
    SessionNotFoundError,
    ToolExecutionError,
    ToolNotFoundError,
    ValidationError,
)

# ============================================================================
# Base Exception Tests
# ============================================================================


class TestColliderException:
    """Test base ColliderException behavior."""

    def test_exception_with_message_only(self):
        """
        TEST: Create exception with message only.

        PURPOSE: Validate basic exception creation without details dict.

        VALIDATES:
        - Exception message stored in .message attribute
        - Exception inherits from Python Exception
        - Details dict defaults to empty {}

        EXPECTED: Exception created with message, empty details.
        """
        exc = ColliderException("Something went wrong")

        assert str(exc) == "Something went wrong"
        assert exc.message == "Something went wrong"
        assert exc.details == {}
        assert isinstance(exc, Exception)

    def test_exception_with_details(self):
        """
        TEST: Create exception with error details dict.

        PURPOSE: Enable structured error context for debugging and logging.

        VALIDATES:
        - Details dict stored in .details attribute
        - Can include user_id, session_id, error codes
        - Useful for audit trails and error tracking

        EXPECTED: Exception stores both message and details.
        """
        details = {"user_id": "user_123", "quota_used": 150, "quota_limit": 100}
        exc = ColliderException("Quota exceeded", details=details)

        assert exc.message == "Quota exceeded"
        assert exc.details == details
        assert exc.details["user_id"] == "user_123"

    def test_exception_can_be_raised_and_caught(self):
        """
        TEST: Exception can be raised and caught in try/except.

        PURPOSE: Verify exception behavior in standard Python error handling.

        VALIDATES:
        - Exception can be raised with raise keyword
        - Exception can be caught in except block
        - Message accessible in caught exception

        EXPECTED: Normal Python exception flow works.
        """
        with pytest.raises(ColliderException) as exc_info:
            raise ColliderException("Test error", details={"code": 500})

        assert exc_info.value.message == "Test error"
        assert exc_info.value.details["code"] == 500


# ============================================================================
# Specific Exception Tests
# ============================================================================


class TestNotFoundError:
    """Test NotFoundError for missing resources."""

    def test_not_found_error_inherits_from_base(self):
        """
        TEST: NotFoundError inherits from ColliderException.

        PURPOSE: Maintain exception hierarchy for catch-all error handling.

        VALIDATES:
        - isinstance(NotFoundError(), ColliderException) is True
        - Can catch NotFoundError with except ColliderException
        - Inheritance chain: NotFoundError → ColliderException → Exception

        EXPECTED: Proper inheritance chain.
        """
        exc = NotFoundError("Resource not found")

        assert isinstance(exc, ColliderException)
        assert isinstance(exc, Exception)

    def test_session_not_found_inherits_from_not_found(self):
        """
        TEST: SessionNotFoundError inherits from NotFoundError.

        PURPOSE: Enable specific session error handling while maintaining general NotFoundError catch.

        VALIDATES:
        - SessionNotFoundError → NotFoundError → ColliderException
        - Can catch with except NotFoundError or except ColliderException
        - Specific error type for session-related 404s

        EXPECTED: Three-level inheritance hierarchy.
        """
        exc = SessionNotFoundError("Session sess_abc123 not found")

        assert isinstance(exc, SessionNotFoundError)
        assert isinstance(exc, NotFoundError)
        assert isinstance(exc, ColliderException)

    def test_tool_not_found_inherits_from_not_found(self):
        """
        TEST: ToolNotFoundError inherits from NotFoundError.

        PURPOSE: Specific error for tool registry misses.

        VALIDATES:
        - ToolNotFoundError → NotFoundError → ColliderException
        - Used when tool lookup fails in ToolRegistry
        - Distinct from SessionNotFoundError

        EXPECTED: Proper inheritance, distinct from SessionNotFoundError.
        """
        exc = ToolNotFoundError("Tool 'analyze_data' not found")

        assert isinstance(exc, ToolNotFoundError)
        assert isinstance(exc, NotFoundError)
        assert not isinstance(exc, SessionNotFoundError)  # Distinct types


class TestPermissionDeniedError:
    """Test PermissionDeniedError for authorization failures."""

    def test_permission_denied_with_details(self):
        """
        TEST: PermissionDeniedError includes user/permission context.

        PURPOSE: Provide audit trail for authorization failures.

        VALIDATES:
        - Error includes user_id, required_permission, user_tier
        - Details useful for security logging
        - Can track which permissions users attempted to access

        EXPECTED: Exception stores permission context in details.
        """
        details = {
            "user_id": "user_123",
            "required_permission": "advanced_analytics",
            "user_tier": "free",
        }
        exc = PermissionDeniedError("Insufficient permissions", details=details)

        assert exc.message == "Insufficient permissions"
        assert exc.details["required_permission"] == "advanced_analytics"
        assert exc.details["user_tier"] == "free"


class TestInsufficientQuotaError:
    """Test InsufficientQuotaError for quota enforcement."""

    def test_quota_error_with_usage_details(self):
        """
        TEST: InsufficientQuotaError includes quota usage context.

        PURPOSE: Help users understand why request was rejected and how much quota needed.

        VALIDATES:
        - Error includes quota_used, quota_limit, quota_needed
        - User can see "You have 90/100 quota, need 20"
        - Useful for user-facing error messages

        EXPECTED: Exception stores quota metrics in details.
        """
        details = {
            "quota_used": 90,
            "quota_limit": 100,
            "quota_needed": 20,
            "shortfall": 10,
        }
        exc = InsufficientQuotaError("Not enough quota", details=details)

        assert exc.details["quota_used"] == 90
        assert exc.details["quota_limit"] == 100
        assert exc.details["shortfall"] == 10


class TestValidationError:
    """Test ValidationError for data validation failures."""

    def test_validation_error_with_field_details(self):
        """
        TEST: ValidationError includes field-level validation errors.

        PURPOSE: Provide specific feedback on which fields failed validation.

        VALIDATES:
        - Error includes field name, invalid value, constraint
        - Compatible with Pydantic ValidationError format
        - Useful for API 422 responses

        EXPECTED: Exception stores field validation context.
        """
        details = {
            "field": "title",
            "value": "",
            "constraint": "min_length=1",
            "error": "Title cannot be empty",
        }
        exc = ValidationError("Validation failed", details=details)

        assert exc.details["field"] == "title"
        assert exc.details["constraint"] == "min_length=1"


class TestAuthenticationError:
    """Test AuthenticationError for auth failures."""

    def test_authentication_error_for_jwt(self):
        """
        TEST: AuthenticationError for JWT token validation failures.

        PURPOSE: Track why authentication failed (expired, invalid, missing).

        VALIDATES:
        - Error includes token_status, reason
        - Used in JWT decode failures
        - Triggers 401 Unauthorized response

        EXPECTED: Exception stores auth failure reason.
        """
        details = {"token_status": "expired", "reason": "Token expired 2 hours ago"}
        exc = AuthenticationError("Invalid token", details=details)

        assert exc.details["token_status"] == "expired"


class TestFirestoreError:
    """Test FirestoreError for database operation failures."""

    def test_firestore_error_with_operation_context(self):
        """
        TEST: FirestoreError includes Firestore operation details.

        PURPOSE: Debug database failures with collection, document, operation context.

        VALIDATES:
        - Error includes collection, document_id, operation
        - Useful for identifying which Firestore call failed
        - Can include original GCP error message

        EXPECTED: Exception stores Firestore operation context.
        """
        details = {
            "collection": "sessions",
            "document_id": "sess_abc123",
            "operation": "update",
            "original_error": "Document not found",
        }
        exc = FirestoreError("Firestore operation failed", details=details)

        assert exc.details["collection"] == "sessions"
        assert exc.details["operation"] == "update"


class TestToolExecutionError:
    """Test ToolExecutionError for tool runtime failures."""

    def test_tool_execution_error_with_tool_context(self):
        """
        TEST: ToolExecutionError includes tool name and execution context.

        PURPOSE: Debug which tool failed and with what input.

        VALIDATES:
        - Error includes tool_name, input_params, error_message
        - Useful for tool debugging and user feedback
        - Can include stack trace in details

        EXPECTED: Exception stores tool execution context.
        """
        details = {
            "tool_name": "analyze_text",
            "input_params": {"text": "sample text", "mode": "sentiment"},
            "error_message": "API key invalid",
        }
        exc = ToolExecutionError("Tool execution failed", details=details)

        assert exc.details["tool_name"] == "analyze_text"
        assert exc.details["error_message"] == "API key invalid"


# ============================================================================
# Exception Hierarchy Tests
# ============================================================================


class TestExceptionHierarchy:
    """Test exception inheritance relationships."""

    def test_all_exceptions_inherit_from_base(self):
        """
        TEST: All custom exceptions inherit from ColliderException.

        PURPOSE: Enable catch-all exception handling with except ColliderException.

        VALIDATES:
        - Every custom exception is instanceof ColliderException
        - Can catch any app exception with single except block
        - Maintains consistent .message and .details interface

        EXPECTED: All 10 exception types inherit from base.
        """
        exceptions = [
            NotFoundError("test"),
            PermissionDeniedError("test"),
            ValidationError("test"),
            AuthenticationError("test"),
            FirestoreError("test"),
            ToolExecutionError("test"),
            InsufficientQuotaError("test"),
            SessionNotFoundError("test"),
            ToolNotFoundError("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, ColliderException)
            assert hasattr(exc, "message")
            assert hasattr(exc, "details")

    def test_exception_can_be_distinguished_by_type(self):
        """
        TEST: Each exception type is distinguishable via isinstance().

        PURPOSE: Enable specific exception handling in except blocks.

        VALIDATES:
        - isinstance() correctly identifies exception type
        - NotFoundError != PermissionDeniedError
        - Can use multiple except blocks for different error handling

        EXPECTED: Type checking works for specific exception handling.
        """
        not_found = NotFoundError("Missing")
        permission = PermissionDeniedError("Denied")

        assert isinstance(not_found, NotFoundError)
        assert not isinstance(not_found, PermissionDeniedError)
        assert isinstance(permission, PermissionDeniedError)
        assert not isinstance(permission, NotFoundError)
