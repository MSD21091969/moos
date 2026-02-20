"""gRPC client for communicating with the GraphToolServer.

The DataServer calls this client when a new tool or workflow is defined
inside a container, forwarding the registration to the GraphToolServer's
gRPC ``ColliderGraph`` service.

The client is lazy — it only connects when the first RPC is issued.
If grpcio is not installed or the GraphToolServer is unreachable, the
error is logged and the REST flow continues unblocked.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Default address of the GraphToolServer gRPC endpoint
_DEFAULT_GRAPH_ADDR = "localhost:50052"


class GraphToolClient:
    """Async gRPC client stub for the ColliderGraph service."""

    def __init__(self, target: str = _DEFAULT_GRAPH_ADDR) -> None:
        self._target = target
        self._channel = None
        self._stub = None

    async def _ensure_channel(self) -> None:
        """Lazily create the gRPC channel and stub."""
        if self._stub is not None:
            return
        try:
            import grpc.aio
            from proto import collider_graph_pb2_grpc  # type: ignore[import-untyped]

            self._channel = grpc.aio.insecure_channel(self._target)
            self._stub = collider_graph_pb2_grpc.ColliderGraphStub(self._channel)
            logger.info("Connected to GraphToolServer at %s", self._target)
        except ImportError:
            logger.warning(
                "grpcio not installed — GraphToolServer forwarding disabled"
            )
        except Exception:
            logger.exception("Failed to connect to GraphToolServer at %s", self._target)

    # ------------------------------------------------------------------ #
    # Tool Registration
    # ------------------------------------------------------------------ #

    async def register_tool(
        self,
        *,
        tool_name: str,
        origin_node_id: str,
        owner_user_id: str,
        params_schema: dict | None = None,
        code_ref: str = "",
        visibility: str = "local",
    ) -> dict[str, Any]:
        """Forward a tool registration to the GraphToolServer.

        Returns the response dict or ``{"success": False}`` on failure.
        """
        await self._ensure_channel()
        if self._stub is None:
            return {"success": False, "message": "gRPC not available"}

        from proto import collider_graph_pb2  # type: ignore[import-untyped]

        request = collider_graph_pb2.RegisterToolRequest(
            tool_name=tool_name,
            origin_node_id=origin_node_id,
            owner_user_id=owner_user_id,
            params_schema_json=json.dumps(params_schema or {}).encode(),
            code_ref=code_ref,
            visibility=visibility,
        )

        try:
            response = await self._stub.RegisterTool(request)
            return {
                "success": response.success,
                "tool_name": response.tool_name,
                "message": response.message,
            }
        except Exception:
            logger.exception("register_tool RPC failed for %s", tool_name)
            return {"success": False, "message": "RPC failed"}

    # ------------------------------------------------------------------ #
    # Workflow Registration
    # ------------------------------------------------------------------ #

    async def register_workflow(
        self,
        *,
        workflow_name: str,
        origin_node_id: str,
        owner_user_id: str,
        steps: list[str] | None = None,
        entry_point: str = "",
    ) -> dict[str, Any]:
        """Forward a workflow registration to the GraphToolServer."""
        await self._ensure_channel()
        if self._stub is None:
            return {"success": False, "message": "gRPC not available"}

        from proto import collider_graph_pb2  # type: ignore[import-untyped]

        request = collider_graph_pb2.RegisterWorkflowRequest(
            workflow_name=workflow_name,
            origin_node_id=origin_node_id,
            owner_user_id=owner_user_id,
            steps=steps or [],
            entry_point=entry_point,
        )

        try:
            response = await self._stub.RegisterWorkflow(request)
            return {
                "success": response.success,
                "workflow_name": response.workflow_name,
                "message": response.message,
            }
        except Exception:
            logger.exception("register_workflow RPC failed for %s", workflow_name)
            return {"success": False, "message": "RPC failed"}

    # ------------------------------------------------------------------ #
    # Tool Discovery
    # ------------------------------------------------------------------ #

    async def discover_tools(
        self,
        *,
        query: str = "",
        user_id: str | None = None,
        visibility_filter: list[str] | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Discover tools from the GraphToolServer."""
        await self._ensure_channel()
        if self._stub is None:
            return []

        from proto import collider_graph_pb2  # type: ignore[import-untyped]

        request = collider_graph_pb2.ToolDiscoveryRequest(
            query=query,
            user_id=user_id or "",
            visibility_filter=visibility_filter or ["local", "group", "global"],
            limit=limit,
        )

        try:
            response = await self._stub.DiscoverTools(request)
            return [
                {
                    "tool_name": t.tool_name,
                    "origin_node_id": t.origin_node_id,
                    "owner_user_id": t.owner_user_id,
                    "params_schema": json.loads(t.params_schema_json) if t.params_schema_json else {},
                    "code_ref": t.code_ref,
                    "visibility": t.visibility,
                }
                for t in response.tools
            ]
        except Exception:
            logger.exception("discover_tools RPC failed")
            return []

    # ------------------------------------------------------------------ #
    # Subgraph Execution
    # ------------------------------------------------------------------ #

    async def execute_subgraph(
        self,
        *,
        workflow_name: str,
        user_id: str,
        inputs: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a subgraph (workflow) on the GraphToolServer."""
        await self._ensure_channel()
        if self._stub is None:
            return {"success": False, "message": "gRPC not available", "result": {}}

        from proto import collider_graph_pb2  # type: ignore[import-untyped]

        request = collider_graph_pb2.SubgraphRequest(
            workflow_name=workflow_name,
            user_id=user_id,
            inputs_json=json.dumps(inputs).encode(),
        )

        try:
            response = await self._stub.ExecuteSubgraph(request)
            result = {}
            if response.success and response.result_json:
                result = json.loads(response.result_json)
            
            return {
                "success": response.success,
                "workflow_name": response.workflow_name,
                "result": result,
                "error_message": response.error_message,
            }
        except Exception:
            logger.exception("execute_subgraph RPC failed for %s", workflow_name)
            return {"success": False, "message": "RPC failed", "result": {}}

    # ------------------------------------------------------------------ #
    # Single Tool Execution
    # ------------------------------------------------------------------ #

    async def execute_tool(
        self,
        *,
        tool_name: str,
        user_id: str,
        inputs: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a single tool on the GraphToolServer by name.

        Returns the response dict or ``{"success": False}`` on failure.
        """
        await self._ensure_channel()
        if self._stub is None:
            return {"success": False, "message": "gRPC not available", "result": {}}

        from proto import collider_graph_pb2  # type: ignore[import-untyped]

        request = collider_graph_pb2.ToolExecutionRequest(
            tool_name=tool_name,
            user_id=user_id,
            inputs_json=json.dumps(inputs).encode(),
        )

        try:
            response = await self._stub.ExecuteTool(request)
            result: dict[str, Any] = {}
            if response.success and response.result_json:
                result = json.loads(response.result_json)
            return {
                "success": response.success,
                "tool_name": response.tool_name,
                "result": result,
                "error_message": response.error_message,
            }
        except Exception:
            logger.exception("execute_tool RPC failed for %s", tool_name)
            return {"success": False, "message": "RPC failed", "result": {}}

    # ------------------------------------------------------------------ #
    # Cleanup
    # ------------------------------------------------------------------ #

    async def close(self) -> None:
        """Gracefully close the gRPC channel."""
        if self._channel is not None:
            await self._channel.close()
            self._channel = None
            self._stub = None
