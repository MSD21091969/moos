"""
Integration tests for the End-to-End Context Pipeline.
Requires ColliderDataServer running on :8000 and ColliderAgentRunner on :8004 (and gRPC on :50051).
"""

import os
import sys

import httpx
import pytest

pytest.importorskip("grpc")
from grpc import aio

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
)  # ColliderAgentRunner
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
)  # FFS2

# We need the proto definitions to parse the gRPC response
if os.getenv("RUN_E2E_CONTEXT_PIPELINE") != "1":
    pytest.skip(
        "Set RUN_E2E_CONTEXT_PIPELINE=1 to run external-service context pipeline tests",
        allow_module_level=True,
    )

try:
    import proto.collider_graph_pb2 as pb2
    import proto.collider_graph_pb2_grpc as pb2_grpc
except Exception as exc:
    pytest.skip(
        f"Proto runtime not available in this test environment: {exc}",
        allow_module_level=True,
    )


@pytest.mark.asyncio
async def test_full_context_pipeline_e2e():
    """
    POST /agent/session -> Compose -> gRPC GetBootstrap -> verify fields.
    """
    agent_runner_url = "http://localhost:8004"
    grpc_address = "localhost:50051"

    # 1. Create a session
    payload = {
        "role": "superadmin",
        "app_id": "c57ab23a-4a57-4b28-a34c-9700320565ea",  # App 2XZ
        "node_ids": ["9848b323-5e65-4179-a1d6-5b99be9f8b87"],  # Root node
        "vector_query": None,
        "visibility_filter": ["global", "group", "local"],
        "depth": 2,
        "inherit_ancestors": True,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{agent_runner_url}/agent/session", json=payload)
        assert resp.status_code == 200, f"Failed to create session: {resp.text}"
        data = resp.json()

        session_id = data.get("session_id")
        assert session_id is not None

        preview = data.get("preview", {})
        assert preview.get("tool_count", 0) > 0, "No tools discovered in preview"

    # 2. Fetch the composed context over gRPC
    async with aio.insecure_channel(grpc_address) as channel:
        stub = pb2_grpc.ColliderContextStub(channel)
        req = pb2.ContextRequest(session_id=session_id)

        response: pb2.BootstrapResponse = await stub.GetBootstrap(req)

        # 3. Validate the grpc context
        assert response.session_id == session_id
        assert len(response.agents_md) > 0, "agents_md should be populated"
        assert len(response.soul_md) > 0, "soul_md should be populated"
        # We expect at least the built-in or root tools to be loaded
        assert len(response.tool_schemas) > 0, "Tool schemas should be delivered"
        assert response.session_meta is not None
        assert response.session_meta.role == "superadmin"
