"""
Unit tests for common models.

Tests TimestampMixin, StatusEnum, ErrorResponse in isolation.
"""

from datetime import datetime


from src.models.common import ErrorResponse, ResponseStatus, StatusEnum, TimestampMixin


class TestTimestampMixin:
    """Test TimestampMixin auto-timestamp functionality."""

    def test_timestamp_mixin_auto_creates_timestamps(self):
        """
        TEST: TimestampMixin auto-generates created_at and updated_at.

        PURPOSE: Ensure all models inheriting TimestampMixin get automatic timestamps.

        VALIDATES:
        - created_at auto-set to current UTC time
        - updated_at auto-set to current UTC time
        - Both are datetime objects
        - Timestamps within 1 second of now (accounting for test execution time)

        EXPECTED: Auto-generated timestamps on model creation.
        """

        class TestModel(TimestampMixin):
            pass

        before = datetime.utcnow()
        model = TestModel()
        after = datetime.utcnow()

        assert isinstance(model.created_at, datetime)
        assert isinstance(model.updated_at, datetime)
        assert before <= model.created_at <= after
        assert before <= model.updated_at <= after

    def test_timestamp_mixin_allows_manual_override(self):
        """
        TEST: TimestampMixin allows manual timestamp override.

        PURPOSE: Enable testing and data migration with specific timestamps.

        VALIDATES:
        - Can pass created_at explicitly
        - Can pass updated_at explicitly
        - Manual values override default_factory

        EXPECTED: Manual timestamps used instead of auto-generated.
        """

        class TestModel(TimestampMixin):
            pass

        custom_time = datetime(2025, 1, 1, 12, 0, 0)
        model = TestModel(created_at=custom_time, updated_at=custom_time)

        assert model.created_at == custom_time
        assert model.updated_at == custom_time


class TestStatusEnum:
    """Test StatusEnum values."""

    def test_status_enum_values(self):
        """
        TEST: StatusEnum includes all expected status values.

        PURPOSE: Validate session/task lifecycle states are defined.

        VALIDATES:
        - ACTIVE, INACTIVE, PENDING, COMPLETED, FAILED, EXPIRED all exist
        - Values are lowercase strings
        - Can be used in equality checks

        EXPECTED: All 6 status values accessible.
        """
        assert StatusEnum.ACTIVE == "active"
        assert StatusEnum.INACTIVE == "inactive"
        assert StatusEnum.PENDING == "pending"
        assert StatusEnum.COMPLETED == "completed"
        assert StatusEnum.FAILED == "failed"
        assert StatusEnum.EXPIRED == "expired"


class TestErrorResponse:
    """Test ErrorResponse model."""

    def test_error_response_with_message_only(self):
        """
        TEST: ErrorResponse creates with message only.

        PURPOSE: Enable simple error responses without extra details.

        VALIDATES:
        - status defaults to ResponseStatus.ERROR
        - message stored correctly
        - details defaults to None
        - timestamp auto-generated

        EXPECTED: Error response with minimal fields.
        """
        error = ErrorResponse(message="Something went wrong")

        assert error.status == ResponseStatus.ERROR
        assert error.message == "Something went wrong"
        assert error.details is None
        assert isinstance(error.timestamp, datetime)

    def test_error_response_with_details(self):
        """
        TEST: ErrorResponse includes error details dict.

        PURPOSE: Provide structured error context for debugging.

        VALIDATES:
        - details dict stored correctly
        - Can include field errors, codes, etc.
        - Useful for API 400/422 responses

        EXPECTED: Error response with details dict.
        """
        error = ErrorResponse(
            message="Validation failed",
            details={
                "field": "email",
                "error": "Invalid format",
                "code": "E001",
            },
        )

        assert error.message == "Validation failed"
        assert error.details["field"] == "email"
        assert error.details["code"] == "E001"
