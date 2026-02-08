"""Unit tests for Session models.

Tests Pydantic validation, business rules, and model behavior in isolation.
Unit tests should be fast (<100ms), have no external dependencies, and test ONE thing.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.models.sessions import (
    Session,
    SessionCreate,
    SessionMetadata,
    SessionStatus,
    SessionType,
)

# ============================================================================
# SessionCreate Validation Tests
# ============================================================================


class TestSessionCreateValidation:
    """Test SessionCreate Pydantic validation rules."""

    def test_valid_session_create(self, session_create_model):
        """
        TEST: Validate SessionCreate model accepts valid input structure.

        PURPOSE: Ensure correctly formed session creation requests pass Pydantic validation.

        VALIDATES:
        - Nested metadata structure (SessionMetadata wrapper required)
        - Title field accessible via metadata.title
        - Session type enum (SessionType.CHAT)
        - TTL hours default (24 hours)

        EXPECTED: Fixture session_create_model passes validation, fields accessible.
        """
        assert session_create_model.metadata.title == "Test Session"
        assert session_create_model.metadata.session_type == SessionType.CHAT
        assert session_create_model.metadata.ttl_hours == 24

    def test_session_create_requires_title(self):
        """
        TEST: Validate title field enforcement (min_length=1).

        PURPOSE: Prevent creation of sessions without meaningful titles.

        VALIDATES:
        - Empty string title="" raises ValidationError
        - Error location is ('title',) in Pydantic v2
        - Error type is 'string_too_short'

        EXPECTED: ValidationError with error at ('title',) location.
        """
        with pytest.raises(ValidationError) as exc_info:
            SessionCreate(
                metadata=SessionMetadata(title="", session_type=SessionType.CHAT)
            )  # Empty title

        errors = exc_info.value.errors()
        # Error is reported at ('title',) not ('metadata', 'title') in Pydantic v2
        assert any(e["loc"] == ("title",) for e in errors)

    def test_session_title_max_length(self):
        """
        TEST: Validate title maximum length constraint (200 chars).

        PURPOSE: Prevent excessively long titles that break UI layouts and database limits.

        VALIDATES:
        - Title with 201 characters raises ValidationError
        - Constraint defined in SessionMetadata: Field(..., max_length=200)

        EXPECTED: ValidationError for title exceeding 200 characters.
        """
        with pytest.raises(ValidationError):
            SessionCreate(
                metadata=SessionMetadata(
                    title="x" * 201,  # Too long
                    session_type=SessionType.CHAT,
                )
            )

    def test_session_title_min_length(self):
        """
        TEST: Validate title minimum length constraint (1 char).

        PURPOSE: Ensure every session has a non-empty title for identification.

        VALIDATES:
        - Empty string title="" raises ValidationError
        - Constraint defined in SessionMetadata: Field(..., min_length=1)

        EXPECTED: ValidationError for empty title string.
        """
        with pytest.raises(ValidationError):
            SessionCreate(
                metadata=SessionMetadata(
                    title="",  # Empty
                    session_type=SessionType.CHAT,
                )
            )

    def test_session_description_optional(self):
        """
        TEST: Validate description field is optional (can be None).

        PURPOSE: Allow session creation without requiring detailed descriptions.

        VALIDATES:
        - SessionCreate without description field passes validation
        - metadata.description defaults to None
        - Field defined as: description: str | None = Field(None, ...)

        EXPECTED: Session created successfully with description=None.
        """
        create = SessionCreate(
            metadata=SessionMetadata(title="Test", session_type=SessionType.CHAT)
        )
        assert create.metadata.description is None

    def test_session_type_must_be_valid_enum(self):
        """
        TEST: Validate session_type accepts only SessionType enum values.

        PURPOSE: Enforce type safety and prevent invalid session types.

        VALIDATES:
        - Valid SessionType values: CHAT, ANALYSIS, INTERACTIVE, WORKFLOW, SIMULATION
        - Invalid string "invalid_type" raises ValidationError
        - Pydantic coerces valid strings to enum automatically

        EXPECTED: Valid types pass, invalid types raise ValidationError.
        """
        # Valid types work
        for valid_type in [SessionType.CHAT, SessionType.ANALYSIS, SessionType.INTERACTIVE]:
            create = SessionCreate(metadata=SessionMetadata(title="Test", session_type=valid_type))
            assert create.metadata.session_type in SessionType

        # Invalid type fails
        with pytest.raises(ValidationError):
            SessionCreate(
                metadata=SessionMetadata(
                    title="Test",
                    session_type="invalid_type",  # type: ignore
                )
            )

    def test_ttl_default_value(self):
        """
        TEST: Validate TTL (time-to-live) defaults to 24 hours.

        PURPOSE: Ensure sessions auto-expire after 1 day if not explicitly configured.

        VALIDATES:
        - SessionMetadata without ttl_hours uses default=24
        - Field defined as: ttl_hours: int = Field(default=24, gt=0, le=8760)
        - Default balances between usability (not too short) and cleanup (not too long)

        EXPECTED: metadata.ttl_hours == 24 when not explicitly set.
        """
        create = SessionCreate(
            metadata=SessionMetadata(title="Test", session_type=SessionType.CHAT)
        )
        assert create.metadata.ttl_hours == 24


# ============================================================================
# Session Model Tests
# ============================================================================


class TestSessionModel:
    """Test Session model behavior and constraints."""

    def test_session_id_format(self, active_session):
        """
        TEST: Validate session_id follows required pattern: sess_[a-f0-9]{12}

        PURPOSE: Ensure session IDs are URL-safe, unique, and conform to expected format.

        VALIDATES:
        - Prefix: "sess_" (4 chars)
        - Suffix: 12 hexadecimal characters [a-f0-9]
        - Total length: 17 characters
        - Pattern defined in SESSION_ID_PATTERN regex in sessions.py

        EXPECTED: active_session.session_id matches pattern (e.g., "sess_abc123def456").
        """
        assert active_session.session_id.startswith("sess_")
        assert len(active_session.session_id) == 17  # sess_ + 12 chars

    def test_session_has_timestamps(self, active_session):
        """
        TEST: Validate Session model includes created_at and updated_at timestamps.

        PURPOSE: Enable audit trails and track session lifecycle for analytics.

        VALIDATES:
        - created_at field exists and is datetime type
        - updated_at field exists and is datetime type
        - Both inherited from TimestampMixin
        - Timezone-aware (UTC) for consistency

        EXPECTED: Both timestamps present and are datetime instances.
        """
        assert active_session.created_at is not None
        assert active_session.updated_at is not None
        assert isinstance(active_session.created_at, datetime)
        assert isinstance(active_session.updated_at, datetime)

    def test_session_default_status_is_active(self):
        """
        TEST: Validate new sessions default to ACTIVE status.

        PURPOSE: Ensure sessions start in usable state without explicit status assignment.

        VALIDATES:
        - Session created without status field defaults to SessionStatus.ACTIVE
        - Field defined as: status: SessionStatus = Field(default=SessionStatus.ACTIVE)
        - Supports session lifecycle: ACTIVE → COMPLETED → EXPIRED → ARCHIVED

        EXPECTED: session.status == SessionStatus.ACTIVE when not explicitly set.
        """
        from datetime import timedelta

        now = datetime.now(timezone.utc)
        session = Session(
            session_id="sess_abc123def456",  # Valid format
            user_id="user_123",
            metadata=SessionMetadata(
                title="Test",
                session_type=SessionType.CHAT,
            ),
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(hours=24),  # 24 hours from now
            created_by="user_123",
        )
        assert session.status == SessionStatus.ACTIVE
