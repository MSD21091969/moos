"""API package."""

from src.api.auth import router as auth_router
from src.api.apps import router as apps_router
from src.api.nodes import router as nodes_router
from src.api.sse import router as sse_router
from src.api.users import router as users_router
from src.api.secrets import router as secrets_router

__all__ = [
    "auth_router",
    "apps_router",
    "nodes_router",
    "sse_router",
    "users_router",
    "secrets_router",
]
