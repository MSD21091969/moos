"""Tests for NanoClaw workspace writer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from src.core.workspace_writer import (
    _format_tool_descriptions,
    _render_skill_md,
    _truncate,
    write_workspace,
)


@pytest.fixture
def tmp_workspace(tmp_path: Path) -> Path:
    return tmp_path / "workspace"


# ---------------------------------------------------------------------------
# _truncate
# ---------------------------------------------------------------------------


def test_truncate_within_limit():
    assert _truncate("hello", 100) == "hello"


def test_truncate_at_limit():
    content = "x" * 20_000
    assert _truncate(content) == content


def test_truncate_over_limit():
    content = "x" * 21_000
    result = _truncate(content)
    assert len(result) < 21_000
    assert "truncated" in result


# ---------------------------------------------------------------------------
# _format_tool_descriptions
# ---------------------------------------------------------------------------


def test_format_tool_descriptions_empty():
    assert _format_tool_descriptions([]) == ""


def test_format_tool_descriptions_with_tools():
    schemas = [
        {
            "type": "function",
            "function": {
                "name": "list_nodes",
                "description": "List all nodes in an app",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "app_id": {
                            "type": "string",
                            "description": "Application UUID",
                        }
                    },
                    "required": ["app_id"],
                },
            },
        }
    ]
    result = _format_tool_descriptions(schemas)
    assert "list_nodes" in result
    assert "app_id" in result
    assert "(required)" in result
    assert "collider-grpc" in result


# ---------------------------------------------------------------------------
# _render_skill_md
# ---------------------------------------------------------------------------


def test_render_skill_md_basic():
    skill = {
        "name": "test-skill",
        "description": "A test skill",
        "markdown_body": "# Usage\nDo things.",
    }
    result = _render_skill_md(skill)
    assert "---" in result
    assert "name: test-skill" in result
    assert "description: A test skill" in result
    assert "# Usage" in result


def test_render_skill_md_with_metadata():
    skill = {
        "name": "gated-skill",
        "description": "Needs env",
        "emoji": "🔧",
        "requires_bins": ["grpcurl"],
        "requires_env": ["API_KEY"],
        "markdown_body": "",
    }
    result = _render_skill_md(skill)
    assert "metadata:" in result
    assert "grpcurl" in result
    assert "API_KEY" in result


# ---------------------------------------------------------------------------
# write_workspace
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_write_workspace_creates_files(tmp_workspace: Path):
    await write_workspace(
        workspace_dir=tmp_workspace,
        agents_md="Agent instructions here",
        soul_md="Rules here",
        tools_md="Reference docs",
        tool_schemas=[
            {
                "type": "function",
                "function": {
                    "name": "list_apps",
                    "description": "Lists apps",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ],
        skills=[],
        session_meta={"session_id": "test-123", "role": "app_user"},
    )

    assert (tmp_workspace / "AGENTS.md").exists()
    assert (tmp_workspace / "SOUL.md").exists()
    assert (tmp_workspace / "TOOLS.md").exists()
    assert (tmp_workspace / "context" / "session.json").exists()

    agents = (tmp_workspace / "AGENTS.md").read_text()
    assert "Agent instructions here" in agents

    tools = (tmp_workspace / "TOOLS.md").read_text()
    assert "list_apps" in tools

    meta = json.loads((tmp_workspace / "context" / "session.json").read_text())
    assert meta["session_id"] == "test-123"


@pytest.mark.asyncio
async def test_write_workspace_with_skills(tmp_workspace: Path):
    await write_workspace(
        workspace_dir=tmp_workspace,
        agents_md="",
        soul_md="",
        tools_md="",
        tool_schemas=[],
        skills=[
            {
                "name": "my-skill",
                "description": "Does stuff",
                "markdown_body": "# How\nDo the thing.",
            }
        ],
        session_meta={},
    )

    skill_path = tmp_workspace / "skills" / "my-skill" / "SKILL.md"
    assert skill_path.exists()
    content = skill_path.read_text()
    assert "name: my-skill" in content
    assert "# How" in content


@pytest.mark.asyncio
async def test_write_workspace_copies_static_skills(tmp_workspace: Path, tmp_path: Path):
    # Create a static skill dir
    static_dir = tmp_path / "static-skills"
    grpc_skill = static_dir / "collider-grpc"
    grpc_skill.mkdir(parents=True)
    (grpc_skill / "SKILL.md").write_text("# gRPC skill\nConnect to :50052")

    await write_workspace(
        workspace_dir=tmp_workspace,
        agents_md="",
        soul_md="",
        tools_md="",
        tool_schemas=[],
        skills=[],
        session_meta={},
        static_skills_dir=static_dir,
    )

    copied = tmp_workspace / "skills" / "collider-grpc" / "SKILL.md"
    assert copied.exists()
    assert ":50052" in copied.read_text()


@pytest.mark.asyncio
async def test_write_workspace_empty_content_skips_files(tmp_workspace: Path):
    await write_workspace(
        workspace_dir=tmp_workspace,
        agents_md="",
        soul_md="",
        tools_md="",
        tool_schemas=[],
        skills=[],
        session_meta={},
    )

    # Empty content files should not be written
    assert not (tmp_workspace / "AGENTS.md").exists()
    assert not (tmp_workspace / "SOUL.md").exists()
    # But context/session.json always written
    assert (tmp_workspace / "context" / "session.json").exists()
