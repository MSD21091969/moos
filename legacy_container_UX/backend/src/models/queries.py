"""Query models for unified data access and graph traversal.

These models define the contract for:
1. Filtering resources (Agents, Tools, Sessions)
2. Navigating the object graph (Chains, Paths)
3. Scoping queries (Depth, Context)

Used by:
- ContainerService (for execution)
- ChatAgent (as Tools)
- API Endpoints (for structured requests)
"""

from enum import Enum
from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field

class QueryScope(str, Enum):
    """Scope of the query."""
    WORKSPACE = "workspace"  # All accessible resources
    SESSION = "session"      # Current session only
    CHILDREN = "children"    # Direct children of a container
    SUBTREE = "subtree"      # Recursive descendants

class BatchOperationType(str, Enum):
    DELETE = "delete"

class ResourceIdentifier(BaseModel):
    parent_id: str = Field(..., description="ID of the container holding the link")
    parent_type: str = Field(..., description="Type of the parent container (session, agent, tool)")
    link_id: str = Field(..., description="ID of the link to operate on")

class BatchOperationRequest(BaseModel):
    operation: BatchOperationType
    items: List[ResourceIdentifier]

class BatchOperationResult(BaseModel):
    success_count: int
    failure_count: int
    errors: List[dict] # { item_index: int, error: str }

class ResourceFilter(BaseModel):
    """Filter criteria for resources."""
    resource_types: Optional[List[str]] = Field(
        None, 
        description="Filter by types: ['agent', 'tool', 'source', 'session']"
    )
    tags: Optional[List[str]] = Field(
        None, 
        description="Filter by tags (any match)"
    )
    name_pattern: Optional[str] = Field(
        None, 
        description="Regex or glob pattern for name matching"
    )
    metadata_filters: Optional[dict] = Field(
        None, 
        description="Key-value pairs to match in metadata"
    )

class GraphTraversalQuery(BaseModel):
    """Query to traverse the object graph."""
    start_node_id: str = Field(
        ..., 
        description="Starting container ID (e.g., sess_123)"
    )
    path: Optional[str] = Field(
        None, 
        description="Slash-separated path (e.g., 'agent_sales/tool_csv')"
    )
    max_depth: int = Field(
        1, 
        description="Maximum depth to traverse (1 = direct children)"
    )
    direction: Literal["down", "up"] = Field(
        "down", 
        description="Traversal direction: 'down' (children) or 'up' (parents)"
    )

class ChainStep(BaseModel):
    """A single step in a resource chain."""
    node_id: str
    node_type: str
    name: str
    depth: int

class ChainResponse(BaseModel):
    """Response for a chain traversal."""
    chain: List[ChainStep]
    final_node: Optional[dict] = None

class ResourceQueryResult(BaseModel):
    """Unified result for resource queries."""
    results: List[dict]
    total: int
    scope: QueryScope
