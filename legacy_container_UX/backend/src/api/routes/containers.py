"""Container API routes for unified instance management.

POST /containers/{type} - Create container instance (agent, tool, source)
GET /containers/{type}/{id} - Get container instance with ACL check
PATCH /containers/{type}/{id} - Update container instance
DELETE /containers/{type}/{id} - Delete container instance
GET /containers/{type}/{id}/resources - List container's resources
POST /containers/{type}/{id}/resources - Add resource to container
DELETE /containers/{type}/{id}/resources/{link_id} - Remove resource from container
"""

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel

from src.api.dependencies import get_current_user, get_user_context
from src.core.exceptions import (
    CircularDependencyError,
    DepthLimitError,
    InvalidContainmentError,
    NotFoundError,
    PermissionDeniedError,
)
from src.core.logging import get_logger
from src.models.context import UserContext
from src.models.links import ResourceLink
from src.persistence.firestore_client import get_firestore_client
from src.services.container_service import ContainerService

logger = get_logger(__name__)
router = APIRouter(prefix="/containers", tags=["containers"])


# Request/Response models
class CreateContainerRequest(BaseModel):
    """Request to create container instance."""
    parent_id: str | None = None
    definition_id: str
    title: str | None = None
    description: str | None = None
    preset_params: dict = {}
    input_mappings: dict = {}
    metadata: dict = {}


class ContainerResponse(BaseModel):
    """Response for container instance."""
    instance_id: str
    definition_id: str
    parent_id: str | None
    depth: int
    acl: dict[str, str | list[str]]
    created_at: str
    updated_at: str


class ResourceListResponse(BaseModel):
    """Response for resources list."""
    resources: list[ResourceLink]
    total: int


@router.post(
    "/{container_type}",
    response_model=ContainerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create container instance",
    description="Create agent/tool/source/session instance with ACL and depth validation."
)
async def create_container(
    container_type: str = Path(..., regex="^(agent|tool|source|session)$"),
    request: CreateContainerRequest = ...,
    user_ctx: UserContext = Depends(get_user_context),
    firestore=Depends(get_firestore_client)
):
    """Create container instance.
    
    Validates:
    - User has editor+ on parent
    - Depth doesn't exceed 2
    - Containment rules (e.g., UserSession→Session only)
    - No circular dependencies
    
    Args:
        container_type: "agent", "tool", "source", or "session"
        request: Container creation data
        user_ctx: Authenticated user context
        firestore: Firestore client
        
    Returns:
        Created container
        
    Raises:
        400: Validation failed (depth, containment, cycles)
        403: No edit permission on parent
        404: Parent or definition not found
    """
    service = ContainerService(firestore)
    user_id = user_ctx.user_id
    
    try:
        instance_id = await service.create_instance(
            parent_id=request.parent_id,
            definition_id=request.definition_id,
            container_type=container_type,
            user_id=user_id,
            user_tier=user_ctx.tier,
            title=request.title,
            description=request.description,
            preset_params=request.preset_params,
            input_mappings=request.input_mappings,
            metadata=request.metadata
        )
        
        # Fetch created instance
        instance = await service.get_instance(instance_id, container_type, user_id)
        
        logger.info(
            "Created container instance",
            extra={"instance_id": instance_id, "type": container_type, "user_id": user_id}
        )
        
        return ContainerResponse(
            instance_id=instance["instance_id"],
            definition_id=instance["definition_id"],
            parent_id=instance["parent_id"],
            depth=instance["depth"],
            acl=instance["acl"],
            created_at=instance["created_at"].isoformat(),
            updated_at=instance["updated_at"].isoformat()
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except (DepthLimitError, InvalidContainmentError, CircularDependencyError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to create container",
            extra={"type": container_type, "user_id": user_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create container: {str(e)}"
        )


@router.get(
    "/{container_type}/{instance_id}",
    response_model=ContainerResponse,
    summary="Get container instance",
    description="Get container instance with ACL check (viewer+)."
)
async def get_container(
    container_type: str = Path(..., regex="^(agent|tool|source)$"),
    instance_id: str = ...,
    user_id: str = Depends(get_current_user),
    firestore=Depends(get_firestore_client)
):
    """Get container instance.
    
    Args:
        container_type: "agent", "tool", or "source"
        instance_id: Container instance ID
        user_id: Authenticated user ID
        firestore: Firestore client
        
    Returns:
        Container data
        
    Raises:
        403: No access
        404: Instance not found
    """
    service = ContainerService(firestore)
    
    try:
        instance = await service.get_instance(instance_id, container_type, user_id)
        
        return ContainerResponse(
            instance_id=instance["instance_id"],
            definition_id=instance["definition_id"],
            parent_id=instance["parent_id"],
            depth=instance["depth"],
            acl=instance["acl"],
            created_at=instance["created_at"].isoformat(),
            updated_at=instance["updated_at"].isoformat()
        )
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "cannot access" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        else:
            logger.error(
                "Failed to get container",
                extra={"instance_id": instance_id, "type": container_type, "error": str(e)}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get container: {str(e)}"
            )


@router.patch(
    "/{container_type}/{instance_id}",
    response_model=ContainerResponse,
    summary="Update container instance",
    description="Update container instance (requires editor+)."
)
async def update_container(
    container_type: str = Path(..., regex="^(agent|tool|source)$"),
    instance_id: str = ...,
    updates: dict = ...,
    user_id: str = Depends(get_current_user),
    firestore=Depends(get_firestore_client)
):
    """Update container instance.
    
    Args:
        container_type: "agent", "tool", or "source"
        instance_id: Container instance ID
        updates: Fields to update
        user_id: Authenticated user ID
        firestore: Firestore client
        
    Returns:
        Updated container
        
    Raises:
        403: Not editor+
        404: Instance not found
    """
    service = ContainerService(firestore)
    
    try:
        await service.update_instance(instance_id, container_type, user_id, updates)
        
        # Fetch updated instance
        instance = await service.get_instance(instance_id, container_type, user_id)
        
        logger.info(
            "Updated container instance",
            extra={"instance_id": instance_id, "type": container_type, "user_id": user_id}
        )
        
        return ContainerResponse(
            instance_id=instance["instance_id"],
            definition_id=instance["definition_id"],
            parent_id=instance["parent_id"],
            depth=instance["depth"],
            acl=instance["acl"],
            created_at=instance["created_at"].isoformat(),
            updated_at=instance["updated_at"].isoformat()
        )
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "cannot edit" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        else:
            logger.error(
                "Failed to update container",
                extra={"instance_id": instance_id, "type": container_type, "error": str(e)}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update container: {str(e)}"
            )


@router.delete(
    "/{container_type}/{instance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete container instance",
    description="Delete container instance (requires owner)."
)
async def delete_container(
    container_type: str = Path(..., regex="^(agent|tool|source)$"),
    instance_id: str = ...,
    user_id: str = Depends(get_current_user),
    firestore=Depends(get_firestore_client)
):
    """Delete container instance.
    
    Args:
        container_type: "agent", "tool", or "source"
        instance_id: Container instance ID
        user_id: Authenticated user ID
        firestore: Firestore client
        
    Raises:
        403: Not owner
        404: Instance not found
    """
    service = ContainerService(firestore)
    
    try:
        await service.delete_instance(instance_id, container_type, user_id)
        
        logger.info(
            "Deleted container instance",
            extra={"instance_id": instance_id, "type": container_type, "user_id": user_id}
        )
        
        return None  # 204 No Content
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "only owner" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        else:
            logger.error(
                "Failed to delete container",
                extra={"instance_id": instance_id, "type": container_type, "error": str(e)}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete container: {str(e)}"
            )


# Resource management endpoints

@router.get(
    "/{container_type}/{instance_id}/resources",
    response_model=ResourceListResponse,
    summary="List container resources",
    description="List ResourceLinks in container (requires viewer+)."
)
async def list_container_resources(
    container_type: str = Path(..., regex="^(agent|tool|source)$"),
    instance_id: str = ...,
    resource_type: str | None = None,
    user_id: str = Depends(get_current_user),
    firestore=Depends(get_firestore_client)
):
    """List resources in container.
    
    Args:
        container_type: "agent", "tool", or "source"
        instance_id: Container instance ID
        resource_type: Optional filter by type
        user_id: Authenticated user ID
        firestore: Firestore client
        
    Returns:
        List of ResourceLinks
        
    Raises:
        403: No access
        404: Instance not found
    """
    service = ContainerService(firestore)
    
    try:
        resources = await service.list_resources(
            parent_id=instance_id,
            user_id=user_id,
            resource_type=resource_type
        )
        
        logger.info(
            "Listed container resources",
            extra={
                "instance_id": instance_id,
                "type": container_type,
                "count": len(resources),
                "user_id": user_id
            }
        )
        
        return ResourceListResponse(
            resources=resources,
            total=len(resources)
        )
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "cannot access" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        else:
            logger.error(
                "Failed to list container resources",
                extra={"instance_id": instance_id, "type": container_type, "error": str(e)}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list resources: {str(e)}"
            )


@router.post(
    "/{container_type}/{instance_id}/resources",
    status_code=status.HTTP_201_CREATED,
    summary="Add resource to container",
    description="Add ResourceLink to container (requires editor+)."
)
async def add_container_resource(
    container_type: str = Path(..., regex="^(agent|tool|source)$"),
    instance_id: str = ...,
    link: ResourceLink = ...,
    user_ctx: UserContext = Depends(get_user_context),
    firestore=Depends(get_firestore_client)
):
    """Add resource to container.
    
    Args:
        container_type: "agent", "tool", or "source"
        instance_id: Container instance ID
        link: ResourceLink to add
        user_id: Authenticated user ID
        firestore: Firestore client
        
    Returns:
        Created link_id
        
    Raises:
        403: Not editor+
        404: Instance not found
    """
    service = ContainerService(firestore)
    
    try:
        link_id = await service.add_resource(
            parent_id=instance_id,
            link=link,
            user_id=user_ctx.user_id,
            user_tier=user_ctx.tier,
        )
        
        logger.info(
            "Added resource to container",
            extra={
                "instance_id": instance_id,
                "type": container_type,
                "link_id": link_id,
                "user_id": user_ctx.user_id
            }
        )
        
        return {"link_id": link_id}
    except DepthLimitError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except InvalidContainmentError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to add resource",
            extra={"instance_id": instance_id, "type": container_type, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add resource: {str(e)}"
        )


@router.delete(
    "/{container_type}/{instance_id}/resources/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove resource from container",
    description="Remove ResourceLink from container (requires editor+)."
)
async def remove_container_resource(
    container_type: str = Path(..., regex="^(agent|tool|source)$"),
    instance_id: str = ...,
    link_id: str = ...,
    user_id: str = Depends(get_current_user),
    firestore=Depends(get_firestore_client)
):
    """Remove resource from container.
    
    Args:
        container_type: "agent", "tool", or "source"
        instance_id: Container instance ID
        link_id: ResourceLink document ID
        user_id: Authenticated user ID
        firestore: Firestore client
        
    Raises:
        403: Not editor+
        404: Instance not found
    """
    service = ContainerService(firestore)
    
    try:
        await service.remove_resource(
            parent_id=instance_id,
            link_id=link_id,
            user_id=user_id
        )
        
        logger.info(
            "Removed resource from container",
            extra={
                "instance_id": instance_id,
                "type": container_type,
                "link_id": link_id,
                "user_id": user_id
            }
        )
        
        return None  # 204 No Content
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "cannot edit" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        else:
            logger.error(
                "Failed to remove resource",
                extra={"instance_id": instance_id, "type": container_type, "error": str(e)}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to remove resource: {str(e)}"
            )
