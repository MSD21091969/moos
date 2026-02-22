"""Agent bootstrap endpoints.

These endpoints allow a NanoClaw agent workspace to bootstrap its context,
identity, and skills from a Collider NodeContainer.

Flow:
1. AgentRunner calls ``GET /api/v1/agent/bootstrap/{node_id}`` with a JWT.
2. The response contains agents_md, soul_md, tools_md content + skill entries
   + OpenAI-compatible tool schemas.
3. The workspace writer merges these into CLAUDE.md + Agent Skills SKILL.md
   files in the NanoClaw workspace directory.

Subtree aggregation:
By default the bootstrap walks the full descendant tree and merges skills and
tool schemas from every child node.  Pass ``?depth=0`` to get only the root
node (flat, legacy behaviour).  ``?depth=1`` includes direct children only.
"""

from __future__ import annotations

from collections import deque

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import get_current_user
from src.core.boundary import enforce_node_boundary
from src.core.database import get_db
from src.core.agent_bootstrap import render_bootstrap
from src.db.models import Node, User
from src.schemas.nodes import NodeContainer
from src.schemas.agent_bootstrap import AgentBootstrap, AgentSkillEntry

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _load_descendants(
    root: Node,
    db: AsyncSession,
    depth: int | None,
) -> list[Node]:
    """Return all descendant nodes of root in BFS order.

    Args:
        root: The root node (not included in the result).
        db: The active async database session.
        depth: Maximum traversal depth.  ``None`` means unlimited.
            ``0`` returns an empty list (root only).  ``1`` returns direct
            children only.

    Returns:
        BFS-ordered list of descendant nodes (root excluded).
    """
    if depth == 0:
        return []

    result = await db.execute(
        select(Node).where(
            Node.application_id == root.application_id,
            Node.id != root.id,
        )
    )
    all_sibling_nodes = result.scalars().all()

    # Build parent_id → [children] index
    children_index: dict[str, list[Node]] = {}
    for n in all_sibling_nodes:
        if n.parent_id:
            children_index.setdefault(n.parent_id, []).append(n)

    # BFS from root, respecting depth limit
    descendants: list[Node] = []
    queue: deque[tuple[str, int]] = deque([(root.id, 0)])

    while queue:
        current_id, current_depth = queue.popleft()
        if depth is not None and current_depth >= depth:
            continue
        for child in children_index.get(current_id, []):
            descendants.append(child)
            queue.append((child.id, current_depth + 1))

    return descendants


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/bootstrap/{node_id}", response_model=AgentBootstrap)
async def get_agent_bootstrap(
    node_id: str,
    depth: int | None = Query(
        None,
        ge=0,
        description=(
            "Max descendant depth to aggregate.  "
            "Omit for full subtree (default).  "
            "0 = root node only (flat, legacy)."
        ),
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentBootstrap:
    """Render a NodeContainer as an agent-compatible workspace bootstrap.

    Returns the node's instructions, rules, and knowledge as Markdown strings
    (``agents_md``, ``soul_md``, ``tools_md``), along with typed skill entries
    and OpenAI-compatible tool function schemas.

    Skills and tool schemas are aggregated recursively from all descendant nodes
    (BFS order, leaf entries override root entries so the most-specific
    definition wins).  Use ``?depth=0`` to disable subtree aggregation.

    The ``execute_workflow_schema`` and ``execute_tool_schema`` fields provide
    pre-built function schemas so the agent can trigger Collider
    workflows or individual tools via:
    - ``POST /execution/workflow/{workflow_name}``
    - ``POST /execution/tool/{tool_name}``
    """
    result = await db.execute(select(Node).where(Node.id == node_id))
    node = result.scalar_one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")

    await enforce_node_boundary(node.container, "rest")

    descendants = await _load_descendants(node, db, depth)
    return render_bootstrap(node, current_user, descendants=descendants)


@router.get("/skills", response_model=list[AgentSkillEntry])
async def list_agent_skills(
    node_id: str | None = Query(None, description="Filter to a specific node's skills"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AgentSkillEntry]:
    """List all skills visible to this user, optionally scoped to a node.

    Queries nodes whose container carries non-empty ``skills`` arrays and
    returns them flattened as Agent Skills entries.  Useful for skill
    discovery or a registry interface.
    """
    stmt = select(Node)
    if node_id:
        stmt = stmt.where(Node.id == node_id)

    result = await db.execute(stmt)
    nodes = result.scalars().all()

    entries: list[AgentSkillEntry] = []
    for node in nodes:
        try:
            container = NodeContainer.model_validate(node.container)
        except Exception:
            continue
        for skill in container.skills:
            entries.append(
                AgentSkillEntry(
                    name=skill.name,
                    description=skill.description,
                    emoji=skill.emoji,
                    requires_bins=skill.requires_bins,
                    requires_env=skill.requires_env,
                    user_invocable=skill.invocation.user_invocable,
                    model_invocable=skill.invocation.model_invocable,
                    markdown_body=skill.markdown_body,
                )
            )

    return entries
