"""Common models shared across the application."""

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class TimestampMixin(BaseModel):
    """Mixin for created/updated timestamps."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class StatusEnum(str, Enum):
    """Common status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class ResponseStatus(str, Enum):
    """API response status."""

    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"


class ErrorResponse(BaseModel):
    """Standard error response."""

    status: ResponseStatus = ResponseStatus.ERROR
    message: str
    details: dict | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
