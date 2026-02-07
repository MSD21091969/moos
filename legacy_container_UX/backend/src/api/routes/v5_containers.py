"""v5 Unified Container API - Single endpoint for all container operations.

Replaces separate v4 endpoints:
- /api/v4/sessions/*
- /api/v4/usersessions/*  
- /api/v4/containers/*

All container types use the same API pattern:
- GET/POST /api/v5/containers/{type}
- GET/PUT/DELETE /api/v5/containers/{type}/{id}
- GET/POST/DELETE /api/v5/containers/{type}/{id}/resources
- POST /api/v5/containers/batch
- GET /api/v5/events/containers (SSE)
"""

import asyncio
from datetime import datetime, UTC
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.api.dependencies import get_current_user, get_firestore_client, get_user_context
from src.models.context import UserContext
from src.core.logging import get_logger
from src.models.sessions import SessionCreate, SessionUpdate
from src.models.links import ResourceLink, ResourceType
from src.services.container_service import ContainerService
from src.services.container_registry import (
    ContainerChanged,
    ContainerRegistry,
    ContainerType,
    get_container_registry,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v5", tags=["v5-containers"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ContainerCreateRequest(BaseModel):
    """Request to create a container."""
    parent_id: str = Field(..., description="Parent container ID")
    definition_id: str | None = Field(None, description="Definition ID (None for sessions)")
    title: str | None = Field(None, description="Display title override")
    metadata: dict = Field(default_factory=dict, description="Container metadata")
    preset_params: dict = Field(default_factory=dict, description="Preset parameters")
    input_mappings: dict = Field(default_factory=dict, description="Input mappings")
    
    # Session-specific
    session_metadata: dict | None = Field(None, description="SessionMetadata for session type")


class ContainerUpdateRequest(BaseModel):
    """Request to update a container."""
    title: str | None = None
    metadata: dict | None = None
    status: str | None = None
    acl: dict | None = None
    # Add other updateable fields as needed


class ResourceLinkRequest(BaseModel):
    """Request to add a ResourceLink."""
    resource_type: str = Field(..., description="Type: SESSION, AGENT, TOOL, SOURCE, USER")
    resource_id: str = Field(..., description="Definition ID or direct ID")
    instance_id: str | None = Field(None, description="Instance ID if already created")
    role: str | None = Field(None, description="Role for USER type: owner, editor, viewer")
    description: str | None = None
    preset_params: dict = Field(default_factory=dict)
    input_mappings: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


class BatchOperation(BaseModel):
    """Single operation in a batch request."""
    action: Literal["create", "update", "delete"]
    container_type: str
    container_id: str | None = None  # Required for update/delete
    data: dict = Field(default_factory=dict)


class BatchRequest(BaseModel):
    """Batch operations request."""
    operations: list[BatchOperation]


class ContainerResponse(BaseModel):
    """Standard container response."""
    success: bool = True
    data: dict | None = None
    change_receipt: dict | None = Field(None, description="Event ID and timestamp for cache sync")


class BatchResponse(BaseModel):
    """Batch operations response."""
    success: bool = True
    results: list[dict]


# ============================================================================
# Container Endpoints
# ============================================================================

@router.get("/containers/{container_type}")
async def list_containers(
    container_type: str,
    user_id: str = Depends(get_current_user),
    firestore=Depends(get_firestore_client),
) -> ContainerResponse:
    """List all containers of a type that user has access to."""
    try:
        ctype = ContainerType(container_type.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid container type: {container_type}")
    
    registry = get_container_registry(firestore)
    containers = await registry.get_by_acl(user_id, ctype)
    
    return ContainerResponse(data={"containers": containers})


@router.post("/containers/{container_type}")
async def create_container(
    container_type: str,
    request: ContainerCreateRequest,
    user_ctx: UserContext = Depends(get_user_context),
    firestore=Depends(get_firestore_client),
) -> ContainerResponse:
    """Create a new container."""
    try:
        ctype = ContainerType(container_type.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid container type: {container_type}")
    
    service = ContainerService(firestore)
    user_id = user_ctx.user_id
    user_tier = user_ctx.tier.value
    
    try:
        if ctype == ContainerType.SESSION:
            # Session creation with full metadata
            from src.models.sessions import SessionCreate, SessionMetadata, SessionType
            
            session_meta = request.session_metadata or {
                "title": request.title or "New Session",
                "session_type": "interactive",
            }
            
            # Ensure required fields
            if "title" not in session_meta:
                session_meta["title"] = request.title or "New Session"
            if "session_type" not in session_meta:
                session_meta["session_type"] = "interactive"
            
            create_request = SessionCreate(
                metadata=SessionMetadata(**session_meta),
                parent_id=request.parent_id,
            )
            
            session = await service.create_session(
                user_id=user_id,
                user_tier=user_tier,
                request=create_request,
                parent_id=request.parent_id
            )
            
            return ContainerResponse(
                data=session.model_dump(),
                change_receipt={"timestamp": datetime.now(UTC).isoformat()}
            )
        else:
            # Other container types
            if not request.definition_id:
                raise HTTPException(status_code=400, detail="definition_id required for non-session containers")
            
            instance_id = await service.create_instance(
                parent_id=request.parent_id,
                definition_id=request.definition_id,
                container_type=container_type,
                user_id=user_id,
                user_tier=user_tier,
                title=request.title,
                preset_params=request.preset_params,
                input_mappings=request.input_mappings,
                metadata=request.metadata,
            )
            
            # Get created instance
            data = await service.get_instance(instance_id, container_type, user_id)
            
            return ContainerResponse(
                data=data,
                change_receipt={"timestamp": datetime.now(UTC).isoformat()}
            )
            
    except Exception as e:
        logger.error(f"Failed to create container: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/containers/{container_type}/{container_id}")
async def get_container(
    container_type: str,
    container_id: str,
    user_id: str = Depends(get_current_user),
    firestore=Depends(get_firestore_client),
) -> ContainerResponse:
    """Get a container by ID."""
    try:
        ctype = ContainerType(container_type.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid container type: {container_type}")
    
    registry = get_container_registry(firestore)
    data = await registry.get(ctype, container_id, user_id)
    
    if not data:
        raise HTTPException(status_code=404, detail=f"{container_type} {container_id} not found")
    
    return ContainerResponse(data=data)


@router.put("/containers/{container_type}/{container_id}")
async def update_container(
    container_type: str,
    container_id: str,
    request: ContainerUpdateRequest,
    user_id: str = Depends(get_current_user),
    firestore=Depends(get_firestore_client),
) -> ContainerResponse:
    """Update a container."""
    try:
        ctype = ContainerType(container_type.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid container type: {container_type}")
    
    service = ContainerService(firestore)
    
    # Build updates dict from non-None fields
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    try:
        await service.update_instance(container_id, container_type, user_id, updates)
        
        # Get updated data
        data = await service.get_instance(container_id, container_type, user_id)
        
        return ContainerResponse(
            data=data,
            change_receipt={"timestamp": datetime.now(UTC).isoformat()}
        )
    except Exception as e:
        logger.error(f"Failed to update container: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/containers/{container_type}/{container_id}")
async def delete_container(
    container_type: str,
    container_id: str,
    user_id: str = Depends(get_current_user),
    firestore=Depends(get_firestore_client),
) -> ContainerResponse:
    """Delete a container (owner only)."""
    try:
        ctype = ContainerType(container_type.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid container type: {container_type}")
    
    service = ContainerService(firestore)
    
    try:
        await service.delete_instance(container_id, container_type, user_id)
        return ContainerResponse(
            data={"deleted": container_id},
            change_receipt={"timestamp": datetime.now(UTC).isoformat()}
        )
    except Exception as e:
        logger.error(f"Failed to delete container: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Resource Link Endpoints
# ============================================================================

@router.get("/containers/{container_type}/{container_id}/resources")
async def list_resources(
    container_type: str,
    container_id: str,
    resource_type: str | None = Query(None, description="Filter by resource type"),
    user_id: str = Depends(get_current_user),
    firestore=Depends(get_firestore_client),
) -> ContainerResponse:
    """List ResourceLinks in a container."""
    service = ContainerService(firestore)
    
    try:
        resources = await service.list_resources(container_id, user_id, resource_type)
        return ContainerResponse(data={"resources": [r.model_dump() for r in resources]})
    except Exception as e:
        logger.error(f"Failed to list resources: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/containers/{container_type}/{container_id}/resources")
async def add_resource(
    container_type: str,
    container_id: str,
    request: ResourceLinkRequest,
    user_ctx: UserContext = Depends(get_user_context),
    firestore=Depends(get_firestore_client),
) -> ContainerResponse:
    """Add a ResourceLink to a container."""
    service = ContainerService(firestore)
    user_id = user_ctx.user_id
    user_tier = user_ctx.tier.value
    
    try:
        # Convert to ResourceLink
        link = ResourceLink(
            resource_type=ResourceType(request.resource_type.lower()),
            resource_id=request.resource_id,
            instance_id=request.instance_id,
            role=request.role,
            description=request.description,
            preset_params=request.preset_params,
            input_mappings=request.input_mappings,
            metadata=request.metadata,
            added_by=user_id,
            added_at=datetime.now(UTC),
            enabled=True,
        )
        
        link_id = await service.add_resource(container_id, link, user_id, user_tier)
        
        return ContainerResponse(
            data={"link_id": link_id},
            change_receipt={"timestamp": datetime.now(UTC).isoformat()}
        )
    except Exception as e:
        logger.error(f"Failed to add resource: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/containers/{container_type}/{container_id}/resources/{link_id}")
async def remove_resource(
    container_type: str,
    container_id: str,
    link_id: str,
    user_id: str = Depends(get_current_user),
    firestore=Depends(get_firestore_client),
) -> ContainerResponse:
    """Remove a ResourceLink from a container."""
    service = ContainerService(firestore)
    
    try:
        await service.remove_resource(container_id, link_id, user_id)
        return ContainerResponse(
            data={"removed": link_id},
            change_receipt={"timestamp": datetime.now(UTC).isoformat()}
        )
    except Exception as e:
        logger.error(f"Failed to remove resource: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


class ResourceLinkUpdateRequest(BaseModel):
    """Request to update a ResourceLink."""
    description: str | None = None
    preset_params: dict | None = None
    input_mappings: dict | None = None
    metadata: dict | None = None
    enabled: bool | None = None


@router.patch("/containers/{container_type}/{container_id}/resources/{link_id}")
async def update_resource(
    container_type: str,
    container_id: str,
    link_id: str,
    request: ResourceLinkUpdateRequest,
    user_id: str = Depends(get_current_user),
    firestore=Depends(get_firestore_client),
) -> ContainerResponse:
    """Update a ResourceLink in a container."""
    registry = get_container_registry(firestore)
    
    try:
        ctype = ContainerType(container_type.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid container type: {container_type}")
    
    # Build updates dict from non-None fields
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    try:
        result = await registry.update_resource(ctype, container_id, link_id, updates, user_id)
        
        return ContainerResponse(
            data=result,
            change_receipt={"timestamp": datetime.now(UTC).isoformat()}
        )
    except Exception as e:
        logger.error(f"Failed to update resource: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Batch Operations
# ============================================================================

@router.post("/containers/batch")
async def batch_operations(
    request: BatchRequest,
    user_id: str = Depends(get_current_user),
    firestore=Depends(get_firestore_client),
) -> BatchResponse:
    """Execute multiple container operations in a single request."""
    registry = get_container_registry(firestore)
    
    operations = []
    for op in request.operations:
        operations.append({
            "action": op.action,
            "container_type": op.container_type,
            "container_id": op.container_id,
            "data": op.data,
        })
    
    results = await registry.batch_update(operations, user_id)
    
    return BatchResponse(results=results)


# ============================================================================
# SSE Events Endpoint
# ============================================================================

@router.get("/events/containers")
async def container_events(
    request: Request,
    since: float | None = Query(None, description="Unix timestamp for catch-up"),
    current_user_id: str = Depends(get_current_user),
    firestore=Depends(get_firestore_client),
):
    """Server-Sent Events stream for container changes.
    
    Clients subscribe to receive real-time ContainerChanged events.
    Use ?since=<timestamp> on reconnect to catch up on missed events.
    """
    registry = get_container_registry(firestore)
    user_id = current_user_id
    
    async def event_generator():
        # Send catch-up events if since provided
        if since:
            events = await registry.get_events_since(since)
            for event in events:
                # Filter to events user can see (based on ACL)
                # For now, send all - client can filter
                yield f"data: {event.model_dump_json()}\n\n"
        
        # Subscribe to live events
        queue = registry.subscribe()
        
        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                
                try:
                    # Wait for event with timeout (allows disconnect check)
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {event.model_dump_json()}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f": keepalive {datetime.now(UTC).isoformat()}\n\n"
                    
        finally:
            registry.unsubscribe(queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# ============================================================================
# UserSession Convenience Endpoints
# ============================================================================

@router.get("/workspace")
async def get_workspace(
    current_user_id: str = Depends(get_current_user),
    firestore=Depends(get_firestore_client),
) -> ContainerResponse:
    """Get user's workspace (UserSession + resources).
    
    Convenience endpoint that returns:
    - UserSession data
    - All ResourceLinks (USER + SESSIONs)
    """
    try:
        service = ContainerService(firestore)
        user_id = current_user_id
        
        # Ensure UserSession exists
        usersession = await service.get_or_create_usersession(user_id)
        
        # Get resources
        resources = await service.get_workspace_resources(user_id)
        
        return ContainerResponse(
            data={
                "usersession": usersession.model_dump(),
                "resources": [r.model_dump() for r in resources],
            }
        )
    except Exception as e:
        logger.error(f"get_workspace failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workspace/sync")
async def sync_workspace(
    current_user_id: str = Depends(get_current_user),
    firestore=Depends(get_firestore_client),
) -> ContainerResponse:
    """Sync workspace with ACL-permitted sessions.
    
    Discovers sessions shared with user and adds/removes ResourceLinks.
    Called on login or manual refresh.
    """
    from src.services.usersession_service import UserSessionService
    
    usersession_service = UserSessionService(firestore)
    user_id = current_user_id
    
    changes = await usersession_service.sync_session_links(user_id)
    
    # Get updated resources
    service = ContainerService(firestore)
    resources = await service.get_workspace_resources(user_id)
    
    return ContainerResponse(
        data={
            "changes": changes,
            "resources": [r.model_dump() for r in resources],
        },
        change_receipt={"timestamp": datetime.now(UTC).isoformat()}
    )
