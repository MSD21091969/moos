"""Definition API routes for agent/tool/source registry management.

GET /definitions/{type} - List available definitions (system + custom with tier+ACL)
POST /definitions/{type} - Create custom definition (PRO/ENT only)
GET /definitions/{type}/{id} - Get definition by ID
PATCH /definitions/{type}/{id} - Update custom definition (owner/editor)
DELETE /definitions/{type}/{id} - Delete custom definition (owner only)
"""

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel

from src.api.dependencies import get_current_user
from src.core.logging import get_logger
from src.persistence.firestore_client import get_firestore_client
from src.services.definition_service import DefinitionService

logger = get_logger(__name__)
router = APIRouter(prefix="/definitions", tags=["definitions"])


# Response models
class DefinitionListResponse(BaseModel):
    """Response for list endpoint."""
    definitions: list[dict]
    total: int


class DefinitionResponse(BaseModel):
    """Response for single definition."""
    definition: dict


# Request models
class CreateDefinitionRequest(BaseModel):
    """Request to create custom definition."""
    title: str
    description: str | None = None
    tags: list[str] | None = None
    category: str | None = None
    # Type-specific fields in nested dict
    spec: dict


@router.get(
    "/{definition_type}",
    response_model=DefinitionListResponse,
    summary="List available definitions",
    description="List definitions available to user (system + custom with tier+ACL filtering)."
)
async def list_definitions(
    definition_type: str = Path(..., regex="^(agent|tool|source)$"),
    user_id: str = Depends(get_current_user),
    firestore=Depends(get_firestore_client)
):
    """List definitions available to user.
    
    Includes:
    - System definitions (if tier permits)
    - Custom definitions (if ACL permits and tier permits)
    
    Args:
        definition_type: "agent", "tool", or "source"
        user_id: Authenticated user ID
        firestore: Firestore client
        
    Returns:
        List of definitions
    """
    service = DefinitionService(firestore)
    
    # TODO: Get user tier from user document or JWT claims
    # For now, default to PRO
    user_tier = "PRO"
    
    try:
        definitions = await service.list_available_definitions(
            definition_type=definition_type,
            user_id=user_id,
            user_tier=user_tier
        )
        
        logger.info(
            "Listed definitions",
            extra={
                "type": definition_type,
                "count": len(definitions),
                "user_id": user_id,
                "tier": user_tier
            }
        )
        
        return DefinitionListResponse(
            definitions=[d.model_dump() if hasattr(d, "model_dump") else d for d in definitions],
            total=len(definitions)
        )
    except Exception as e:
        logger.error(
            "Failed to list definitions",
            extra={"type": definition_type, "user_id": user_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list definitions: {str(e)}"
        )


@router.post(
    "/{definition_type}",
    response_model=DefinitionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create custom definition",
    description="Create custom agent/tool/source definition (requires PRO or ENT tier)."
)
async def create_definition(
    definition_type: str = Path(..., regex="^(agent|tool|source)$"),
    request: CreateDefinitionRequest = ...,
    user_id: str = Depends(get_current_user),
    firestore=Depends(get_firestore_client)
):
    """Create custom definition (PRO/ENT only).
    
    Args:
        definition_type: "agent", "tool", or "source"
        request: Definition data
        user_id: Authenticated user ID
        firestore: Firestore client
        
    Returns:
        Created definition
        
    Raises:
        403: If tier is FREE
    """
    service = DefinitionService(firestore)
    
    # TODO: Get user tier from user document or JWT claims
    user_tier = "PRO"
    
    # Merge base fields + spec
    definition_data = {
        "title": request.title,
        "description": request.description,
        "tags": request.tags or [],
        "category": request.category,
        **request.spec  # Merge type-specific fields
    }
    
    try:
        definition_id = await service.create_definition(
            definition_type=definition_type,
            definition_data=definition_data,
            user_id=user_id,
            user_tier=user_tier
        )
        
        # Fetch created definition
        definition = await service.get_definition(definition_id, definition_type, user_id)
        
        logger.info(
            "Created custom definition",
            extra={"definition_id": definition_id, "type": definition_type, "user_id": user_id}
        )
        
        return DefinitionResponse(definition=definition)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "Failed to create definition",
            extra={"type": definition_type, "user_id": user_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create definition: {str(e)}"
        )


@router.get(
    "/{definition_type}/{definition_id}",
    response_model=DefinitionResponse,
    summary="Get definition by ID",
    description="Get specific definition (system or custom with ACL check)."
)
async def get_definition(
    definition_type: str = Path(..., regex="^(agent|tool|source)$"),
    definition_id: str = ...,
    user_id: str = Depends(get_current_user),
    firestore=Depends(get_firestore_client)
):
    """Get definition by ID.
    
    Args:
        definition_type: "agent", "tool", or "source"
        definition_id: Definition ID
        user_id: Authenticated user ID
        firestore: Firestore client
        
    Returns:
        Definition data
        
    Raises:
        404: Definition not found
        403: No access to custom definition
    """
    service = DefinitionService(firestore)
    
    try:
        definition = await service.get_definition(definition_id, definition_type, user_id)
        
        return DefinitionResponse(definition=definition)
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
                "Failed to get definition",
                extra={"definition_id": definition_id, "type": definition_type, "error": str(e)}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get definition: {str(e)}"
            )


@router.patch(
    "/{definition_type}/{definition_id}",
    response_model=DefinitionResponse,
    summary="Update custom definition",
    description="Update custom definition (requires owner or editor role)."
)
async def update_definition(
    definition_type: str = Path(..., regex="^(agent|tool|source)$"),
    definition_id: str = ...,
    updates: dict = ...,
    user_id: str = Depends(get_current_user),
    firestore=Depends(get_firestore_client)
):
    """Update custom definition (owner/editor only).
    
    Args:
        definition_type: "agent", "tool", or "source"
        definition_id: Definition ID
        updates: Fields to update
        user_id: Authenticated user ID
        firestore: Firestore client
        
    Returns:
        Updated definition
        
    Raises:
        403: Not owner/editor or system definition
        404: Definition not found
    """
    service = DefinitionService(firestore)
    
    try:
        await service.update_definition(definition_id, definition_type, updates, user_id)
        
        # Fetch updated definition
        definition = await service.get_definition(definition_id, definition_type, user_id)
        
        logger.info(
            "Updated custom definition",
            extra={"definition_id": definition_id, "type": definition_type, "user_id": user_id}
        )
        
        return DefinitionResponse(definition=definition)
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "cannot" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        else:
            logger.error(
                "Failed to update definition",
                extra={"definition_id": definition_id, "type": definition_type, "error": str(e)}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update definition: {str(e)}"
            )


@router.delete(
    "/{definition_type}/{definition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete custom definition",
    description="Delete custom definition (requires owner role)."
)
async def delete_definition(
    definition_type: str = Path(..., regex="^(agent|tool|source)$"),
    definition_id: str = ...,
    user_id: str = Depends(get_current_user),
    firestore=Depends(get_firestore_client)
):
    """Delete custom definition (owner only).
    
    Args:
        definition_type: "agent", "tool", or "source"
        definition_id: Definition ID
        user_id: Authenticated user ID
        firestore: Firestore client
        
    Raises:
        403: Not owner or system definition
        404: Definition not found
    """
    service = DefinitionService(firestore)
    
    try:
        await service.delete_definition(definition_id, definition_type, user_id)
        
        logger.info(
            "Deleted custom definition",
            extra={"definition_id": definition_id, "type": definition_type, "user_id": user_id}
        )
        
        return None  # 204 No Content
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "cannot" in str(e).lower() or "only owner" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        else:
            logger.error(
                "Failed to delete definition",
                extra={"definition_id": definition_id, "type": definition_type, "error": str(e)}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete definition: {str(e)}"
            )
