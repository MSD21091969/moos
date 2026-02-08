---
description: Backend development patterns for FastAPI, PydanticAI, and Firestore
applyTo: "backend/**"
---

# Backend Instructions

## Architecture
- **Framework:** FastAPI 2.0 (Async)
- **AI Engine:** PydanticAI (Structured outputs, function calling)
- **Database:** Firestore (NoSQL, Realtime)
  - **NO SQL:** Do not use SQL patterns. Use Firestore collections/documents.
- **Auth:** JWT (Google OAuth)
  - **Dev Mode:** `SKIP_AUTH_FOR_TESTING=true` (defaults to enterprise@test.com)

## Terminology Mapping
| User UX | Backend API (v5) |
|---|---|
| **Sticky Note** | `Session` |
| **Agent Card** | `AgentInstance` |
| **Tool Card** | `ToolInstance` |
| **Data Source** | `SourceInstance` |
| **Canvas / Workspace Root** | `UserSession` (L0) |

## Non-Trivial Invariants (UOM)
- **Tree topology:** containers form a strict tree; `parent_id` is the single source of truth.
- **No implicit moves:** require unlink → orphan → adopt (enforced by validation).
- **Cycle safety:** when adding links between containers (especially sessions), validate the operation cannot create cycles (this is a common frontend recursion/crash trigger).

## Observability (Logfire)
- **Query Errors:** `python scripts/logfire_tail.py --hours 1 --min-level error`
- **Trace ID:** Use `logfire` to trace requests across services.

## Best Practices (FastAPI & Pydantic)
### Good Patterns
- **Pydantic Models:** Use `BaseModel` for all request bodies and response schemas.
- **Dependency Injection:** Use `Depends()` for database clients, auth, and config.
- **APIRouter:** Split routes into modules (e.g., `api/routers/sessions.py`).
- **Lifespan Events:** Use `lifespan` context manager for startup/shutdown logic (db connection).
- **Annotated:** Use `Annotated[str, Depends(...)]` for cleaner dependency signatures.
- **Pytest Fixtures:** Use `conftest.py` for shared fixtures (db client, auth headers).
- **TestClient:** Use `fastapi.testclient.TestClient` for API integration tests.

### Bad Patterns
- **Global State:** Avoid global variables for database connections. Use dependencies.
- **Sync I/O:** Never perform blocking I/O (file read, requests) in `async def` routes.
- **Hardcoded Config:** Use `pydantic-settings` or environment variables.
- **Broad Exceptions:** Avoid `except Exception:`. Catch specific errors and raise `HTTPException`.
- **Real External Services in Tests:** Mock external APIs (OpenAI, Stripe) in unit tests.
- **State Leakage:** Ensure DB is cleaned up after tests (use `cleanup_firestore.py` logic).

## Best Practices (Firestore)
- **NoSQL Design:** Design for read patterns. Duplicate data if necessary (denormalization).
- **Batch Writes:** Use `batch()` for multiple writes to ensure atomicity.
- **Converters:** Use `to_dict()` and `from_dict()` methods on models to map to Firestore.

## Container Adoption Rules (Library Pattern)

### Strict Tree Topology
- Every container has **at most one parent** (`parent_id`)
- Containers with `parent_id=None` are **orphans** (available in Library)
- **No implicit moves:** Must `unlink` before `adopt`

### Orphan-Only Adoption
`add_resource()` rejects containers that already have a parent:

```python
# In container_registry.py
if instance_id:
    child = await self._get_container(child_type, instance_id)
    if child.get("parent_id") is not None:
        raise ValidationError(
            f"Container {instance_id} already has parent {child['parent_id']}. "
            "Unlink before adopting elsewhere."
        )
```

### SSE Events
| Action | Event | Effect |
|--------|-------|--------|
| Adopt orphan | `UPDATED` | `parent_id` changes from `None` to `parent_id` |
| Unlink child | `UPDATED` | `parent_id` changes to `None` (becomes orphan) |
| Delete container | `DELETED` | Removed from registry |
