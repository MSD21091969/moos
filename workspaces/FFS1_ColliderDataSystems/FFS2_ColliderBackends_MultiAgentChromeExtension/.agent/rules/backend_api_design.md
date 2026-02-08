# Backend API Design

> Standards for FastAPI services in FFS2.

---

## Service Architecture

### Protocol

- **Primary**: gRPC for inter-service (efficient, typed).
- **Secondary**: REST (JSON) for simple CRUD / Debugging.
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
# app/main.py
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])
```
