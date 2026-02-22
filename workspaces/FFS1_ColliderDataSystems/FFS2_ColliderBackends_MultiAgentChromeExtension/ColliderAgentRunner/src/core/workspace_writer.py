"""Write composed Collider context to NanoClaw workspace files.

Maps the merged bootstrap output to Claude Code's workspace format:
  - CLAUDE.md     ← merged agents_md + soul_md + tools_md (single context file)
  - .mcp.json     ← MCP server config pointing to GraphToolServer
  - skills/<name>/SKILL.md ← dynamic skills in Agent Skills format
  - context/session.json   ← debug metadata

Claude Code reads CLAUDE.md and .mcp.json at session start. Skills are
discovered from the skills/ directory using the Agent Skills specification.
"""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import Any

from src.core.config import settings

logger = logging.getLogger("collider.workspace_writer")


def _format_tool_descriptions(tool_schemas: list[dict[str, Any]]) -> str:
    """Format tool schemas as human-readable markdown for the tools section.

    This tells the LLM what Collider tools are available via MCP.
    """
    if not tool_schemas:
        return ""

    lines = ["## Available Collider Tools\n"]
    lines.append(
        "These tools are available via the MCP server (auto-configured in `.mcp.json`).\n"
    )

    for schema in tool_schemas:
        fn = schema.get("function", {})
        name = fn.get("name", "")
        desc = fn.get("description", "")
        params = fn.get("parameters", {})
        props = params.get("properties", {})
        required = params.get("required", [])

        lines.append(f"### `{name}`")
        if desc:
            lines.append(f"\n{desc}\n")
        if props:
            lines.append("**Parameters:**")
            for pname, pschema in props.items():
                req = " (required)" if pname in required else ""
                pdesc = pschema.get("description", "")
                ptype = pschema.get("type", "any")
                lines.append(f"- `{pname}` ({ptype}{req}): {pdesc}")
            lines.append("")

    return "\n".join(lines)


def _render_claude_md(
    agents_md: str,
    soul_md: str,
    tools_md: str,
    tool_schemas: list[dict[str, Any]],
) -> str:
    """Merge agent context, rules, and tool docs into a single CLAUDE.md."""
    sections: list[str] = []

    if agents_md:
        sections.append(f"# Agent Instructions\n\n{agents_md}")

    if soul_md:
        sections.append(f"# Rules & Guardrails\n\n{soul_md}")

    tool_desc = _format_tool_descriptions(tool_schemas)
    if tools_md or tool_desc:
        tools_parts = []
        if tools_md:
            tools_parts.append(tools_md)
        if tool_desc:
            tools_parts.append(tool_desc)
        sections.append("# Tools & Reference\n\n" + "\n\n---\n\n".join(tools_parts))

    return "\n\n---\n\n".join(sections) + "\n"


def _render_mcp_json(mcp_url: str | None = None) -> str:
    """Generate .mcp.json pointing to the Collider GraphToolServer MCP endpoint."""
    url = mcp_url or settings.graph_tool_mcp_url
    config = {
        "mcpServers": {
            "collider-tools": {
                "type": "sse",
                "url": url,
            }
        }
    }
    return json.dumps(config, indent=2) + "\n"


def _render_skill_md(skill: dict[str, Any]) -> str:
    """Render a Collider SkillEntry as Agent Skills SKILL.md content."""
    name = skill.get("name", "unnamed")
    description = skill.get("description", "")
    user_invocable = skill.get("user_invocable", True)
    model_invocable = skill.get("model_invocable", True)
    markdown_body = skill.get("markdown_body", "")

    # Build YAML frontmatter (Agent Skills spec)
    fm_lines = [
        "---",
        f"name: {name}",
        f"description: {description}",
    ]

    if not user_invocable:
        fm_lines.append("user-invocable: false")
    if not model_invocable:
        fm_lines.append("disable-model-invocation: true")

    fm_lines.append("---")

    parts = ["\n".join(fm_lines)]
    if markdown_body:
        parts.append(markdown_body)

    return "\n\n".join(parts) + "\n"


async def write_workspace(
    workspace_dir: Path,
    agents_md: str,
    soul_md: str,
    tools_md: str,
    tool_schemas: list[dict[str, Any]],
    skills: list[dict[str, Any]],
    session_meta: dict[str, Any],
    static_skills_dir: Path | None = None,
    mcp_url: str | None = None,
) -> None:
    """Write composed Collider context to a NanoClaw workspace directory.

    Creates/overwrites workspace files that Claude Code loads at session start.
    Static skills (e.g. collider-mcp) are copied from ``static_skills_dir``.
    Dynamic skills from the bootstrap are rendered as Agent Skills SKILL.md files.

    Args:
        workspace_dir: Target NanoClaw workspace directory.
        agents_md: Merged agent identity / instructions.
        soul_md: Merged rules / guardrails.
        tools_md: Merged knowledge / reference docs.
        tool_schemas: List of tool schema dicts (OpenAI function format).
        skills: List of skill entry dicts from bootstrap merge.
        session_meta: Session metadata (session_id, role, app_id, nodes).
        static_skills_dir: Path to static skill directories to copy.
        mcp_url: GraphToolServer MCP endpoint URL override.
    """
    workspace_dir = workspace_dir.expanduser().resolve()
    workspace_dir.mkdir(parents=True, exist_ok=True)

    total_chars = 0

    # --- CLAUDE.md (merged context) ---
    claude_content = _render_claude_md(agents_md, soul_md, tools_md, tool_schemas)
    if claude_content.strip():
        (workspace_dir / "CLAUDE.md").write_text(claude_content, encoding="utf-8")
        total_chars += len(claude_content)
        logger.debug("Wrote CLAUDE.md (%d chars)", len(claude_content))

    # --- .mcp.json (MCP server config for Claude Code) ---
    mcp_content = _render_mcp_json(mcp_url)
    (workspace_dir / ".mcp.json").write_text(mcp_content, encoding="utf-8")
    logger.debug("Wrote .mcp.json")

    # --- skills/ directory ---
    skills_dir = workspace_dir / "skills"
    skills_dir.mkdir(exist_ok=True)

    # Copy static skills (e.g. collider-mcp/SKILL.md)
    if static_skills_dir and static_skills_dir.is_dir():
        for skill_subdir in static_skills_dir.iterdir():
            if skill_subdir.is_dir():
                dest = skills_dir / skill_subdir.name
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(skill_subdir, dest)
                logger.debug("Copied static skill: %s", skill_subdir.name)

    # Write dynamic skills from bootstrap (Agent Skills format)
    for skill in skills:
        name = skill.get("name", "")
        if not name:
            continue
        skill_dir = skills_dir / name
        skill_dir.mkdir(exist_ok=True)
        content = _render_skill_md(skill)
        (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
        total_chars += len(content)

    # --- context/session.json (metadata for debugging) ---
    ctx_dir = workspace_dir / "context"
    ctx_dir.mkdir(exist_ok=True)
    session_json = json.dumps(session_meta, indent=2)
    (ctx_dir / "session.json").write_text(session_json, encoding="utf-8")

    # Clean up legacy workspace files if they exist from previous format
    for old_file in ("AGENTS.md", "SOUL.md", "TOOLS.md"):
        old_path = workspace_dir / old_file
        if old_path.exists():
            old_path.unlink()
            logger.info("Removed legacy workspace file: %s", old_file)

    logger.info(
        "Workspace written: %s (%d chars, %d skills, %d tools)",
        workspace_dir,
        total_chars,
        len(skills),
        len(tool_schemas),
    )
