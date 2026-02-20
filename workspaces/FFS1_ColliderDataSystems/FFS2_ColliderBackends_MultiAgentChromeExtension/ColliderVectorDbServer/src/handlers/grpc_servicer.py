"""gRPC Servicer for VectorDB."""

import logging
import json
import grpc
from concurrent import futures

from proto import collider_vectordb_pb2
from proto import collider_vectordb_pb2_grpc
from src.core.vector_store import store

logger = logging.getLogger(__name__)


class ColliderVectorServicer(collider_vectordb_pb2_grpc.ColliderVectorDbServicer):
    """Implements the VectorDB gRPC service."""

    async def IndexTool(self, request, context):
        """Index a tool for semantic search."""
        try:
            logger.info(f"Indexing tool: {request.tool_name}")
            # Synchronous store call
            success = store.index_tool_full(
                tool_name=request.tool_name,
                description=request.description,
                origin_node_id=request.origin_node_id,
                owner_user_id=request.owner_user_id,
                params_schema_json=request.params_schema_json
            )
            return collider_vectordb_pb2.ToolIndexResponse(
                success=success,
                message="Tool indexed successfully" if success else "Failed to index tool"
            )
        except Exception as e:
            logger.error(f"Error indexing tool: {e}")
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return collider_vectordb_pb2.ToolIndexResponse(success=False, message=str(e))

    async def SearchTools(self, request, context):
        """Search for tools semantically."""
        try:
            logger.info(f"Searching tools with query: {request.query}")
            results = store.search_tools(
                query=request.query,
                limit=request.limit,
                owner_user_id=request.owner_user_id if request.owner_user_id else None
            )
            
            matches = []
            for r in results:
                matches.append(collider_vectordb_pb2.ToolMatch(
                    tool_name=r["tool_name"],
                    description=r["description"],
                    score=r["score"],
                    origin_node_id=r["origin_node_id"]
                ))
                
            return collider_vectordb_pb2.ToolSearchResponse(matches=matches)
        except Exception as e:
            logger.error(f"Error searching tools: {e}")
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return collider_vectordb_pb2.ToolSearchResponse()
