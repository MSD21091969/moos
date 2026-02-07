"""Custom exception hierarchy."""

from typing import Any


class ColliderException(Exception):
    """Base exception for all Collider errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(ColliderException):
    """Resource not found."""

    pass


class PermissionDeniedError(ColliderException):
    """User lacks permission for operation."""

    pass


class ValidationError(ColliderException):
    """Data validation failed."""

    pass


class AuthenticationError(ColliderException):
    """Authentication failed."""

    pass


class FirestoreError(ColliderException):
    """Firestore operation failed."""

    pass


class ToolExecutionError(ColliderException):
    """Tool execution failed."""

    pass


class InsufficientQuotaError(ColliderException):
    """User has insufficient quota."""

    pass


class SessionNotFoundError(NotFoundError):
    """Session not found."""

    pass


class ToolNotFoundError(NotFoundError):
    """Tool not found in registry."""

    pass


class CircularDependencyError(ValidationError):
    """Circular dependency detected in container hierarchy."""

    pass


class DepthLimitError(ValidationError):
    """Container depth limit exceeded."""

    pass


class InvalidContainmentError(ValidationError):
    """Invalid container containment (e.g., Source in Session)."""

    pass


class TerminalNodeError(ValidationError):
    """Terminal node cannot have children or be navigated into.
    
    Terminal nodes in UOM: SOURCE, USER, INTROSPECTION
    These nodes are leaf nodes that cannot contain other resources.
    """

    pass
