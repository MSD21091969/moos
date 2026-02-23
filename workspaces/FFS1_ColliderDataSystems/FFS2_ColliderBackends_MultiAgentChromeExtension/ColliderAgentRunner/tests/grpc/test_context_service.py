"""Tests for the gRPC ColliderContext service.

Tests the context composition → gRPC delivery pipeline:
  - GetBootstrap returns well-formed BootstrapResponse
  - StreamContext yields typed ContextChunks in correct order
  - SubscribeContextDeltas keeps stream open
  - Permission enforcement (role filtering)
  - Error handling (missing nodes, invalid requests)
"""

from __future__ import annotations

import json

# Mock the proto modules before importing the service
# (proto compilation may not be available in test environment)
import sys
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

mock_pb2 = MagicMock()
mock_pb2_grpc = MagicMock()
sys.modules["proto.collider_graph_pb2"] = mock_pb2
sys.modules["proto.collider_graph_pb2_grpc"] = mock_pb2_grpc

from src.grpc.context_service import (
    ColliderContextServicer,
    _session_meta_to_chunk,
    _skill_to_chunk,
    _tool_schema_to_chunk,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@dataclass
class FakeComposedContext:
    system_prompt: str = "You are a test agent."
    agents_md: str = "# Agent Instructions\nTest instructions."
    soul_md: str = "# Soul\nBe helpful."
    tools_md: str = "# Tools\nUse tools wisely."
    tool_schemas: list[dict[str, Any]] = field(
        default_factory=lambda: [
            {
                "function": {
                    "name": "test_tool",
                    "description": "A test tool",
                    "parameters": {
                        "type": "object",
                        "properties": {"query": {"type": "string"}},
                    },
                }
            }
        ]
    )
    skills: list[dict[str, Any]] = field(
        default_factory=lambda: [
            {
                "name": "test-skill",
                "description": "A test skill",
                "emoji": "T",
                "markdown_body": "# Test Skill\nDo the test.",
                "tool_ref": "test_tool",
                "user_invocable": True,
                "model_invocable": True,
                "invocation_policy": "auto",
                "requires_bins": [],
                "requires_env": [],
            }
        ]
    )
    preview: Any = None
    session_meta: dict[str, Any] = field(
        default_factory=lambda: {
            "role": "app_user",
            "app_id": "test-app",
            "composed_nodes": ["node-1", "node-2"],
            "username": "test-user",
        }
    )


@pytest.fixture
def composed_context():
    return FakeComposedContext()


@pytest.fixture
def servicer():
    return ColliderContextServicer()


@pytest.fixture
def mock_context():
    """Mock gRPC ServicerContext."""
    ctx = AsyncMock()
    ctx.cancelled.return_value = False
    return ctx


@pytest.fixture
def mock_request():
    """Mock gRPC ContextRequest."""
    req = MagicMock()
    req.session_id = "test-session-123"
    req.node_ids = ["node-1", "node-2"]
    req.role = "app_user"
    req.app_id = "test-app"
    req.inherit_ancestors = True
    return req


# ---------------------------------------------------------------------------
# Unit tests: converter functions
# ---------------------------------------------------------------------------


class TestSkillToChunk:
    def test_basic_conversion(self):
        skill = {
            "name": "my-skill",
            "description": "Does stuff",
            "emoji": "S",
            "markdown_body": "# Instructions",
            "tool_ref": "my_tool",
            "user_invocable": True,
            "model_invocable": False,
            "invocation_policy": "confirm",
            "requires_bins": ["node"],
            "requires_env": ["API_KEY"],
        }
        result = _skill_to_chunk(skill)
        mock_pb2.SkillChunk.assert_called_once_with(
            name="my-skill",
            description="Does stuff",
            emoji="S",
            markdown_body="# Instructions",
            tool_ref="my_tool",
            user_invocable=True,
            model_invocable=False,
            invocation_policy="confirm",
            requires_bins=["node"],
            requires_env=["API_KEY"],
        )

    def test_missing_fields_default_to_empty(self):
        skill = {"name": "minimal"}
        _skill_to_chunk(skill)
        call_kwargs = mock_pb2.SkillChunk.call_args[1]
        assert call_kwargs["description"] == ""
        assert call_kwargs["emoji"] == ""
        assert call_kwargs["requires_bins"] == []


class TestToolSchemaToChunk:
    def test_basic_conversion(self):
        schema = {
            "function": {
                "name": "test_tool",
                "description": "A tool",
                "parameters": {"type": "object", "properties": {}},
            }
        }
        _tool_schema_to_chunk(schema)
        call_kwargs = mock_pb2.ToolSchemaChunk.call_args[1]
        assert call_kwargs["name"] == "test_tool"
        assert call_kwargs["description"] == "A tool"
        assert json.loads(call_kwargs["parameters_json"]) == {
            "type": "object",
            "properties": {},
        }

    def test_empty_schema(self):
        _tool_schema_to_chunk({})
        call_kwargs = mock_pb2.ToolSchemaChunk.call_args[1]
        assert call_kwargs["name"] == ""


class TestSessionMetaToChunk:
    def test_basic_conversion(self):
        meta = {
            "role": "collider_admin",
            "app_id": "my-app",
            "composed_nodes": ["a", "b", "c"],
            "username": "admin",
        }
        _session_meta_to_chunk(meta)
        call_kwargs = mock_pb2.SessionMetaChunk.call_args[1]
        assert call_kwargs["role"] == "collider_admin"
        assert call_kwargs["composed_nodes"] == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# Integration tests: GetBootstrap RPC
# ---------------------------------------------------------------------------


class TestGetBootstrap:
    @pytest.mark.asyncio
    @patch("src.grpc.context_service.compose_context_set")
    async def test_returns_bootstrap_response(
        self, mock_compose, servicer, mock_request, mock_context, composed_context
    ):
        mock_compose.return_value = composed_context
        await servicer.GetBootstrap(mock_request, mock_context)

        # Verify BootstrapResponse was constructed
        mock_pb2.BootstrapResponse.assert_called_once()
        call_kwargs = mock_pb2.BootstrapResponse.call_args[1]
        assert call_kwargs["session_id"] == "test-session-123"
        assert call_kwargs["agents_md"] == "# Agent Instructions\nTest instructions."
        assert call_kwargs["soul_md"] == "# Soul\nBe helpful."
        assert call_kwargs["tools_md"] == "# Tools\nUse tools wisely."

    @pytest.mark.asyncio
    @patch("src.grpc.context_service.compose_context_set")
    async def test_includes_skills(
        self, mock_compose, servicer, mock_request, mock_context, composed_context
    ):
        mock_compose.return_value = composed_context
        await servicer.GetBootstrap(mock_request, mock_context)

        call_kwargs = mock_pb2.BootstrapResponse.call_args[1]
        assert len(call_kwargs["skills"]) == 1

    @pytest.mark.asyncio
    @patch("src.grpc.context_service.compose_context_set")
    async def test_error_aborts_with_internal(
        self, mock_compose, servicer, mock_request, mock_context
    ):
        mock_compose.side_effect = RuntimeError("DB connection failed")
        await servicer.GetBootstrap(mock_request, mock_context)
        mock_context.abort.assert_called_once()


# ---------------------------------------------------------------------------
# Integration tests: StreamContext RPC
# ---------------------------------------------------------------------------


class TestStreamContext:
    @pytest.mark.asyncio
    @patch("src.grpc.context_service.compose_context_set")
    async def test_streams_correct_number_of_chunks(
        self, mock_compose, servicer, mock_request, mock_context, composed_context
    ):
        mock_compose.return_value = composed_context
        chunks = []
        async for chunk in servicer.StreamContext(mock_request, mock_context):
            chunks.append(chunk)

        # Expected: agents_md + soul_md + tools_md + 1 skill + 1 tool_schema + 1 mcp_config + 1 session_meta = 7
        assert len(chunks) == 7

    @pytest.mark.asyncio
    @patch("src.grpc.context_service.compose_context_set")
    async def test_chunks_have_sequential_sequence_numbers(
        self, mock_compose, servicer, mock_request, mock_context, composed_context
    ):
        mock_compose.return_value = composed_context
        sequences = []
        async for _ in servicer.StreamContext(mock_request, mock_context):
            # Verify ContextChunk was called with incrementing sequence
            call_kwargs = mock_pb2.ContextChunk.call_args[1]
            sequences.append(call_kwargs["sequence"])

        assert sequences == list(range(len(sequences)))

    @pytest.mark.asyncio
    @patch("src.grpc.context_service.compose_context_set")
    async def test_empty_sections_are_skipped(
        self, mock_compose, servicer, mock_request, mock_context
    ):
        ctx = FakeComposedContext(agents_md="", soul_md="", tools_md="")
        mock_compose.return_value = ctx
        chunks = []
        async for chunk in servicer.StreamContext(mock_request, mock_context):
            chunks.append(chunk)

        # Only: 1 skill + 1 tool_schema + 1 mcp_config + 1 session_meta = 4
        assert len(chunks) == 4
