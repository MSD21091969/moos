"""Secrets API routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_db, User
from src.api.auth import get_current_user
from src.api.permissions import RequireAdmin
from src.firebase_auth import FirebaseUser
from src.secrets import get_secret_store, get_required_secrets

router = APIRouter(prefix="/secrets", tags=["secrets"])


class SecretCreate(BaseModel):
    name: str
    value: str


class SecretInfo(BaseModel):
    name: str
    scope: str
    has_value: bool = True  # Never expose actual value


@router.get("/app/{app_id}", response_model=list[SecretInfo])
async def list_app_secrets(
    app_id: str,
    perm: RequireAdmin,  # Only admins can view secrets
):
    """List secrets for an application (names only, not values)."""
    store = get_secret_store()
    names = await store.list(scope=f"app-{app_id}")

    return [SecretInfo(name=name, scope=f"app-{app_id}") for name in names]


@router.post("/app/{app_id}")
async def set_app_secret(
    app_id: str,
    data: SecretCreate,
    perm: RequireAdmin,  # Only admins can set secrets
):
    """Set an application-scoped secret."""
    store = get_secret_store()
    await store.set(data.name, data.value, scope=f"app-{app_id}")

    return {"status": "created", "name": data.name, "scope": f"app-{app_id}"}


@router.delete("/app/{app_id}/{name}")
async def delete_app_secret(
    app_id: str,
    name: str,
    perm: RequireAdmin,  # Only admins can delete secrets
):
    """Delete an application-scoped secret."""
    store = get_secret_store()
    await store.delete(name, scope=f"app-{app_id}")

    return {"status": "deleted", "name": name}


@router.get("/user/me", response_model=list[SecretInfo])
async def list_my_secrets(
    user_data: tuple[User, FirebaseUser] = Depends(get_current_user),
):
    """List secrets for the current user (names only)."""
    user, _ = user_data
    store = get_secret_store()
    names = await store.list(scope=f"user-{user.id}")

    return [SecretInfo(name=name, scope=f"user-{user.id}") for name in names]


@router.post("/user/me")
async def set_my_secret(
    data: SecretCreate,
    user_data: tuple[User, FirebaseUser] = Depends(get_current_user),
):
    """Set a user-scoped secret."""
    user, _ = user_data
    store = get_secret_store()
    await store.set(data.name, data.value, scope=f"user-{user.id}")

    return {"status": "created", "name": data.name, "scope": f"user-{user.id}"}


@router.delete("/user/me/{name}")
async def delete_my_secret(
    name: str,
    user_data: tuple[User, FirebaseUser] = Depends(get_current_user),
):
    """Delete a user-scoped secret."""
    user, _ = user_data
    store = get_secret_store()
    await store.delete(name, scope=f"user-{user.id}")

    return {"status": "deleted", "name": name}


@router.post("/validate")
async def validate_secrets(
    container: dict,
    user_data: tuple[User, FirebaseUser] = Depends(get_current_user),
):
    """
    Validate that all required secrets for a container are available.

    Returns list of missing secrets.
    """
    required = await get_required_secrets(container)
    store = get_secret_store()
    user, _ = user_data

    missing = []
    for name in required:
        # Check user scope
        value = await store.get(name, scope=f"user-{user.id}")
        if value:
            continue

        # Check global scope
        value = await store.get(name, scope="global")
        if value:
            continue

        missing.append(name)

    return {
        "required": required,
        "missing": missing,
        "valid": len(missing) == 0,
    }
