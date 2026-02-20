"""gRPC Client for VectorDB Service."""

import logging
import grpc
from typing import Any

from proto import collider_vectordb_pb2
from proto import collider_vectordb_pb2_grpc

logger = logging.getLogger(__name__)


class VectorDbClient:
    """Async client for VectorDbServer."""

    def __init__(self, host: str = "localhost", port: int = 8002):
        self._target = f"{host}:{port}"
        self._channel = None
        self._stub = None

    async def _ensure_channel(self):
        if self._channel is None:
            self._channel = grpc.aio.insecure_channel(self._target)
            self._stub = collider_vectordb_pb2_grpc.ColliderVectorDbStub(self._channel)

    async def index_tool(
        self,
        tool_name: str,
        description: str,
        origin_node_id: str,
        owner_user_id: str,
        params_schema_json: str,
    ) -> bool:
        """Index a tool in the VectorDB."""
        try:
            await self._ensure_channel()
            request = collider_vectordb_pb2.ToolIndexRequest(
                tool_name=tool_name,
                description=description,
                origin_node_id=origin_node_id,
                owner_user_id=owner_user_id,
                params_schema_json=params_schema_json
            )
            response = await self._stub.IndexTool(request)
            return response.success
        except grpc.RpcError as e:
            logger.warning(f"VectorDB IndexTool failed: {e.details()} (Code: {e.code()})")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in index_tool: {e}")
            return False

    async def search_tools(
        self,
        query: str,
        limit: int = 5,
        owner_user_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search for tools."""
        try:
            await self._ensure_channel()
            request = collider_vectordb_pb2.ToolSearchRequest(
                query=query,
                limit=limit,
                owner_user_id=owner_user_id if owner_user_id else ""
            )
            response = await self._stub.SearchTools(request)
            
            matches = []
            for m in response.matches:
                matches.append({
                    "name": m.tool_name,
                    "description": m.description,
                    "score": m.score,
                    "origin_node_id": m.origin_node_id
                })
            return matches
        except grpc.RpcError as e:
            logger.warning(f"VectorDB SearchTools failed: {e.details()}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in search_tools: {e}")
            return []

    async def close(self):
        if self._channel:
            await self._channel.close()

# Singleton instance
vector_client = VectorDbClient()
