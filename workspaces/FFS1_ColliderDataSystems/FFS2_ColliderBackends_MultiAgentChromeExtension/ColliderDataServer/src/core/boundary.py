"""Per-node API boundary enforcement.

Reads ``container.api_boundary`` from a node and raises 403 if the
protocol being used is not permitted for that node.
"""

from __future__ import annotations

from fastapi import HTTPException

from src.schemas.nodes import ApiBoundary, NodeContainer


async def enforce_node_boundary(
    container_data: dict,
    protocol: str,
) -> None:
    """Raise 403 if *protocol* is not permitted by the node's container.

    Parameters
    ----------
    container_data:
        The raw ``Node.container`` JSON dict from the database.
    protocol:
        One of ``"rest"``, ``"sse"``, ``"websocket"``, ``"webrtc"``,
        ``"native_messaging"``, ``"grpc"``.
    """
    try:
        container = NodeContainer(**container_data)
        boundary = container.api_boundary
    except Exception:
        # Legacy containers without api_boundary — use defaults (rest+sse)
        boundary = ApiBoundary()

    if not getattr(boundary, protocol, False):
        raise HTTPException(
            status_code=403,
            detail=f"Protocol '{protocol}' not permitted for this node",
        )
