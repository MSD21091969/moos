"""Query API routes for unified data access.

POST /query/resources - Find resources with filters
POST /query/traverse - Traverse object graph
"""

from fastapi import APIRouter, Depends, HTTPException
from src.api.dependencies import get_user_context, get_session_service, get_firestore_client
from src.models.context import UserContext
from src.models.queries import (
    ResourceFilter, 
    GraphTraversalQuery, 
    ResourceQueryResult, 
    ChainResponse,
    QueryScope,
    BatchOperationRequest,
    BatchOperationResult
)
from src.services.query_service import QueryService
from src.services.container_service import ContainerService
from src.services.session_service import SessionService

router = APIRouter(prefix="/query", tags=["query"])

def get_query_service(
    firestore=Depends(get_firestore_client),
    session_service: SessionService = Depends(get_session_service)
) -> QueryService:
    container_service = ContainerService(firestore)
    return QueryService(container_service, session_service)

@router.post("/batch", response_model=BatchOperationResult)
async def execute_batch(
    request: BatchOperationRequest,
    user_ctx: UserContext = Depends(get_user_context),
    service: QueryService = Depends(get_query_service)
):
    """Execute batch operation on resources."""
    return await service.execute_batch_operation(
        user_id=user_ctx.user_id,
        request=request
    )

@router.post("/resources", response_model=ResourceQueryResult)
async def find_resources(
    scope_id: str,
    query: ResourceFilter,
    scope_type: QueryScope = QueryScope.SESSION,
    user_ctx: UserContext = Depends(get_user_context),
    service: QueryService = Depends(get_query_service)
):
    """Find resources matching criteria."""
    return await service.find_resources(
        user_id=user_ctx.user_id,
        scope_id=scope_id,
        query=query,
        scope_type=scope_type
    )

@router.post("/traverse", response_model=ChainResponse)
async def traverse_graph(
    query: GraphTraversalQuery,
    user_ctx: UserContext = Depends(get_user_context),
    service: QueryService = Depends(get_query_service)
):
    """Traverse the object graph."""
    return await service.traverse_chain(
        user_id=user_ctx.user_id,
        query=query,
        user_tier=user_ctx.tier.value
    )
