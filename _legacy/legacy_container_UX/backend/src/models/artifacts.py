"""Artifact model for the Collider architecture.

Artifacts represent the actual data objects (files, JSON, streams) that exist within a session.
They are produced by Sources (ResourceLinks) and consumed by Agents (ResourceLinks).
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ArtifactType(str, Enum):
    """Type of data artifact."""
    
    FILE = "file"           # Binary/Text file (stored in GCS/Blob)
    JSON = "json"           # Structured data (stored in Firestore)
    TEXT = "text"           # Unstructured text (stored in Firestore)
    STREAM = "stream"       # Live data stream reference
    REFERENCE = "reference" # Pointer to external resource


class Artifact(BaseModel):
    """Data object residing in a session."""

    artifact_id: str = Field(..., description="Unique artifact ID")
    session_id: str = Field(..., description="Parent session ID")
    
    # Content
    type: ArtifactType = Field(..., description="Type of artifact")
    uri: str | None = Field(None, description="Storage URI (gs://... or internal ref)")
    content: Any | None = Field(None, description="Inline content (for JSON/Text < 1MB)")
    
    # Metadata
    key: str = Field(..., description="Session-unique key (e.g., 'report_pdf')")
    filename: str | None = Field(None, description="Original filename if applicable")
    mime_type: str | None = Field(None, description="MIME type")
    size_bytes: int = Field(default=0, description="Size in bytes")
    
    # Provenance
    created_by_link_id: str | None = Field(None, description="ID of ResourceLink that produced this")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    # Context
    tags: list[str] = Field(default_factory=list, description="Search tags")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom metadata")
