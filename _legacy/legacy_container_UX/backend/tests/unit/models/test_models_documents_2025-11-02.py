"""Unit tests for src/models/documents.py

TEST: Document model validation
PURPOSE: Ensure document schemas validate correctly
VALIDATES: Field constraints, defaults, Pydantic validation
EXPECTED: Valid documents pass, invalid documents raise ValidationError
"""

import pytest
from pydantic import ValidationError
from datetime import datetime, UTC

from src.models.documents import (
    Document,
    DocumentCreate,
    DocumentResponse,
    DocumentListResponse,
)


class TestDocumentModel:
    """Test Document Pydantic model."""

    def test_valid_document_creation(self):
        """
        TEST: Create document with all required fields
        PURPOSE: Verify basic document instantiation
        VALIDATES: All required fields accepted
        EXPECTED: Document created successfully
        """
        doc = Document(
            document_id="doc_abc123",
            session_id="sess_xyz789",
            filename="report.txt",
            content_type="text/plain",
            size_bytes=2048,
            content="Document content here",
            user_id="user_123",
        )

        assert doc.document_id == "doc_abc123"
        assert doc.session_id == "sess_xyz789"
        assert doc.filename == "report.txt"
        assert doc.content_type == "text/plain"
        assert doc.size_bytes == 2048
        assert doc.user_id == "user_123"

    def test_document_auto_timestamps(self):
        """
        TEST: Document timestamps auto-populate
        PURPOSE: Ensure created_at/updated_at default to current time
        VALIDATES: Timestamp defaults work
        EXPECTED: Timestamps set to current UTC time
        """
        doc = Document(
            document_id="doc_123",
            session_id="sess_123",
            filename="test.txt",
            content_type="text/plain",
            size_bytes=100,
            user_id="user_123",
        )

        assert isinstance(doc.created_at, datetime)
        assert isinstance(doc.updated_at, datetime)
        assert doc.created_at.tzinfo == UTC
        assert doc.updated_at.tzinfo == UTC

    def test_document_requires_filename(self):
        """
        TEST: Document requires filename
        PURPOSE: Validate required field enforcement
        VALIDATES: Missing filename raises error
        EXPECTED: ValidationError raised
        """
        with pytest.raises(ValidationError) as exc_info:
            Document(
                document_id="doc_123",
                session_id="sess_123",
                # filename missing
                content_type="text/plain",
                size_bytes=100,
                user_id="user_123",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("filename",) for e in errors)

    def test_document_filename_max_length(self):
        """
        TEST: Filename cannot exceed 255 characters
        PURPOSE: Validate max_length constraint
        VALIDATES: Pydantic Field validation
        EXPECTED: ValidationError for long filename
        """
        long_filename = "a" * 256

        with pytest.raises(ValidationError) as exc_info:
            Document(
                document_id="doc_123",
                session_id="sess_123",
                filename=long_filename,
                content_type="text/plain",
                size_bytes=100,
                user_id="user_123",
            )

        errors = exc_info.value.errors()
        assert any("filename" in str(e["loc"]) for e in errors)

    def test_document_size_bytes_positive(self):
        """
        TEST: size_bytes must be >= 1
        PURPOSE: Validate minimum file size
        VALIDATES: Field ge=1 constraint
        EXPECTED: ValidationError for size_bytes=0
        """
        with pytest.raises(ValidationError):
            Document(
                document_id="doc_123",
                session_id="sess_123",
                filename="empty.txt",
                content_type="text/plain",
                size_bytes=0,  # Invalid
                user_id="user_123",
            )

    def test_document_tags_default_empty_list(self):
        """
        TEST: tags defaults to empty list
        PURPOSE: Verify default factory works
        VALIDATES: Field default_factory
        EXPECTED: tags is empty list when not provided
        """
        doc = Document(
            document_id="doc_123",
            session_id="sess_123",
            filename="test.txt",
            content_type="text/plain",
            size_bytes=100,
            user_id="user_123",
        )

        assert doc.tags == []

    def test_document_tags_max_length(self):
        """
        TEST: tags cannot exceed 10 items
        PURPOSE: Validate max_length constraint on list
        VALIDATES: Pydantic list validation
        EXPECTED: ValidationError for >10 tags
        """
        with pytest.raises(ValidationError):
            Document(
                document_id="doc_123",
                session_id="sess_123",
                filename="test.txt",
                content_type="text/plain",
                size_bytes=100,
                user_id="user_123",
                tags=["tag" + str(i) for i in range(11)],  # 11 tags
            )

    def test_document_metadata_default_empty_dict(self):
        """
        TEST: metadata defaults to empty dict
        PURPOSE: Verify dict default factory
        VALIDATES: Field default_factory
        EXPECTED: metadata is empty dict when not provided
        """
        doc = Document(
            document_id="doc_123",
            session_id="sess_123",
            filename="test.txt",
            content_type="text/plain",
            size_bytes=100,
            user_id="user_123",
        )

        assert doc.metadata == {}


class TestDocumentCreate:
    """Test DocumentCreate request model."""

    def test_valid_document_create(self):
        """
        TEST: Create valid DocumentCreate request
        PURPOSE: Verify request model validation
        VALIDATES: All required fields accepted
        EXPECTED: DocumentCreate instance created
        """
        request = DocumentCreate(
            filename="report.pdf",
            content_type="application/pdf",
            content="PDF content as text",
        )

        assert request.filename == "report.pdf"
        assert request.content_type == "application/pdf"
        assert request.content == "PDF content as text"

    def test_document_create_requires_content(self):
        """
        TEST: DocumentCreate requires content
        PURPOSE: Validate required field enforcement
        VALIDATES: Missing content raises error
        EXPECTED: ValidationError raised
        """
        with pytest.raises(ValidationError) as exc_info:
            DocumentCreate(
                filename="test.txt",
                content_type="text/plain",
                # content missing
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("content",) for e in errors)

    def test_document_create_tags_defaults(self):
        """
        TEST: tags defaults to empty list
        PURPOSE: Verify optional field defaults
        VALIDATES: Default factory works
        EXPECTED: tags is empty list
        """
        request = DocumentCreate(
            filename="test.txt", content_type="text/plain", content="Test content"
        )

        assert request.tags == []
        assert request.metadata == {}


class TestDocumentResponse:
    """Test DocumentResponse API model."""

    def test_document_response_creation(self):
        """
        TEST: Create DocumentResponse
        PURPOSE: Verify response model structure
        VALIDATES: All fields can be set
        EXPECTED: Response model created successfully
        """
        response = DocumentResponse(
            document_id="doc_123",
            filename="report.txt",
            content_type="text/plain",
            size_bytes=2048,
            created_at=datetime.now(UTC),
            user_id="user_123",
            tags=["finance"],
            metadata={"source": "upload"},
        )

        assert response.document_id == "doc_123"
        assert response.filename == "report.txt"
        assert len(response.tags) == 1


class TestDocumentListResponse:
    """Test DocumentListResponse API model."""

    def test_document_list_response_with_pagination(self):
        """
        TEST: Create paginated document list response
        PURPOSE: Verify pagination fields work
        VALIDATES: Pagination metadata
        EXPECTED: All pagination fields set correctly
        """
        response = DocumentListResponse(
            session_id="sess_123",
            documents=[],
            total=42,
            page=2,
            page_size=20,
            has_more=True,
        )

        assert response.session_id == "sess_123"
        assert response.total == 42
        assert response.page == 2
        assert response.page_size == 20
        assert response.has_more is True

    def test_document_list_defaults(self):
        """
        TEST: Pagination defaults
        PURPOSE: Verify default values
        VALIDATES: Default field values
        EXPECTED: page=1, page_size=50
        """
        response = DocumentListResponse(
            session_id="sess_123", documents=[], total=0, has_more=False
        )

        assert response.page == 1
        assert response.page_size == 50
