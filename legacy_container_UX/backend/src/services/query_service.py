"""Query service for unified graph traversal and resource retrieval.

Implements the logic for:
- ResourceFilter execution
- GraphTraversalQuery execution
"""

from typing import List, Optional
from src.core.logging import get_logger
from src.models.queries import (
    ResourceFilter, 
    GraphTraversalQuery, 
    ResourceQueryResult, 
    QueryScope,
    ChainResponse,
    ChainStep,
    BatchOperationRequest,
    BatchOperationResult,
    BatchOperationType
)
from src.services.container_service import ContainerService
from src.services.session_service import SessionService
from src.core.exceptions import NotFoundError

logger = get_logger(__name__)

class QueryService:
    """Service for executing structured queries against the object graph."""

    def __init__(
        self, 
        container_service: ContainerService,
        session_service: SessionService
    ):
        self.container_service = container_service
        self.session_service = session_service

    async def _collect_subtree_resources(
        self,
        user_id: str,
        container_id: str,
        container_type: str,
        visited_containers: set,
        results: list,
        depth: int = 0,
        max_depth: int = 5
    ):
        """Recursively collect resources from a container subtree."""
        if depth > max_depth:
            return
            
        if container_id in visited_containers:
            return
        visited_containers.add(container_id)
        
        # Fetch resources
        try:
            if container_type == "session":
                links = await self.session_service.get_resources(container_id, user_id)
            else:
                links = await self.container_service.list_resources(container_id, user_id)
        except Exception as e:
            # ACL failure or not found - skip this branch
            logger.debug(f"Skipping subtree {container_id}: {e}")
            return

        for link in links:
            # Add parent_id to result for batch ops
            item = link.model_dump()
            item["parent_id"] = container_id
            results.append(item)
            
            # Recurse if container
            rtype = link.resource_type.lower()
            if rtype in ["agent", "tool", "session"] and link.instance_id:
                await self._collect_subtree_resources(
                    user_id,
                    link.instance_id,
                    rtype,
                    visited_containers,
                    results,
                    depth + 1,
                    max_depth
                )

    async def execute_batch_operation(
        self,
        user_id: str,
        request: BatchOperationRequest
    ) -> BatchOperationResult:
        """Execute a batch operation on resources."""
        success = 0
        failure = 0
        errors = []
        
        if request.operation == BatchOperationType.DELETE:
            for idx, item in enumerate(request.items):
                try:
                    if item.parent_type == "session":
                        await self.session_service.remove_resource_link(
                            item.parent_id, user_id, item.link_id
                        )
                    else:
                        await self.container_service.remove_resource(
                            item.parent_id, item.link_id, user_id
                        )
                    success += 1
                except Exception as e:
                    failure += 1
                    errors.append({"item_index": idx, "error": str(e)})
                    
        return BatchOperationResult(
            success_count=success,
            failure_count=failure,
            errors=errors
        )

    async def find_resources(
        self, 
        user_id: str,
        scope_id: str,
        query: ResourceFilter,
        scope_type: QueryScope = QueryScope.SESSION
    ) -> ResourceQueryResult:
        """
        Find resources matching criteria within a scope.
        
        Args:
            user_id: User executing query
            scope_id: ID of the container/session to search in
            query: Filter criteria
            scope_type: Scope of search
        """
        # 1. Fetch candidates based on scope
        candidates = []
        
        if scope_type == QueryScope.SESSION:
            # Get session resources
            links = await self.session_service.get_resources(scope_id, user_id)
            candidates = []
            for link in links:
                item = link.model_dump()
                item["parent_id"] = scope_id
                candidates.append(item)
            
        elif scope_type == QueryScope.CHILDREN:
            # Get container resources
            links = await self.container_service.list_resources(scope_id, user_id)
            candidates = []
            for link in links:
                item = link.model_dump()
                item["parent_id"] = scope_id
                candidates.append(item)
                
        elif scope_type == QueryScope.SUBTREE:
            # Recursive fetch
            # Infer start type from ID
            start_type = "session" if scope_id.startswith("sess_") else self.container_service._get_container_type(scope_id)
            await self._collect_subtree_resources(
                user_id,
                scope_id,
                start_type,
                set(),
                candidates,
                max_depth=5 # Hardcoded limit for safety
            )
            
        # 2. Apply filters
        results = []
        for item in candidates:
            # Type filter
            if query.resource_types:
                if item.get("resource_type", "").lower() not in [t.lower() for t in query.resource_types]:
                    continue
            
            # Name filter (simple substring for now)
            if query.name_pattern:
                # Need to fetch actual instance to check name if not in link
                # For now, check link_id or metadata
                pass 
                
            # Tag filter
            # Requires fetching instance details usually
            
            results.append(item)
            
        return ResourceQueryResult(
            results=results,
            total=len(results),
            scope=scope_type
        )

    async def traverse_chain(
        self,
        user_id: str,
        query: GraphTraversalQuery,
        user_tier: str = "FREE"
    ) -> ChainResponse:
        """
        Traverse the graph following a path.
        
        Args:
            user_id: User executing query
            query: Traversal parameters
            user_tier: User tier (FREE, PRO, ENTERPRISE)
        """
        # Tier-based depth limits
        MAX_TRAVERSAL_DEPTH = {
            "FREE": 1,
            "PRO": 3,
            "ENTERPRISE": 5
        }
        
        allowed_depth = MAX_TRAVERSAL_DEPTH.get(user_tier.upper(), 1)
        if query.max_depth > allowed_depth:
            # Cap the depth instead of raising error, for better UX
            logger.info(f"Capping traversal depth from {query.max_depth} to {allowed_depth} for tier {user_tier}")
            query.max_depth = allowed_depth

        current_id = query.start_node_id
        chain = []
        
        # Initial node
        # We need to infer type to get details
        try:
            current_type = self.container_service._get_container_type(current_id)
            # Fetch details
            if current_type == "session":
                node = await self.session_service.get(current_id, user_id)
                name = node.metadata.title
                depth = node.depth or 0
            else:
                node = await self.container_service.get_instance(current_id, current_type, user_id)
                name = node.get("title", current_id)
                depth = node.get("depth", 0)
                
            chain.append(ChainStep(
                node_id=current_id,
                node_type=current_type,
                name=name,
                depth=depth
            ))
            
        except Exception as e:
            logger.warning(f"Failed to fetch start node {current_id}: {e}")
            raise NotFoundError(f"Start node {current_id} not found")

        # If path provided, follow it
        if query.path:
            segments = query.path.strip("/").split("/")
            for segment in segments:
                # Logic to find child by name/ID matching segment
                # This requires searching children
                pass

        return ChainResponse(
            chain=chain,
            final_node=None # TODO: Populate
        )
