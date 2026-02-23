import json
import uuid

from proto import collider_graph_pb2 as pb2
from src.grpc.context_service import (
    _session_meta_to_chunk,
    _skill_to_chunk,
    _tool_schema_to_chunk,
)


def test_bootstrap_response_has_all_fields():
    """Ensure BootstrapResponse has session_id, agents_md, soul_md, etc."""
    skill_chunk = pb2.SkillChunk(name="test_skill", markdown_body="body")
    tool_chunk = pb2.ToolSchemaChunk(name="test_tool", parameters_json=b'{}')
    mcp_chunk = pb2.McpConfigChunk(name="mcp", transport_type="sse", url="http://mcp")
    meta_chunk = pb2.SessionMetaChunk(role="admin", app_id="test_app")
    
    resp = pb2.BootstrapResponse(
        session_id="test_session",
        agents_md="# agents",
        soul_md="# soul",
        tools_md="# tools",
        skills=[skill_chunk],
        tool_schemas=[tool_chunk],
        mcp_servers=[mcp_chunk],
        session_meta=meta_chunk,
    )
    
    assert resp.session_id == "test_session"
    assert resp.agents_md == "# agents"
    assert resp.soul_md == "# soul"
    assert resp.tools_md == "# tools"
    assert len(resp.skills) == 1
    assert resp.skills[0].name == "test_skill"
    assert len(resp.tool_schemas) == 1
    assert resp.tool_schemas[0].name == "test_tool"
    assert len(resp.mcp_servers) == 1
    assert resp.mcp_servers[0].name == "mcp"
    assert resp.session_meta.role == "admin"


def test_context_chunk_oneof_coverage():
    """Every oneof variant (skill, tool_schema, system_prompt, etc.) can be constructed."""
    
    # 1. SystemPrompt
    c1 = pb2.ContextChunk(
        chunk_id=str(uuid.uuid4()),
        sequence=0,
        system_prompt=pb2.SystemPromptChunk(section="agents_md", content="..."),
    )
    assert c1.HasField("system_prompt")
    
    # 2. Skill
    c2 = pb2.ContextChunk(
        chunk_id=str(uuid.uuid4()),
        sequence=1,
        skill=pb2.SkillChunk(name="skill1"),
    )
    assert c2.HasField("skill")
    
    # 3. ToolSchema
    c3 = pb2.ContextChunk(
        chunk_id=str(uuid.uuid4()),
        sequence=2,
        tool_schema=pb2.ToolSchemaChunk(name="tool1"),
    )
    assert c3.HasField("tool_schema")
    
    # 4. McpConfig
    c4 = pb2.ContextChunk(
        chunk_id=str(uuid.uuid4()),
        sequence=3,
        mcp_config=pb2.McpConfigChunk(name="mcp1"),
    )
    assert c4.HasField("mcp_config")
    
    # 5. SessionMeta
    c5 = pb2.ContextChunk(
        chunk_id=str(uuid.uuid4()),
        sequence=4,
        session_meta=pb2.SessionMetaChunk(role="user"),
    )
    assert c5.HasField("session_meta")


def test_skill_chunk_round_trip():
    """SkillDefinition dict → SkillChunk protobuf"""
    
    skill_dict = {
        "name": "search",
        "description": "Search the web",
        "emoji": "🔍",
        "markdown_body": "Use this to search",
        "tool_ref": "web_search",
        "user_invocable": False,
        "model_invocable": True,
        "invocation_policy": "disabled",
        "requires_bins": ["curl", "jq"],
        "requires_env": ["API_KEY"],
    }
    
    chunk = _skill_to_chunk(skill_dict)
    
    assert chunk.name == "search"
    assert chunk.description == "Search the web"
    assert chunk.emoji == "🔍"
    assert chunk.markdown_body == "Use this to search"
    assert chunk.tool_ref == "web_search"
    assert chunk.user_invocable is False
    assert chunk.model_invocable is True
    assert chunk.invocation_policy == "disabled"
    assert list(chunk.requires_bins) == ["curl", "jq"]
    assert list(chunk.requires_env) == ["API_KEY"]


def test_tool_schema_chunk_conversion():
    schema_dict = {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Gets the weather",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                }
            }
        }
    }
    
    chunk = _tool_schema_to_chunk(schema_dict)
    assert chunk.name == "get_weather"
    assert chunk.description == "Gets the weather"
    
    params = json.loads(chunk.parameters_json.decode("utf-8"))
    assert params["type"] == "object"
    assert "location" in params["properties"]


def test_session_meta_chunk_conversion():
    meta_dict = {
        "role": "app_admin",
        "app_id": "test_app",
        "composed_nodes": ["node1", "node2"],
        "username": "Sam"
    }
    
    chunk = _session_meta_to_chunk(meta_dict)
    assert chunk.role == "app_admin"
    assert chunk.app_id == "test_app"
    assert list(chunk.composed_nodes) == ["node1", "node2"]
    assert chunk.username == "Sam"
