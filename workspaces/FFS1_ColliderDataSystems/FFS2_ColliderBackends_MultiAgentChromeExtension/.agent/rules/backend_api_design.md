---
description: FastAPI standards for FFS2 — async routes, Pydantic V2, RBAC via Depends(), schema separation, error handling
activation: always
---

# Backend API Design

> Standards for FastAPI services in FFS2.

---

## Service Architecture

### Protocol

- **Primary planned**: gRPC for inter-service (efficient, typed).
- **Currently implemented**: REST (JSON) for all CRUD, auth, and permissions.
- **Streaming**: Server-Sent Events (SSE) for agent thought streams.

### Framework: FastAPI

- **Async First**: All route handlers must be `async def`.
- **Lifespan**: Use `lifespan` context managers for startup/shutdown (DB connections).
- **Dependency Injection**: Heavy use of `Depends()` for auth, DB sessions, and services.

---

## Data Validation

### Pydantic V2

- **Strict Mode**: Use `ConfigDict(strict=True)` where possible.
- **Aliases**: Use `serialization_alias` for public API compatibility if internal names differ.
- **Environment**: Use `pydantic-settings` for `.env` loading.

### Schema Separation

- **DTOs**: Define separate Request/Response models in `schemas/`.
- **ORM**: SQLAlchemy models in `models/` (never exposed directly).

---

## Error Handling

- **Exceptions**: Raise custom `HTTPException` with error codes.
- **Global Handler**: Middleware to catch unhandled exceptions and return structured JSON error responses.

---

## Router Structure

```python
# src/main.py
app.include_router(auth.router)       # /api/v1/auth
app.include_router(users.router)      # /api/v1/users
app.include_router(apps.router)       # /api/v1/apps
app.include_router(nodes.router)      # /api/v1/apps/{id}/nodes
app.include_router(roles.router)      # /api/v1/users/{id}/assign-role
app.include_router(app_permissions.router)  # /api/v1/apps/{id}/request-access
```

---

## RBAC Pattern

Use `Depends()` for role-based access control:

```python
from src.api.auth import require_collider_admin, get_current_user

# Endpoint restricted to SAD/CAD
@router.post("/{user_id}/assign-role")
async def assign_role(user_id: str, ..., current_user=Depends(require_collider_admin)):
    ...

# Endpoint for any authenticated user
@router.post("/{id}/request-access")
async def request_access(id: str, ..., current_user=Depends(get_current_user)):
    ...
```
