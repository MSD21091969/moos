"""pydantic-ai agent runner — hydrates from OpenClaw bootstrap, streams responses."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

from src.agent.tools import build_tools
from src.core.auth_client import auth_client
from src.core import collider_client, graph_tool_client
from src.core.config import settings
from src.schemas.context_set import ContextSet, SessionPreview


async def run_agent_stream(node_id: str, user_message: str) -> AsyncIterator[str]:
    """Authenticate, bootstrap a single node, and stream an LLM response.

    Legacy single-node path — kept for backward compatibility.

    Args:
        node_id: Collider node UUID (leaf segment of selectedNodePath).
        user_message: The user's chat input.

    Yields:
        String chunks (text deltas) from the LLM.
    """
    token = await auth_client.get_token()
    bootstrap = await collider_client.get_bootstrap(node_id, token)

    system_prompt = _build_system_prompt(bootstrap, auth_client.user)
    tools = build_tools(bootstrap.get("tool_schemas", []), token)

    agent: Agent[None, str] = Agent(
        model=AnthropicModel(settings.agent_model),
        system_prompt=system_prompt,
        tools=tools,
    )

    async with agent.run_stream(user_message) as result:
        async for chunk in result.stream_text(delta=True):
            yield chunk


async def run_session_stream(
    system_prompt: str,
    tool_schemas: list[dict[str, Any]],
    user_message: str,
    token: str,
) -> AsyncIterator[str]:
    """Stream an LLM response from a pre-composed session context.

    Args:
        system_prompt: Pre-built system prompt from compose_context_set().
        tool_schemas: Pre-merged tool schema list from compose_context_set().
        user_message: The user's chat input.
        token: Valid Bearer JWT (default credentials).

    Yields:
        String chunks (text deltas) from the LLM.
    """
    tools = build_tools(tool_schemas, token)
    agent: Agent[None, str] = Agent(
        model=AnthropicModel(settings.agent_model),
        system_prompt=system_prompt,
        tools=tools,
    )
    async with agent.run_stream(user_message) as result:
        async for chunk in result.stream_text(delta=True):
            yield chunk


async def compose_context_set(
    ctx: ContextSet,
) -> tuple[str, list[dict[str, Any]], SessionPreview]:
    """Compose a full agent context from a ContextSet specification.

    Steps:
      1. Authenticate as the role's configured credentials.
      2. Bootstrap each node in ``ctx.node_ids`` (with optional depth limit).
      3. Merge all bootstraps — leaf-wins dict strategy (later node overrides):
         - agents_md / soul_md / tools_md: concatenated with node-path headers
         - skills: ``{name → entry}``, later nodes override earlier
         - tool_schemas: ``{fn_name → schema}``, later nodes override earlier
      4. If ``ctx.vector_query``: discover tools via GraphToolServer and extend
         the tool_schema map (vector matches add, do not override existing).
      5. Apply ``ctx.visibility_filter``: drop schemas not matching any listed
         visibility level (note: bootstrapped schemas don't carry visibility;
         the filter applies only to vector-discovered GraphStepEntry tools).
      6. Build system prompt from merged context + role session context.

    Args:
        ctx: The ContextSet specifying role, nodes, vector query, and filters.

    Returns:
        Tuple of (system_prompt, tool_schemas_list, SessionPreview).
    """
    token = await auth_client.get_token_for_role(ctx.role)
    user = auth_client.user_for_role(ctx.role)

    # --- Fetch all bootstraps ---
    bootstraps: list[dict[str, Any]] = []
    for node_id in ctx.node_ids:
        try:
            b = await collider_client.get_bootstrap(node_id, token, depth=ctx.depth)
            bootstraps.append(b)
        except Exception:  # noqa: BLE001
            # Skip unreachable nodes; log is handled in collider_client
            pass

    if not bootstraps:
        # No valid nodes — return a minimal identity context
        system_prompt = _role_context_only(ctx.role, user)
        return system_prompt, [], SessionPreview(
            node_count=0, skill_count=0, tool_count=0,
            role=ctx.role, vector_matches=0,
        )

    # --- Merge bootstraps (leaf-wins: later entries in node_ids win) ---
    agents_md_parts: list[str] = []
    soul_md_parts: list[str] = []
    tools_md_parts: list[str] = []
    skill_map: dict[str, dict[str, Any]] = {}
    tool_schema_map: dict[str, dict[str, Any]] = {}

    for b in bootstraps:
        node_label = b.get("node_path") or b.get("node_id", "")

        a = b.get("agents_md", "")
        if a:
            agents_md_parts.append(f"<!-- node: {node_label} -->\n{a}")
        s = b.get("soul_md", "")
        if s:
            soul_md_parts.append(s)
        t = b.get("tools_md", "")
        if t:
            tools_md_parts.append(t)

        for skill in b.get("skills", []):
            skill_map[skill.get("name", "")] = skill
        for schema in b.get("tool_schemas", []):
            fn = schema.get("function", {})
            name = fn.get("name", "")
            if name:
                tool_schema_map[name] = schema

    # --- Vector-augmented tool discovery ---
    vector_matches = 0
    if ctx.vector_query:
        discovered = await graph_tool_client.discover_tools(
            query=ctx.vector_query,
            visibility_filter=ctx.visibility_filter,
        )
        for schema in discovered:
            fn_name = schema.get("function", {}).get("name", "")
            if fn_name and fn_name not in tool_schema_map:
                tool_schema_map[fn_name] = schema
                vector_matches += 1

    merged_bootstrap: dict[str, Any] = {
        "agents_md": "\n\n".join(agents_md_parts),
        "soul_md": "\n\n".join(soul_md_parts),
        "tools_md": "\n\n".join(tools_md_parts),
        "skills": list(skill_map.values()),
        "tool_schemas": list(tool_schema_map.values()),
        "session_context": {
            "user_role": ctx.role,
            "app_id": ctx.app_id,
            "composed_nodes": ctx.node_ids,
        },
        "node_path": f"[{len(bootstraps)} nodes]",
        "node_id": ctx.app_id,
    }

    system_prompt = _build_system_prompt(merged_bootstrap, user)
    tool_schemas_list = list(tool_schema_map.values())

    preview = SessionPreview(
        node_count=len(bootstraps),
        skill_count=len(skill_map),
        tool_count=len(tool_schemas_list),
        role=ctx.role,
        vector_matches=vector_matches,
    )

    return system_prompt, tool_schemas_list, preview


def _role_context_only(role: str, user: dict[str, Any]) -> str:
    """Minimal system prompt when no nodes could be bootstrapped."""
    username = user.get("username", "unknown")
    return (
        f"You are a Collider AI agent.\n\n"
        f"## Session Context\n\n"
        f"- **User:** {username}\n"
        f"- **System role:** {role}\n"
        f"- **Note:** No workspace nodes could be loaded for this session."
    )


def _build_system_prompt(bootstrap: dict[str, Any], user: dict[str, Any]) -> str:
    """Compose the full system prompt from OpenClaw bootstrap fields.

    Sections (separated by ``---``):
      - agents_md (agent identity / role)
      - soul_md (guardrails / rules)
      - tools_md (knowledge / reference docs)
      - Skill playbooks (each skill's markdown_body)
      - Session context (username, system_role, app_id, composed nodes)

    Args:
        bootstrap: Merged OpenClawBootstrap-like dict.
        user: User dict from the role login (username, system_role, id).

    Returns:
        Fully composed system prompt string.
    """
    parts: list[str] = []

    agents_md: str = bootstrap.get("agents_md", "")
    if agents_md:
        parts.append(agents_md)

    soul_md: str = bootstrap.get("soul_md", "")
    if soul_md:
        parts.append(soul_md)

    tools_md: str = bootstrap.get("tools_md", "")
    if tools_md:
        parts.append(tools_md)

    for skill in bootstrap.get("skills", []):
        body: str = skill.get("markdown_body", "")
        name: str = skill.get("name", "Skill")
        if body:
            parts.append(f"## Skill: {name}\n\n{body}")

    session: dict[str, Any] = bootstrap.get("session_context", {})
    username: str = user.get("username", "unknown")
    role: str = str(session.get("user_role") or user.get("system_role") or "unknown")
    app_id: str = str(session.get("app_id", "unknown"))
    node_path: str = bootstrap.get("node_path", "")
    composed: list[str] = session.get("composed_nodes", [])

    ctx_lines = [
        f"- **User:** {username}",
        f"- **System role:** {role}",
        f"- **Application:** {app_id}",
    ]
    if composed:
        ctx_lines.append(f"- **Composed nodes:** {', '.join(composed)}")
    else:
        ctx_lines.append(f"- **Active node:** {node_path or bootstrap.get('node_id', '')}")

    parts.append("## Session Context\n\n" + "\n".join(ctx_lines))

    return "\n\n---\n\n".join(parts)
