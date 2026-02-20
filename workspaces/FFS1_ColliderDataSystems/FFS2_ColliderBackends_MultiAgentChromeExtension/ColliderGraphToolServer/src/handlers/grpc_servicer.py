"""ColliderGraph gRPC servicer — tool/workflow registration and discovery.

Wraps the ToolRegistry behind a gRPC interface.  The compiled stubs
(``collider_graph_pb2`` / ``_pb2_grpc``) are expected in the ``proto/``
package at the FFS2 root.

Until proto compilation is run, this module imports stub types lazily
so the rest of the application can start without grpc dependencies.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import grpc

    from src.core.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lazy imports — only resolved when the gRPC server is actually started.
# This lets the REST API work even without grpcio installed.
# ---------------------------------------------------------------------------

def _load_stubs():
    """Import compiled proto stubs (call after proto compilation)."""
    # These will exist after running `python -m proto.compile_protos`
    from proto import collider_graph_pb2, collider_graph_pb2_grpc  # type: ignore[import-untyped]
    return collider_graph_pb2, collider_graph_pb2_grpc


class ColliderGraphServicer:
    """gRPC servicer that delegates to the in-memory ToolRegistry.

    Each RPC method receives a protobuf request, delegates to the
    ToolRegistry, and returns a protobuf response.
    """

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry
        self._pb2, self._grpc = _load_stubs()

    # ------------------------------------------------------------------ #
    # Tool Registration
    # ------------------------------------------------------------------ #

    async def RegisterTool(self, request, context: grpc.aio.ServicerContext):
        """Register a tool from a DataServer ToolDefinition."""
        from src.schemas.registry import GraphStepEntry

        params_schema = json.loads(request.params_schema_json) if request.params_schema_json else {}

        entry = GraphStepEntry(
            tool_name=request.tool_name,
            origin_node_id=request.origin_node_id,
            owner_user_id=request.owner_user_id,
            params_schema=params_schema,
            code_ref=request.code_ref,
            visibility=request.visibility or "local",
        )

        try:
            args_model = await self._registry.register_tool(entry)
            return self._pb2.RegisterToolResponse(
                success=True,
                tool_name=entry.tool_name,
                args_schema_json=json.dumps(args_model.model_json_schema()).encode(),
                message="registered",
            )
        except Exception as exc:
            logger.exception("RegisterTool failed for %s", request.tool_name)
            return self._pb2.RegisterToolResponse(
                success=False,
                tool_name=request.tool_name,
                message=str(exc),
            )

    # ------------------------------------------------------------------ #
    # Workflow Registration
    # ------------------------------------------------------------------ #

    async def RegisterWorkflow(self, request, context: grpc.aio.ServicerContext):
        """Register a workflow as a subgraph manifest."""
        from src.schemas.registry import SubgraphManifest

        manifest = SubgraphManifest(
            workflow_name=request.workflow_name,
            origin_node_id=request.origin_node_id,
            owner_user_id=request.owner_user_id,
            steps=list(request.steps),
            entry_point=request.entry_point,
        )

        try:
            self._registry.register_workflow(manifest)
            return self._pb2.RegisterWorkflowResponse(
                success=True,
                workflow_name=manifest.workflow_name,
                message="registered",
            )
        except Exception as exc:
            logger.exception("RegisterWorkflow failed for %s", request.workflow_name)
            return self._pb2.RegisterWorkflowResponse(
                success=False,
                workflow_name=request.workflow_name,
                message=str(exc),
            )

    # ------------------------------------------------------------------ #
    # Tool Discovery
    # ------------------------------------------------------------------ #

    async def DiscoverTools(self, request, context: grpc.aio.ServicerContext):
        """Discover tools matching a query."""
        from src.schemas.registry import ToolQuery

        query = ToolQuery(
            query=request.query,
            user_id=request.user_id or None,
            visibility_filter=list(request.visibility_filter) or ["local", "group", "global"],
            limit=request.limit or 50,
        )

        results = await self._registry.discover_tools(query)

        tool_entries = [
            self._pb2.ToolEntry(
                tool_name=t.tool_name,
                origin_node_id=t.origin_node_id,
                owner_user_id=t.owner_user_id,
                params_schema_json=json.dumps(t.params_schema).encode(),
                code_ref=t.code_ref,
                visibility=t.visibility,
            )
            for t in results
        ]

        return self._pb2.ToolDiscoveryResponse(
            tools=tool_entries,
            total_count=len(tool_entries),
        )

    # ------------------------------------------------------------------ #
    # Subgraph Execution (stub — real logic in Phase 5+)
    # ------------------------------------------------------------------ #

    async def ExecuteSubgraph(self, request, context: grpc.aio.ServicerContext):
        """Execute a subgraph synchronously — returns final result."""
        from src.core.execution import WorkflowExecutor, ToolExecutionError, WorkflowExecutionError

        workflow = self._registry.get_workflow(request.workflow_name)
        if workflow is None:
            return self._pb2.SubgraphResponse(
                success=False,
                workflow_name=request.workflow_name,
                error_message=f"Workflow '{request.workflow_name}' not found",
            )

        try:
            inputs = json.loads(request.inputs_json) if request.inputs_json else {}
            executor = WorkflowExecutor(self._registry)
            
            # Execute
            result_ctx = await executor.execute(workflow, inputs)
            
            return self._pb2.SubgraphResponse(
                success=True,
                workflow_name=request.workflow_name,
                result_json=json.dumps(result_ctx, default=str).encode(),
            )
        except (ToolExecutionError, WorkflowExecutionError) as e:
            logger.error(f"Execution failed: {e}")
            return self._pb2.SubgraphResponse(
                success=False,
                workflow_name=request.workflow_name,
                error_message=str(e),
            )
        except Exception as e:
            logger.exception("Unexpected execution error")
            return self._pb2.SubgraphResponse(
                success=False,
                workflow_name=request.workflow_name,
                error_message=f"Internal error: {str(e)}",
            )

    # ------------------------------------------------------------------ #
    # Single Tool Execution
    # ------------------------------------------------------------------ #

    async def ExecuteTool(self, request, context: grpc.aio.ServicerContext):
        """Execute a single registered tool by name, bypassing any workflow wrapper."""
        from src.core.execution import ToolRunner, ToolExecutionError

        tool = self._registry.get_tool(request.tool_name)
        if tool is None:
            return self._pb2.ToolExecutionResponse(
                success=False,
                tool_name=request.tool_name,
                error_message=f"Tool '{request.tool_name}' not found in registry",
            )

        try:
            inputs = json.loads(request.inputs_json) if request.inputs_json else {}
            result = await ToolRunner.execute(tool, inputs)
            return self._pb2.ToolExecutionResponse(
                success=True,
                tool_name=request.tool_name,
                result_json=json.dumps(result, default=str).encode(),
            )
        except ToolExecutionError as exc:
            logger.error("ExecuteTool failed for %s: %s", request.tool_name, exc)
            return self._pb2.ToolExecutionResponse(
                success=False,
                tool_name=request.tool_name,
                error_message=str(exc),
            )
        except Exception:
            logger.exception("ExecuteTool unexpected error for %s", request.tool_name)
            return self._pb2.ToolExecutionResponse(
                success=False,
                tool_name=request.tool_name,
                error_message="Internal error during tool execution",
            )

    async def ExecuteSubgraphStream(self, request, context: grpc.aio.ServicerContext):
        """Stream execution progress for a subgraph."""
        workflow = self._registry.get_workflow(request.workflow_name)
        if workflow is None:
            yield self._pb2.SubgraphProgress(
                workflow_name=request.workflow_name,
                status="failed",
                current_step="",
                step_index=0,
                total_steps=0,
            )
            return

        # TODO(Phase 5): Real step-by-step streaming execution
        for i, step_name in enumerate(workflow.steps):
            yield self._pb2.SubgraphProgress(
                workflow_name=request.workflow_name,
                current_step=step_name,
                step_index=i,
                total_steps=len(workflow.steps),
                status="completed",
            )


# ---------------------------------------------------------------------------
# Server bootstrap helper
# ---------------------------------------------------------------------------

async def serve_grpc(registry: ToolRegistry, port: int = 50052) -> None:
    """Start the gRPC server on the given port.

    Call this from ``main.py`` at startup to run gRPC alongside the
    FastAPI HTTP server.
    """
    import grpc.aio

    pb2, pb2_grpc = _load_stubs()
    server = grpc.aio.server()
    pb2_grpc.add_ColliderGraphServicer_to_server(
        ColliderGraphServicer(registry), server
    )
    server.add_insecure_port(f"[::]:{port}")
    logger.info("gRPC ColliderGraph server listening on port %d", port)
    await server.start()
    await server.wait_for_termination()
