"""Query tools for the ChatAgent.

These tools allow the agent to:
1. Find resources using structured filters
2. Traverse the object graph to understand context
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from src.models.queries import ResourceFilter, GraphTraversalQuery, QueryScope

class FindResourcesTool(BaseModel):
    """Find resources (agents, tools, sessions) matching criteria."""
    scope_id: str = Field(..., description="ID of session or container to search in")
    scope_type: QueryScope = Field(QueryScope.SESSION, description="Scope of search")
    types: Optional[List[str]] = Field(None, description="Filter by types: ['agent', 'tool', 'source', 'session']")
    name_pattern: Optional[str] = Field(None, description="Name matching pattern")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")

class TraverseGraphTool(BaseModel):
    """Traverse the object graph to explore relationships."""
    start_node_id: str = Field(..., description="Starting node ID")
    path: Optional[str] = Field(None, description="Path to follow (e.g. 'agent_sales/tool_csv')")
    max_depth: int = Field(1, description="How deep to traverse")
    direction: str = Field("down", description="'down' (children) or 'up' (parents)")
