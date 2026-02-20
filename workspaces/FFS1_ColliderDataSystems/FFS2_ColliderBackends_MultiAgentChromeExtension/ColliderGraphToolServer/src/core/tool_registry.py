"""In-memory Tool Registry for the GraphToolServer.

Holds all registered ``GraphStepEntry`` and ``SubgraphManifest`` objects,
supports registration, discovery (fuzzy + filtered), and provides the
dynamic Pydantic models built from their schemas.

In production Phase 6 this will be backed by VectorDB for semantic search.
For now, simple substring matching provides a functional baseline.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from src.core.model_factory import build_args_model
from src.schemas.registry import GraphStepEntry, SubgraphManifest, ToolQuery

logger = logging.getLogger(__name__)


class ToolRegistryStats(BaseModel):
    """Quick summary of registry contents."""

    total_tools: int = 0
    total_workflows: int = 0
    by_visibility: dict[str, int] = {}


class ToolRegistry:
    """In-memory registry of tools and workflows.

    Thread-safety note: this is a single-process async server, so
    dict operations are safe within a single event loop.
    """

    def __init__(self) -> None:
        self._tools: dict[str, GraphStepEntry] = {}
        self._workflows: dict[str, SubgraphManifest] = {}
        self._models: dict[str, type[BaseModel]] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    async def register_tool(self, entry: GraphStepEntry) -> type[BaseModel]:
        """Register a tool and build its dynamic args model.

        Returns the generated Pydantic model class.
        """
        self._tools[entry.tool_name] = entry

        # Build and cache the dynamic model
        model = build_args_model(entry.tool_name, entry.params_schema)
        self._models[entry.tool_name] = model

        # Index in VectorDB (fire and forget or await? await for reliability)
        from src.core.vector_client import vector_client
        import json
        
        await vector_client.index_tool(
            tool_name=entry.tool_name,
            description=entry.description if hasattr(entry, "description") else "", # Access description safely
            origin_node_id=entry.origin_node_id,
            owner_user_id=entry.owner_user_id,
            params_schema_json=json.dumps(entry.params_schema)
        )

        logger.info(
            "Registered tool %r (visibility=%s, origin=%s)",
            entry.tool_name,
            entry.visibility,
            entry.origin_node_id,
        )
        return model

    def register_workflow(self, manifest: SubgraphManifest) -> None:
        """Register a workflow (subgraph manifest)."""
        self._workflows[manifest.workflow_name] = manifest
        logger.info(
            "Registered workflow %r with %d steps",
            manifest.workflow_name,
            len(manifest.steps),
        )

    # ------------------------------------------------------------------
    # Removal
    # ------------------------------------------------------------------

    def unregister_tool(self, tool_name: str) -> bool:
        """Remove a tool from the registry. Returns True if it existed."""
        removed = self._tools.pop(tool_name, None) is not None
        self._models.pop(tool_name, None)
        return removed

    def unregister_workflow(self, workflow_name: str) -> bool:
        """Remove a workflow from the registry."""
        return self._workflows.pop(workflow_name, None) is not None

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    async def discover_tools(self, query: ToolQuery) -> list[GraphStepEntry]:
        """Find tools matching the query criteria.

        Uses VectorDB for semantic search if query text is provided.
        Falls back to local substring matching if no results or no query.
        """
        results: list[GraphStepEntry] = []
        q_lower = query.query.lower()
        
        vector_matches = []
        if q_lower:
            from src.core.vector_client import vector_client
            vector_matches = await vector_client.search_tools(
                query=query.query,
                limit=query.limit,
                owner_user_id=query.user_id
            )
        
        # If we got vector matches, use them (filtering by visibility still needed)
        # For now, let's keep the existing logic but prioritize/mix vector results?
        # Simpler approach: If vector results exist, return them (filtered).
        # Otherwise, fall back to simple search.
        
        candidate_tools = self._tools.values()
        
        # If vector search returned names, prioritize those
        if vector_matches:
            # Re-order candidates based on vector match order?
            # Or just filter?
            # Let's trust vector DB for relevance but verify existence/visibility here
            matched_names = {m["name"] for m in vector_matches}
            # We still need to iterate all tools to check permissions? 
            # Or just look up the matched ones?
            candidates_from_vector = []
            for m in vector_matches:
                t = self._tools.get(m["name"])
                if t:
                    candidates_from_vector.append(t)
            
            # If we have vector matches, use those as the source
            if candidates_from_vector:
                candidate_tools = candidates_from_vector

        for entry in candidate_tools:
            # Visibility filter
            if entry.visibility not in query.visibility_filter:
                continue

            # User filter (local tools only visible to owner)
            if (
                entry.visibility == "local"
                and query.user_id
                and entry.owner_user_id != query.user_id
            ):
                continue

            # Text match (only if NOT using vector results)
            if not vector_matches and q_lower and q_lower not in entry.tool_name.lower():
                continue

            results.append(entry)

            if len(results) >= query.limit:
                break

        return results

    def discover_workflows(
        self,
        query: str = "",
        visibility_filter: list[Literal["local", "group", "global"]] | None = None,
        limit: int = 50,
    ) -> list[SubgraphManifest]:
        """Find workflows matching text query."""
        if visibility_filter is None:
            visibility_filter = ["local", "group", "global"]

        results: list[SubgraphManifest] = []
        q_lower = query.lower()

        for manifest in self._workflows.values():
            if q_lower and q_lower not in manifest.workflow_name.lower():
                continue
            results.append(manifest)
            if len(results) >= limit:
                break

        return results

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_tool(self, tool_name: str) -> GraphStepEntry | None:
        """Get a specific tool entry by name."""
        return self._tools.get(tool_name)

    def get_workflow(self, workflow_name: str) -> SubgraphManifest | None:
        """Get a specific workflow manifest by name."""
        return self._workflows.get(workflow_name)

    def get_args_model(self, tool_name: str) -> type[BaseModel] | None:
        """Get the dynamically generated args model for a tool."""
        return self._models.get(tool_name)

    def stats(self) -> ToolRegistryStats:
        """Return summary statistics."""
        by_vis: dict[str, int] = {}
        for entry in self._tools.values():
            by_vis[entry.visibility] = by_vis.get(entry.visibility, 0) + 1
        return ToolRegistryStats(
            total_tools=len(self._tools),
            total_workflows=len(self._workflows),
            by_visibility=by_vis,
        )
