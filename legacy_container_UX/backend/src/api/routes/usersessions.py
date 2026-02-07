"""UserSession API routes for workspace management.

GET /usersessions/{user_id} - Get or create user's workspace root
GET /usersessions/{user_id}/resources - List ACL-permitted sessions
POST /usersessions/{user_id}/resources - Add resource to workspace
PATCH /usersessions/{user_id}/resources/{link_id} - Update resource
DELETE /usersessions/{user_id}/resources/{link_id} - Remove resource
"""

from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.dependencies import get_current_user
from src.core.logging import get_logger
from src.models.containers import UserSession
from src.models.links import ResourceLink, ResourceType
from src.persistence.firestore_client import get_firestore_client
from src.services.usersession_service import UserSessionService

logger = get_logger(__name__)
router = APIRouter(prefix="/usersessions", tags=["usersessions"])


class UserSessionResponse(BaseModel):
    """Response model for UserSession."""
    instance_id: str
    depth: int
    acl: dict[str, str | list[str]]
    created_at: str
    updated_at: str


class ResourceListResponse(BaseModel):
    """Response model for resources list."""
    resources: list[ResourceLink]
    total: int


class AddWorkspaceResourceRequest(BaseModel):
    """Request to add a resource link to workspace."""
    resource_id: str
    resource_type: ResourceType
    description: str | None = None
    preset_params: dict = {}
    input_mappings: dict = {}
    metadata: dict = {}


class UpdateWorkspaceResourceRequest(BaseModel):
    """Request to update a resource link in workspace."""
    description: str | None = None
    preset_params: dict | None = None
    input_mappings: dict | None = None
    metadata: dict | None = None
    enabled: bool | None = None


@router.get(
    "/{user_id}",
    response_model=UserSessionResponse,
    summary="Get or create UserSession",
    description="Get user's workspace root (L0). Creates if doesn't exist (sign-in flow)."
)
async def get_usersession(
    user_id: str,
    current_user_id: str = Depends(get_current_user),
    firestore=Depends(get_firestore_client)
):
    """Get or create user's workspace root (L0 container).
    
    Args:
        user_id: User identifier
        current_user_id: Authenticated user ID from JWT
        firestore: Firestore client
        
    Returns:
        UserSession data
        
    Raises:
        403: If current_user_id != user_id (can only access own workspace)
    """
    # ACL: Users can only access their own workspace
    if current_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access another user's workspace"
        )
    
    service = UserSessionService(firestore)
    
    try:
        usersession = await service.get_or_create(user_id)
        
        # Sync ACL-permitted sessions on login (not on every read)
        # L0 sharing is visibility-only, no data dependency - safe to sync once
        await service.sync_session_links(user_id)
        
        return UserSessionResponse(
            instance_id=usersession.instance_id,
            depth=usersession.depth,
            acl=usersession.acl,
            created_at=usersession.created_at.isoformat(),
            updated_at=usersession.updated_at.isoformat()
        )
    except Exception as e:
        logger.error(
            "Failed to get UserSession",
            extra={"user_id": user_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workspace: {str(e)}"
        )


@router.get(
    "/{user_id}/resources",
    response_model=ResourceListResponse,
    summary="List workspace resources",
    description="List ResourceLinks in user's workspace (USER + SESSION types with ACL filtering)."
)
async def list_workspace_resources(
    user_id: str,
    current_user_id: str = Depends(get_current_user),
    firestore=Depends(get_firestore_client)
):
    """List resources in user's workspace (L0 container).
    
    Returns USER ResourceLink + SESSION ResourceLinks for ACL-permitted sessions.
    
    Args:
        user_id: User identifier
        current_user_id: Authenticated user ID from JWT
        firestore: Firestore client
        
    Returns:
        List of ResourceLinks
        
    Raises:
        403: If current_user_id != user_id
    """
    # ACL: Users can only access their own workspace
    if current_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access another user's workspace"
        )
    
    service = UserSessionService(firestore)
    
    try:
        # NOTE: sync_session_links moved to get_usersession (login) - not needed on every read
        # L0 sharing is visibility-only, sync on login is sufficient
        resources = await service.get_resources(user_id)
        
        logger.info(
            "Listed workspace resources",
            extra={"user_id": user_id, "count": len(resources)}
        )
        
        return ResourceListResponse(
            resources=resources,
            total=len(resources)
        )
    except Exception as e:
        logger.error(
            "Failed to list workspace resources",
            extra={"user_id": user_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list resources: {str(e)}"
        )


@router.post(
    "/{user_id}/resources",
    response_model=ResourceLink,
    status_code=status.HTTP_201_CREATED,
    summary="Add resource to workspace",
    description="Add a ResourceLink (SESSION or USER type) to user's workspace."
)
async def add_workspace_resource(
    user_id: str,
    request: AddWorkspaceResourceRequest,
    current_user_id: str = Depends(get_current_user),
    firestore=Depends(get_firestore_client)
):
    """Add a resource link to user's workspace (L0 container).
    
    Only SESSION and USER types are allowed at workspace level.
    
    Args:
        user_id: User identifier
        request: Resource link data
        current_user_id: Authenticated user ID from JWT
        firestore: Firestore client
        
    Returns:
        Created ResourceLink with generated link_id
        
    Raises:
        400: If resource_type is not SESSION or USER
        403: If current_user_id != user_id
    """
    # ACL: Users can only modify their own workspace
    if current_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify another user's workspace"
        )
    
    # Validate: Only SESSION and USER allowed at workspace level
    if request.resource_type not in (ResourceType.SESSION, ResourceType.USER):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only SESSION and USER types allowed at workspace level, got: {request.resource_type.value}"
        )
    
    service = UserSessionService(firestore)
    
    try:
        # Create ResourceLink
        link = ResourceLink(
            resource_id=request.resource_id,
            resource_type=request.resource_type,
            description=request.description,
            preset_params=request.preset_params,
            input_mappings=request.input_mappings,
            metadata=request.metadata,
            added_at=datetime.now(UTC),
            added_by=current_user_id,
            enabled=True,
        )
        
        created_link = await service.add_resource(user_id, link)
        
        logger.info(
            "Added workspace resource",
            extra={
                "user_id": user_id,
                "link_id": created_link.link_id,
                "resource_type": request.resource_type.value,
                "resource_id": request.resource_id,
            }
        )
        
        return created_link
        
    except Exception as e:
        logger.error(
            "Failed to add workspace resource",
            extra={"user_id": user_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add resource: {str(e)}"
        )


@router.get(
    "/{user_id}/resources/{link_id}",
    response_model=ResourceLink,
    summary="Get workspace resource",
    description="Get a single ResourceLink by link_id from user's workspace."
)
async def get_workspace_resource(
    user_id: str,
    link_id: str,
    current_user_id: str = Depends(get_current_user),
    firestore=Depends(get_firestore_client)
):
    """Get a single resource from user's workspace.
    
    Args:
        user_id: User identifier
        link_id: ResourceLink ID
        current_user_id: Authenticated user ID from JWT
        firestore: Firestore client
        
    Returns:
        ResourceLink
        
    Raises:
        403: If current_user_id != user_id
        404: If resource not found
    """
    # ACL: Users can only access their own workspace
    if current_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access another user's workspace"
        )
    
    service = UserSessionService(firestore)
    
    try:
        resource = await service.get_resource(user_id, link_id)
        
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resource '{link_id}' not found"
            )
        
        return resource
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get workspace resource",
            extra={"user_id": user_id, "link_id": link_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get resource: {str(e)}"
        )


@router.patch(
    "/{user_id}/resources/{link_id}",
    response_model=ResourceLink,
    summary="Update workspace resource",
    description="Update a ResourceLink in user's workspace."
)
async def update_workspace_resource(
    user_id: str,
    link_id: str,
    request: UpdateWorkspaceResourceRequest,
    current_user_id: str = Depends(get_current_user),
    firestore=Depends(get_firestore_client)
):
    """Update a resource link in user's workspace.
    
    Supports partial updates to: description, preset_params, input_mappings, metadata, enabled.
    
    Args:
        user_id: User identifier
        link_id: ResourceLink ID
        request: Fields to update
        current_user_id: Authenticated user ID from JWT
        firestore: Firestore client
        
    Returns:
        Updated ResourceLink
        
    Raises:
        403: If current_user_id != user_id
        404: If resource not found
    """
    # ACL: Users can only modify their own workspace
    if current_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify another user's workspace"
        )
    
    service = UserSessionService(firestore)
    
    try:
        # Build updates dict from non-None fields
        updates = {}
        if request.description is not None:
            updates["description"] = request.description
        if request.preset_params is not None:
            updates["preset_params"] = request.preset_params
        if request.input_mappings is not None:
            updates["input_mappings"] = request.input_mappings
        if request.metadata is not None:
            updates["metadata"] = request.metadata
        if request.enabled is not None:
            updates["enabled"] = request.enabled
        
        updated_link = await service.update_resource(user_id, link_id, updates)
        
        if not updated_link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resource '{link_id}' not found"
            )
        
        logger.info(
            "Updated workspace resource",
            extra={"user_id": user_id, "link_id": link_id, "fields": list(updates.keys())}
        )
        
        return updated_link
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update workspace resource",
            extra={"user_id": user_id, "link_id": link_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update resource: {str(e)}"
        )


@router.delete(
    "/{user_id}/resources/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove workspace resource",
    description="Remove a ResourceLink from user's workspace."
)
async def remove_workspace_resource(
    user_id: str,
    link_id: str,
    current_user_id: str = Depends(get_current_user),
    firestore=Depends(get_firestore_client)
):
    """Remove a resource link from user's workspace.
    
    Note: Owner USER links cannot be deleted (system-defined).
    
    Args:
        user_id: User identifier
        link_id: ResourceLink ID
        current_user_id: Authenticated user ID from JWT
        firestore: Firestore client
        
    Raises:
        403: If current_user_id != user_id or trying to delete owner link
        404: If resource not found
    """
    # ACL: Users can only modify their own workspace
    if current_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify another user's workspace"
        )
    
    service = UserSessionService(firestore)
    
    try:
        deleted = await service.remove_resource(user_id, link_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resource '{link_id}' not found"
            )
        
        logger.info(
            "Removed workspace resource",
            extra={"user_id": user_id, "link_id": link_id}
        )
        
        return None
        
    except HTTPException:
        raise
    except ValueError as e:
        # Owner protection
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "Failed to remove workspace resource",
            extra={"user_id": user_id, "link_id": link_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove resource: {str(e)}"
        )
