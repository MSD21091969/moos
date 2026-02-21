"""ContextSet — parameterized agent context composition request and session schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ContextSet(BaseModel):
    """Parameterized description of what context to compose for an agent session.

    The AgentRunner resolves this into a system prompt + tool set by:
    1. Authenticating as the given ``role``'s pre-seeded Collider account.
    2. Bootstrapping each node in ``node_ids`` and merging (leaf-wins).
    3. Optionally running a vector query against the GraphToolServer tool registry.
    4. Filtering the merged tool schemas by ``visibility_filter``.
    """

    role: Literal["superadmin", "collider_admin", "app_admin", "app_user"]
    app_id: str
    node_ids: list[str]
    vector_query: str | None = None
    visibility_filter: list[Literal["local", "group", "global"]] = ["global", "group"]
    depth: int | None = None  # bootstrap subtree depth per node; None = full subtree


class SessionPreview(BaseModel):
    """Summary of what was composed into a session — returned to the UI."""

    node_count: int
    skill_count: int
    tool_count: int
    role: str
    vector_matches: int


class SessionResponse(BaseModel):
    """Response from POST /agent/session."""

    session_id: str
    preview: SessionPreview
