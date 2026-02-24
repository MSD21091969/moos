"""GraphToolServer registry schemas."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class GraphStepEntry(BaseModel):
    """A tool registered as a runnable Pydantic Graph step.

    Created when the DataServer notifies the GraphToolServer of a new
    ``ToolDefinition`` inside a container.  ``params_schema`` feeds
    ``pydantic.create_model()`` to build a dynamic args model at runtime.
    """

    tool_name: str
    origin_node_id: str  # DataServer Node.id
    owner_user_id: str
    params_schema: dict = Field(default_factory=dict)  # JSON Schema for create_model()
    code_ref: str = ""
    visibility: Literal["local", "group", "global"] = "local"
    registered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SubgraphManifest(BaseModel):
    """A workflow registered as a discoverable subgraph.

    Wraps a ``WorkflowDefinition`` into something the Pydantic Graph Beta
    engine can execute.  Agents call this as a single tool; the graph
    handles the multi-step orchestration internally.
    """

    workflow_name: str
    origin_node_id: str  # DataServer Node.id
    owner_user_id: str
    steps: list[str] = Field(
        default_factory=list
    )  # Ordered GraphStepEntry.tool_name refs
    entry_point: str = ""  # First step name
    registered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ToolQuery(BaseModel):
    """Query parameters for tool discovery."""

    query: str = ""
    user_id: str | None = None
    visibility_filter: list[Literal["local", "group", "global"]] = Field(
        default_factory=lambda: ["local", "group", "global"]
    )
    limit: int = 50
