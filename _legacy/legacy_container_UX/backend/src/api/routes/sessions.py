"""Session management API endpoints.

Handles:
- Create new session
- List user sessions (with pagination)
- Get session details
- Update session metadata
- Delete/archive session
- Get/export message history
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ValidationError as PydanticValidationError

from src.api.dependencies import get_session_service, get_user_context
from src.api.models import (
    BatchSessionCreateRequest,
    BatchSessionCreateResponse,
    SessionCreateRequest,
    SessionListResponse,
    SessionResponse,
    SessionUpdateRequest,
)
from src.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from src.core.logging import get_logger
from src.models.context import UserContext
from src.models.sessions import (
    SessionCreate,
    SessionMetadata,
    SessionStatus,
    SessionType,
)
from src.services.session_service import SessionService

logger = get_logger(__name__)
router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(
    request: SessionCreateRequest,
    user_ctx: UserContext = Depends(get_user_context),
    session_service: SessionService = Depends(get_session_service),
):
    """
    Create a new session.

    **Authentication Required**: Yes (JWT token)

    **Validation**:
    - `title`: 1-200 chars, required
    - `session_type`: chat|analysis|workflow
    - `ttl_hours`: 1-8760 (max 365 days)
    - `tags`: max 10 tags, each 1-50 chars

    **Session Lifecycle**:
    1. Created → Active (immediately)
    2. Auto-expires after TTL (default 24h)
    3. Can be archived/deleted manually

    **Use Cases**:
    - **Conversational**: Multi-turn chat with persistent history
    - **Analysis**: Data analysis with tool execution tracking
    - **Workflow**: Multi-step automated tasks

    **Frontend Integration**:
    ```typescript
    const session = await fetch('/sessions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        title: 'Q4 Data Analysis',
        session_type: 'analysis',
        tags: ['finance', 'quarterly'],
        ttl_hours: 48
      })
    }).then(r => r.json());

    // Use session_id for subsequent agent calls
    const result = await runAgent(message, session.session_id);
    ```
    """
    try:
        logger.info(
            "Creating session for user",
            extra={"user_id": user_ctx.user_id, "tier": user_ctx.tier.value},
        )
        try:
            session_type = SessionType(request.session_type)
        except ValueError as exc:
            raise HTTPException(
                status_code=400, detail=f"Invalid session_type: {request.session_type}"
            ) from exc

        session_create = SessionCreate(
            metadata=SessionMetadata(
                title=request.title,
                description=request.description,
                tags=request.tags,
                session_type=session_type,
                ttl_hours=request.ttl_hours,
                domain=request.domain,
                scenario=request.scenario,
                is_container=request.is_container,
                child_node_ids=request.child_node_ids,
                visual_metadata=request.visual_metadata,
            ),
            initial_collections={},
            clone_from_session_id=request.clone_from_session_id,
            parent_session_id=request.parent_session_id,
        )
        session = await session_service.create(
            user_id=user_ctx.user_id, user_tier=user_ctx.tier, request=session_create
        )
        return SessionResponse(
            session_id=session.session_id,
            title=session.metadata.title,
            description=session.metadata.description,
            tags=session.metadata.tags,
            session_type=session.metadata.session_type,
            status=session.status,
            created_at=session.created_at,
            updated_at=session.updated_at,
            expires_at=session.expires_at,
            is_active=session.is_active,
            domain=session.metadata.domain,
            scenario=session.metadata.scenario,
            active_agent_id=session.active_agent_id,
            is_shared=session.is_shared,
            shared_with_users=session.shared_with_users,
            source_session_id=None,  # Deprecated in v4.0.0, use parent_id
            parent_session_id=session.parent_session_id,
            child_sessions=session.child_sessions,
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PydanticValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())
    except Exception as e:
        logger.error("Failed to create session", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=BatchSessionCreateResponse, status_code=201)
async def create_sessions_batch(
    request: BatchSessionCreateRequest,
    user_ctx: UserContext = Depends(get_user_context),
    session_service: SessionService = Depends(get_session_service),
):
    """
    Create multiple sessions in a single batch operation (max 25 sessions).

    **Authentication Required**: Yes (JWT token)

    **Use Case**: Frontend staging queue creating multiple sessions at once
    (e.g., "Group 5 nodes into container" → 5 child sessions + 1 container)

    **Validation**:
    - Max 25 sessions per batch (reduced from 50 for Firestore transaction safety)
    - Each session validated independently
    - Tier limits checked upfront for entire batch
    - Partial success allowed: returns successful sessions + error details

    **Response**:
    - `sessions`: Array of successfully created sessions
    - `total`: Total sessions requested
    - `success_count`: Number of successfully created sessions
    - `failed_count`: Number of failed sessions
    - `errors`: Array of error details: [{index, title, error}]

    **Frontend Integration**:
    ```typescript
    const response = await fetch('/sessions/batch', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        sessions: [
          {title: 'Child 1', parent_session_id: 'sess_abc123', session_type: 'chat'},
          {title: 'Child 2', parent_session_id: 'sess_abc123', session_type: 'chat'},
        ]
      })
    }).then(r => r.json());

    // Handle partial success
    if (response.failed_count > 0) {
      console.error('Some sessions failed:', response.errors);
    }
    ```

    **Error Handling**:
    - 400: Invalid request (validation failure, batch too large)
    - 429: Quota exceeded (tier session limit reached)
    - 500: Internal server error
    """
    try:
        logger.info(
            "Batch creating sessions for user",
            extra={
                "user_id": user_ctx.user_id,
                "tier": user_ctx.tier.value,
                "batch_size": len(request.sessions),
            },
        )

        # Convert API requests to domain SessionCreate objects
        session_creates = []
        for req in request.sessions:
            try:
                session_type = SessionType(req.session_type)
            except ValueError as exc:
                raise HTTPException(
                    status_code=400, detail=f"Invalid session_type: {req.session_type}"
                ) from exc

            session_creates.append(
                SessionCreate(
                    metadata=SessionMetadata(
                        title=req.title,
                        description=req.description,
                        tags=req.tags,
                        session_type=session_type,
                        ttl_hours=req.ttl_hours,
                        domain=req.domain,
                        scenario=req.scenario,
                        is_container=req.is_container,
                        child_node_ids=req.child_node_ids,
                        visual_metadata=req.visual_metadata,
                    ),
                    initial_collections={},
                    clone_from_session_id=req.clone_from_session_id,
                    parent_session_id=req.parent_session_id,
                )
            )

        # Execute batch creation
        created_sessions, errors = await session_service.create_batch(
            user_id=user_ctx.user_id, user_tier=user_ctx.tier, requests=session_creates
        )

        # Convert domain sessions to API responses
        session_responses = [
            SessionResponse(
                session_id=s.session_id,
                title=s.metadata.title,
                description=s.metadata.description,
                tags=s.metadata.tags,
                session_type=s.metadata.session_type,
                status=s.status,
                created_at=s.created_at,
                updated_at=s.updated_at,
                expires_at=s.expires_at,
                is_active=s.is_active,
                domain=s.metadata.domain,
                scenario=s.metadata.scenario,
                active_agent_id=s.active_agent_id,
                is_shared=s.is_shared,
                shared_with_users=s.shared_with_users,
                source_session_id=None,
                parent_session_id=s.parent_session_id,
                child_sessions=s.child_sessions,
            )
            for s in created_sessions
        ]

        return BatchSessionCreateResponse(
            sessions=session_responses,
            total=len(request.sessions),
            success_count=len(created_sessions),
            failed_count=len(errors),
            errors=errors,
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PydanticValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())
    except Exception as e:
        logger.error("Failed to batch create sessions", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    session_type: Optional[str] = Query(None, description="Filter by session type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    parent_session_id: Optional[str] = Query(
        None, description="Filter by parent session ID (for container children)"
    ),
    user_ctx: UserContext = Depends(get_user_context),
    session_service: SessionService = Depends(get_session_service),
):
    """
    List user's sessions with pagination and filtering.

    **Authentication Required**: Yes

    **Use Case**: Frontend "My Sessions" page with filters
    """
    try:
        from src.models.sessions import SessionStatus

        # Convert status string to enum if provided
        status_filter = SessionStatus(status) if status else None

        # Get sessions from service
        sessions, total = await session_service.list_user_sessions(
            user_id=user_ctx.user_id,
            status=status_filter,
            page=page,
            page_size=page_size,
            parent_session_id=parent_session_id,
        )

        # Convert domain models to API response models
        session_responses = [
            SessionResponse(
                session_id=s.session_id,
                title=s.metadata.title,
                description=s.metadata.description,
                tags=s.metadata.tags,
                session_type=s.metadata.session_type,
                status=s.status,
                created_at=s.created_at,
                updated_at=s.updated_at,
                expires_at=s.expires_at,
                is_active=s.is_active,
                domain=s.metadata.domain,
                scenario=s.metadata.scenario,
                active_agent_id=s.active_agent_id,
                is_shared=s.is_shared,
                shared_with_users=s.shared_with_users,
                source_session_id=None,
                collection_schemas=s.collection_schemas,
                parent_session_id=s.parent_session_id,
                child_sessions=s.child_sessions,
            )
            for s in sessions
        ]

        has_more = total > (page * page_size)

        return SessionListResponse(
            sessions=session_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more,
        )
    except Exception as e:
        logger.error("Failed to list sessions", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    user_ctx: UserContext = Depends(get_user_context),
    session_service: SessionService = Depends(get_session_service),
):
    """
    Get session details by ID.

    **Authentication Required**: Yes
    **Authorization**: User must own the session

    **Use Case**: Frontend loading session details
    """
    try:
        from src.core.exceptions import NotFoundError, PermissionDeniedError

        session = await session_service.get(session_id=session_id, user_id=user_ctx.user_id)

        return SessionResponse(
            session_id=session.session_id,
            title=session.metadata.title,
            description=session.metadata.description,
            tags=session.metadata.tags,
            session_type=session.metadata.session_type,
            status=session.status,
            created_at=session.created_at,
            updated_at=session.updated_at,
            expires_at=session.expires_at,
            is_active=session.is_active,
            domain=session.metadata.domain,
            scenario=session.metadata.scenario,
            active_agent_id=session.active_agent_id,
            is_shared=session.is_shared,
            shared_with_users=session.shared_with_users,
            source_session_id=None,
            collection_schemas=session.collection_schemas,
            parent_session_id=session.parent_session_id,
            child_sessions=session.child_sessions,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to get session",
            extra={"session_id": session_id, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    request: SessionUpdateRequest,
    user_ctx: UserContext = Depends(get_user_context),
    session_service: SessionService = Depends(get_session_service),
):
    """
    Update session metadata.

    **Use Case**: User renames session, adds tags, marks as completed
    """
    try:
        # Build SessionUpdate from request
        from src.models.sessions import SessionUpdate

        # Only include fields that were actually provided
        update_dict = {}
        if request.title is not None:
            update_dict["title"] = request.title
        if request.description is not None:
            update_dict["description"] = request.description
        if request.tags is not None:
            update_dict["tags"] = request.tags
        if request.status is not None:
            update_dict["status"] = SessionStatus(request.status)
        if request.active_agent_id is not None:
            update_dict["active_agent_id"] = request.active_agent_id
        if request.domain is not None:
            update_dict["domain"] = request.domain
        if request.scenario is not None:
            update_dict["scenario"] = request.scenario
        if request.visual_metadata is not None:
            update_dict["visual_metadata"] = request.visual_metadata
        if request.theme_color is not None:
            update_dict["theme_color"] = request.theme_color
        if request.collections_to_add is not None:
            update_dict["collections_to_add"] = request.collections_to_add
        if request.collections_to_remove is not None:
            update_dict["collections_to_remove"] = request.collections_to_remove

        update_data = SessionUpdate(**update_dict)

        # Use service layer for update
        updated_session = await session_service.update(
            session_id=session_id,
            user_id=user_ctx.user_id,
            update_data=update_data,
        )

        return SessionResponse(
            session_id=updated_session.session_id,
            title=updated_session.metadata.title,
            description=updated_session.metadata.description,
            tags=updated_session.metadata.tags,
            session_type=updated_session.metadata.session_type,
            status=updated_session.status,
            created_at=updated_session.created_at,
            updated_at=updated_session.updated_at,
            expires_at=updated_session.expires_at,
            is_active=updated_session.is_active,
            domain=updated_session.metadata.domain,
            scenario=updated_session.metadata.scenario,
            active_agent_id=updated_session.active_agent_id,
            is_shared=updated_session.is_shared,
            shared_with_users=updated_session.shared_with_users,
            source_session_id=None,
            parent_session_id=updated_session.parent_session_id,
            child_sessions=updated_session.child_sessions,
        )

    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to update session",
            extra={"session_id": session_id, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    cascade: bool = Query(False, description="If true, recursively delete all child sessions"),
    user_ctx: UserContext = Depends(get_user_context),
    session_service: SessionService = Depends(get_session_service),
):
    """
    Delete/archive a session.

    **Authentication Required**: Yes
    **Authorization**: User must own the session

    **Behavior**: Soft delete - marks as archived, doesn't remove data

    **Use Case**: User wants to clean up old sessions
    """
    try:
        await session_service.delete(
            session_id=session_id, user_id=user_ctx.user_id, cascade=cascade
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to delete session",
            extra={"session_id": session_id, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/share", response_model=SessionResponse)
async def share_session(
    session_id: str,
    user_ids: list[str] = Query(..., description="List of user IDs to grant access to"),
    user_ctx: UserContext = Depends(get_user_context),
    session_service: SessionService = Depends(get_session_service),
):
    """
    Share session with other users (grant read access).

    **Authentication Required**: Yes (must be session owner)

    **Permissions**: Only session owner can share

    **ACL**: Adds users to shared_with_users list

    Args:
        session_id: Session to share
        user_ids: List of user IDs to grant access to

    Returns:
        Updated session with new ACL

    Raises:
        403: User is not session owner
        404: Session not found
        500: Internal error
    """
    try:
        updated_session = await session_service.share_session(
            session_id=session_id,
            owner_user_id=user_ctx.user_id,
            target_user_ids=user_ids,
        )

        return SessionResponse(
            session_id=updated_session.session_id,
            title=updated_session.metadata.title,
            description=updated_session.metadata.description,
            tags=updated_session.metadata.tags,
            session_type=updated_session.metadata.session_type,
            status=updated_session.status,
            created_at=updated_session.created_at,
            updated_at=updated_session.updated_at,
            expires_at=updated_session.expires_at,
            is_active=updated_session.is_active,
            domain=updated_session.metadata.domain,
            scenario=updated_session.metadata.scenario,
            active_agent_id=updated_session.active_agent_id,
            is_shared=updated_session.is_shared,
            shared_with_users=updated_session.shared_with_users,
            source_session_id=None,
            collection_schemas=updated_session.collection_schemas,
            parent_session_id=updated_session.parent_session_id,
            child_sessions=updated_session.child_sessions,
        )

    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to share session",
            extra={"session_id": session_id, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/unshare", response_model=SessionResponse)
async def unshare_session(
    session_id: str,
    user_ids: list[str] = Query(..., description="List of user IDs to revoke access from"),
    user_ctx: UserContext = Depends(get_user_context),
    session_service: SessionService = Depends(get_session_service),
):
    """
    Revoke session access from users.

    **Authentication Required**: Yes (must be session owner)

    **Permissions**: Only session owner can unshare

    **ACL**: Removes users from shared_with_users list

    Args:
        session_id: Session to unshare
        user_ids: List of user IDs to revoke access from

    Returns:
        Updated session with modified ACL

    Raises:
        403: User is not session owner
        404: Session not found
        500: Internal error
    """
    try:
        updated_session = await session_service.unshare_session(
            session_id=session_id,
            owner_user_id=user_ctx.user_id,
            target_user_ids=user_ids,
        )

        return SessionResponse(
            session_id=updated_session.session_id,
            title=updated_session.metadata.title,
            description=updated_session.metadata.description,
            tags=updated_session.metadata.tags,
            session_type=updated_session.metadata.session_type,
            status=updated_session.status,
            created_at=updated_session.created_at,
            updated_at=updated_session.updated_at,
            expires_at=updated_session.expires_at,
            is_active=updated_session.is_active,
            domain=updated_session.metadata.domain,
            scenario=updated_session.metadata.scenario,
            active_agent_id=updated_session.active_agent_id,
            is_shared=updated_session.is_shared,
            shared_with_users=updated_session.shared_with_users,
            source_session_id=None,
            collection_schemas=updated_session.collection_schemas,
            parent_session_id=updated_session.parent_session_id,
            child_sessions=updated_session.child_sessions,
        )

    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to unshare session",
            extra={"session_id": session_id, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))
