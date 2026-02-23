"""gRPC Context Service — serves composed agent context to NanoClawBridge.

Implements the ColliderContext gRPC service defined in collider_graph.proto.
This replaces filesystem-based delivery (CLAUDE.md, SKILL.md, .mcp.json)
with programmatic gRPC streaming.

RPCs:
  StreamContext          — stream composed context as typed chunks
  GetBootstrap           — one-shot full context response
  SubscribeContextDeltas — live delta subscription (future)
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from concurrent import futures
from typing import Any

import grpc

from proto import collider_graph_pb2 as pb2
from proto import collider_graph_pb2_grpc as pb2_grpc
from src.agent.runner import ComposedContext, compose_context_set
from src.core.config import settings
from src.schemas.context_set import ContextSet

logger = logging.getLogger("collider.grpc.context")


class ColliderContextServicer(pb2_grpc.ColliderContextServicer):
    """gRPC servicer that delivers composed agent context."""

    # ------------------------------------------------------------------
    # StreamContext — stream full context as typed chunks
    # ------------------------------------------------------------------

    async def StreamContext(
        self,
        request: pb2.ContextRequest,
        context: grpc.aio.ServicerContext,
    ):
        """Compose a ContextSet and stream the result as typed chunks."""
        logger.info(
            "StreamContext: session=%s nodes=%s role=%s",
            request.session_id,
            list(request.node_ids),
            request.role,
        )

        try:
            composed = await self._compose(request)
        except Exception as exc:
            await context.abort(grpc.StatusCode.INTERNAL, str(exc))
            return

        seq = 0

        # Chunk 1: agents_md
        if composed.agents_md:
            yield pb2.ContextChunk(
                chunk_id=str(uuid.uuid4()),
                sequence=seq,
                system_prompt=pb2.SystemPromptChunk(
                    section="agents_md",
                    content=composed.agents_md,
                ),
            )
            seq += 1

        # Chunk 2: soul_md
        if composed.soul_md:
            yield pb2.ContextChunk(
                chunk_id=str(uuid.uuid4()),
                sequence=seq,
                system_prompt=pb2.SystemPromptChunk(
                    section="soul_md",
                    content=composed.soul_md,
                ),
            )
            seq += 1

        # Chunk 3: tools_md
        if composed.tools_md:
            yield pb2.ContextChunk(
                chunk_id=str(uuid.uuid4()),
                sequence=seq,
                system_prompt=pb2.SystemPromptChunk(
                    section="tools_md",
                    content=composed.tools_md,
                ),
            )
            seq += 1

        # Skills
        for skill in composed.skills:
            yield pb2.ContextChunk(
                chunk_id=str(uuid.uuid4()),
                sequence=seq,
                skill=_skill_to_chunk(skill),
            )
            seq += 1

        # Tool schemas
        for schema in composed.tool_schemas:
            yield pb2.ContextChunk(
                chunk_id=str(uuid.uuid4()),
                sequence=seq,
                tool_schema=_tool_schema_to_chunk(schema),
            )
            seq += 1

        # MCP config
        yield pb2.ContextChunk(
            chunk_id=str(uuid.uuid4()),
            sequence=seq,
            mcp_config=pb2.McpConfigChunk(
                name="collider-tools",
                transport_type="sse",
                url=settings.graph_tool_mcp_url,
            ),
        )
        seq += 1

        # Session meta
        yield pb2.ContextChunk(
            chunk_id=str(uuid.uuid4()),
            sequence=seq,
            session_meta=_session_meta_to_chunk(composed.session_meta),
        )

        logger.info("StreamContext: streamed %d chunks", seq + 1)

    # ------------------------------------------------------------------
    # GetBootstrap — one-shot full context
    # ------------------------------------------------------------------

    async def GetBootstrap(
        self,
        request: pb2.ContextRequest,
        context: grpc.aio.ServicerContext,
    ) -> pb2.BootstrapResponse:
        """Compose a ContextSet and return the full context as one response."""
        logger.info(
            "GetBootstrap: session=%s nodes=%s role=%s",
            request.session_id,
            list(request.node_ids),
            request.role,
        )

        try:
            composed = await self._compose(request)
        except Exception as exc:
            await context.abort(grpc.StatusCode.INTERNAL, str(exc))
            return pb2.BootstrapResponse()

        return pb2.BootstrapResponse(
            session_id=request.session_id,
            agents_md=composed.agents_md,
            soul_md=composed.soul_md,
            tools_md=composed.tools_md,
            skills=[_skill_to_chunk(s) for s in composed.skills],
            tool_schemas=[_tool_schema_to_chunk(t) for t in composed.tool_schemas],
            mcp_servers=[
                pb2.McpConfigChunk(
                    name="collider-tools",
                    transport_type="sse",
                    url=settings.graph_tool_mcp_url,
                )
            ],
            session_meta=_session_meta_to_chunk(composed.session_meta),
        )

    # ------------------------------------------------------------------
    # SubscribeContextDeltas — live updates (placeholder)
    # ------------------------------------------------------------------

    async def SubscribeContextDeltas(
        self,
        request: pb2.DeltaSubscription,
        context: grpc.aio.ServicerContext,
    ):
        """Watch for NodeContainer changes and stream deltas.

        Placeholder — will be implemented when DataServer exposes
        node mutation events via SSE.
        """
        logger.info(
            "SubscribeContextDeltas: session=%s nodes=%s (placeholder)",
            request.session_id,
            list(request.node_ids),
        )
        # Keep stream open — will push deltas when available
        while not context.cancelled():
            await asyncio.sleep(30)

    # ------------------------------------------------------------------
    # Internal: compose context from gRPC request
    # ------------------------------------------------------------------

    async def _compose(self, request: pb2.ContextRequest) -> ComposedContext:
        """Convert gRPC ContextRequest → ContextSet → ComposedContext."""
        ctx = ContextSet(
            role=request.role or "app_user",
            app_id=request.app_id,
            node_ids=list(request.node_ids),
            inherit_ancestors=request.inherit_ancestors,
        )
        return await compose_context_set(ctx)


# ----------------------------------------------------------------------
# Converters: dict → protobuf message
# ----------------------------------------------------------------------


def _skill_to_chunk(skill: dict[str, Any]) -> pb2.SkillChunk:
    return pb2.SkillChunk(
        name=skill.get("name", ""),
        description=skill.get("description", ""),
        emoji=skill.get("emoji", ""),
        markdown_body=skill.get("markdown_body", ""),
        tool_ref=skill.get("tool_ref", ""),
        user_invocable=skill.get("user_invocable", True),
        model_invocable=skill.get("model_invocable", True),
        invocation_policy=skill.get("invocation_policy", "auto"),
        requires_bins=skill.get("requires_bins", []),
        requires_env=skill.get("requires_env", []),
    )


def _tool_schema_to_chunk(schema: dict[str, Any]) -> pb2.ToolSchemaChunk:
    fn = schema.get("function", {})
    return pb2.ToolSchemaChunk(
        name=fn.get("name", ""),
        description=fn.get("description", ""),
        parameters_json=json.dumps(fn.get("parameters", {})).encode("utf-8"),
    )


def _session_meta_to_chunk(meta: dict[str, Any]) -> pb2.SessionMetaChunk:
    return pb2.SessionMetaChunk(
        role=meta.get("role", ""),
        app_id=meta.get("app_id", ""),
        composed_nodes=meta.get("composed_nodes", []),
        username=meta.get("username", ""),
    )


# ----------------------------------------------------------------------
# Server startup
# ----------------------------------------------------------------------


async def serve_grpc(port: int = 50051) -> grpc.aio.Server:
    """Start the gRPC context server.

    Returns the server instance (caller should await server.wait_for_termination()).
    """
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=4))
    pb2_grpc.add_ColliderContextServicer_to_server(ColliderContextServicer(), server)
    listen_addr = f"[::]:{port}"
    server.add_insecure_port(listen_addr)
    await server.start()
    logger.info("gRPC ColliderContext server listening on %s", listen_addr)
    return server
