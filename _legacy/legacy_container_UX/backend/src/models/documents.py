"""Document domain model."""

from datetime import UTC, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class Document(BaseModel):
    """Document metadata and content."""

    document_id: str = Field(..., description="Unique document identifier")
    session_id: str = Field(..., description="Parent session ID")
    filename: str = Field(..., min_length=1, max_length=255, description="Original filename")
    content_type: str = Field(..., description="MIME type (e.g., text/plain, application/pdf)")
    size_bytes: int = Field(..., ge=1, description="File size in bytes")
    content: Optional[str] = Field(None, description="Document content (text)")
    storage_path: Optional[str] = Field(
        None, description="Path to stored blob (for binary/large files)"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    user_id: str = Field(..., description="User who uploaded the document")
    tags: list[str] = Field(default_factory=list, max_length=10)
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "document_id": "doc_abc123",
                "session_id": "sess_xyz789",
                "filename": "report.txt",
                "content_type": "text/plain",
                "size_bytes": 2048,
                "content": "Document content here...",
                "created_at": "2025-11-01T21:51:00Z",
                "user_id": "user_123",
                "tags": ["finance", "q4"],
                "metadata": {"source": "upload"},
            }
        }


class DocumentCreate(BaseModel):
    """Create document request."""

    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., description="MIME type")
    content: str = Field(..., description="Document text content")
    tags: list[str] = Field(default_factory=list, max_length=10)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentResponse(BaseModel):
    """Document response model."""

    document_id: str
    filename: str
    content_type: str
    size_bytes: int
    created_at: datetime
    user_id: str
    tags: list[str]
    metadata: dict[str, Any]


class DocumentListResponse(BaseModel):
    """List documents response."""

    session_id: str
    documents: list[DocumentResponse]
    total: int
    page: int = 1
    page_size: int = 50
    has_more: bool
