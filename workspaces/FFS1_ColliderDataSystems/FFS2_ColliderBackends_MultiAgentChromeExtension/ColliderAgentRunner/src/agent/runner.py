"""pydantic-ai agent runner — hydrates from OpenClaw bootstrap, streams responses."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

from src.agent.tools import build_tools
from src.core.auth_client import auth_client
from src.core import collider_client
from src.core.config import settings


async def run_agent_stream(node_id: str, user_message: str) -> AsyncIterator[str]:
    """Authenticate, bootstrap, and stream an LLM response for one turn.

    Flow:
      1. Fetch (or reuse cached) JWT from DataServer ``/auth/login``.
      2. GET ``/openclaw/bootstrap/{node_id}`` → full NodeContainer context.
      3. Build system prompt from: agents_md + soul_md + tools_md + skill playbooks
         + session ACL context (username, system_role, app_id).
      4. Register dynamic tool functions from tool_schemas.
      5. Run pydantic-ai agent and stream text deltas.

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


def _build_system_prompt(bootstrap: dict[str, Any], user: dict[str, Any]) -> str:
    """Compose the full system prompt from OpenClaw bootstrap fields.

    Sections (separated by ``---``):
      - agents_md (agent identity / role)
      - soul_md (guardrails / rules)
      - tools_md (knowledge / reference docs)
      - Skill playbooks (each skill's markdown_body)
      - Session context (username, system_role, app_id)

    Args:
        bootstrap: OpenClawBootstrap JSON dict from DataServer.
        user: User dict from the last successful login (username, system_role, id).

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

    parts.append(
        f"## Session Context\n\n"
        f"- **User:** {username}\n"
        f"- **System role:** {role}\n"
        f"- **Application:** {app_id}\n"
        f"- **Active node:** {node_path or bootstrap.get('node_id', '')}"
    )

    return "\n\n---\n\n".join(parts)
