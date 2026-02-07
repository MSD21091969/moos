"""Tool wrapper for permission and quota enforcement."""

from functools import wraps
from typing import Any, Callable, ParamSpec, TypeVar

from pydantic_ai import RunContext

from src.core.logging import get_logger
from src.core.tool_registry import get_tool_registry
from src.models.context import SessionContext

logger = get_logger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


class PermissionDeniedError(Exception):
    """Raised when user lacks required permissions."""

    pass


class QuotaExceededError(Exception):
    """Raised when user has insufficient quota."""

    pass


class ToolWrapper:
    """
    Wrapper for tools with permission and quota enforcement.

    Provides:
    - Permission checking before execution
    - Quota validation and deduction
    - Audit logging
    - Error handling
    """

    def __init__(self, tool_name: str):
        """
        Initialize wrapper.

        Args:
            tool_name: Name of tool to wrap (must be in registry)
        """
        self.tool_name = tool_name
        self.registry = get_tool_registry()

    def __call__(self, func: Callable[P, T]) -> Any:
        """
        Wrap a tool function.

        Args:
            func: Tool function to wrap

        Returns:
            Wrapped function with enforcement

        Example:
            >>> wrapper = ToolWrapper("analyze_csv")
            >>> @wrapper
            ... async def analyze_csv(ctx: RunContext[SessionContext], file_path: str):
            ...     return {"rows": 100}
        """

        @wraps(func)
        async def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
            # Extract RunContext (first arg by PydanticAI convention)
            ctx = args[0] if args else None

            if not isinstance(ctx, RunContext):
                raise TypeError(f"First argument must be RunContext, got {type(ctx)}")

            session_ctx: SessionContext = ctx.deps

            # Check if tool can be executed
            user_tier = (
                session_ctx.tier.value
                if hasattr(session_ctx.tier, "value")
                else str(session_ctx.tier)
            )

            can_execute, reason = self.registry.can_execute(
                self.tool_name, user_tier, session_ctx.quota_remaining
            )

            if not can_execute:
                logger.warning(
                    f"Tool execution denied: {self.tool_name}",
                    extra={"user_id": session_ctx.user_id, "reason": reason},
                )
                raise PermissionDeniedError(reason)

            # Get tool metadata
            metadata = self.registry.get_metadata(self.tool_name)
            if metadata is None:
                raise RuntimeError(f"Tool metadata not found for {self.tool_name}")

            # Log execution start
            logger.info(
                f"Tool execution started: {self.tool_name}",
                extra={
                    "user_id": session_ctx.user_id,
                    "session_id": session_ctx.session_id,
                    "quota_cost": metadata.quota_cost,  # type: ignore[union-attr]
                },
            )

            try:
                # Execute tool
                result = await func(*args, **kwargs)  # type: ignore[misc]

                # Log success
                logger.info(
                    f"Tool execution completed: {self.tool_name}",
                    extra={"user_id": session_ctx.user_id, "session_id": session_ctx.session_id},
                )

                # Quota deduction (real implementation with Firestore)
                from src.core.container import get_container
                from src.services.quota_service import QuotaService

                try:
                    container = get_container()
                    quota_service = QuotaService(container.firestore_client)
                    await quota_service.deduct_quota(
                        user_id=session_ctx.user_id,
                        tier=session_ctx.tier.value
                        if hasattr(session_ctx.tier, "value")
                        else str(session_ctx.tier),
                        amount=metadata.quota_cost,  # type: ignore[union-attr]
                    )
                    logger.info(
                        f"Quota deducted: {metadata.quota_cost} units for user {session_ctx.user_id}",  # type: ignore[union-attr]
                        extra={"tool": self.tool_name},
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to deduct quota (continuing anyway): {e}",
                        extra={"user_id": session_ctx.user_id, "tool": self.tool_name},
                    )

                return result

            except Exception as e:
                # Log failure
                logger.error(
                    f"Tool execution failed: {self.tool_name}",
                    extra={
                        "user_id": session_ctx.user_id,
                        "session_id": session_ctx.session_id,
                        "error": str(e),
                    },
                )
                raise

        return wrapped


def enforce_permissions(tool_name: str) -> Callable:
    """
    Decorator for permission/quota enforcement.

    Args:
        tool_name: Name of tool (must be registered)

    Returns:
        Decorator function

    Example:
        >>> @enforce_permissions("analyze_csv")
        ... async def analyze_csv(ctx: RunContext[SessionContext], file_path: str):
        ...     return {"rows": 100}
    """
    wrapper = ToolWrapper(tool_name)
    return wrapper


def check_quota(ctx: RunContext[SessionContext], required_quota: int) -> bool:
    """
    Check if user has sufficient quota.

    Args:
        ctx: Run context with session info
        required_quota: Quota units required

    Returns:
        True if user has sufficient quota

    Example:
        >>> if not check_quota(ctx, 10):
        ...     raise QuotaExceededError("Need 10 quota units")
    """
    return ctx.deps.quota_remaining >= required_quota


def check_permission(ctx: RunContext[SessionContext], required_permission: str) -> bool:
    """
    Check if user has a specific permission.

    Args:
        ctx: Run context with session info
        required_permission: Permission to check

    Returns:
        True if user has permission

    Example:
        >>> if not check_permission(ctx, "export"):
        ...     raise PermissionDeniedError("Need 'export' permission")
    """
    return required_permission in ctx.deps.permissions
