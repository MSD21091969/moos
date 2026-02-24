"""Agent runner — composes Collider bootstrap context for NanoClaw sessions.

NanoClaw (ws://127.0.0.1:18789) is the LLM agent. This module handles:
  - Context hydration: bootstrap Collider nodes → system prompt + tool schemas
  - Session composition: merge multiple node bootstraps (leaf-wins strategy)
  - Vector tool discovery: augment composed context via GraphToolServer

Chat streaming is handled directly by the Chrome extension via WebSocket to
NanoClaw's bridge. AgentRunner returns nanoclaw_ws_url in session responses.
NanoClaw calls Collider tools via gRPC at grpc://localhost:50052.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import zip_longest
from typing import Any

from src.core import collider_client, graph_tool_client
from src.core.auth_client import auth_client
from src.schemas.context_set import ContextSet, SessionPreview


@dataclass
class ComposedContext:
    """Full output of compose_context_set — raw parts + merged prompt."""

    system_prompt: str
    agents_md: str
    soul_md: str
    tools_md: str
    tool_schemas: list[dict[str, Any]]
    skills: list[dict[str, Any]]
    preview: SessionPreview
    session_meta: dict[str, Any] = field(default_factory=dict)


async def compose_context_set(
    ctx: ContextSet,
) -> ComposedContext:
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
        ComposedContext with system prompt, raw parts, and preview.
    """
    token = await auth_client.get_token_for_role(ctx.role)
    user = auth_client.user_for_role(ctx.role)

    # --- Fetch all bootstraps (optionally prepend ancestors) ---
    bootstraps: list[dict[str, Any]] = []
    seen_node_ids: set[str] = set()

    for node_id in ctx.node_ids:
        # Prepend ancestor context (root-first) before the selected node
        if ctx.inherit_ancestors:
            try:
                ancestors = await collider_client.get_node_ancestors(
                    ctx.app_id, node_id, token
                )
                for ancestor in ancestors:
                    ancestor_id = ancestor["id"]
                    if ancestor_id not in seen_node_ids:
                        seen_node_ids.add(ancestor_id)
                        try:
                            ab = await collider_client.get_bootstrap(
                                ancestor_id,
                                token,
                                depth=0,  # root only, no subtree
                            )
                            bootstraps.append(ab)
                        except Exception:  # noqa: BLE001
                            pass
            except Exception:  # noqa: BLE001
                pass  # Ancestor fetch failure is non-fatal

        if node_id not in seen_node_ids:
            seen_node_ids.add(node_id)
            try:
                b = await collider_client.get_bootstrap(node_id, token, depth=ctx.depth)
                bootstraps.append(b)
            except Exception:  # noqa: BLE001
                pass

    if not bootstraps:
        # No valid nodes — return a minimal identity context
        system_prompt = _role_context_only(ctx.role, user)
        return ComposedContext(
            system_prompt=system_prompt,
            agents_md="",
            soul_md="",
            tools_md="",
            tool_schemas=[],
            skills=[],
            preview=SessionPreview(
                node_count=0,
                skill_count=0,
                tool_count=0,
                role=ctx.role,
                vector_matches=0,
            ),
            session_meta={
                "role": ctx.role,
                "app_id": ctx.app_id,
                "composed_nodes": ctx.node_ids,
            },
        )

    # --- Merge bootstraps (leaf-wins: later entries in node_ids win) ---
    agents_md_parts: list[str] = []
    soul_md_parts: list[str] = []
    tools_md_parts: list[str] = []
    skill_map: dict[str, dict[str, Any]] = {}
    tool_schema_map: dict[str, dict[str, Any]] = {}
    selected_node_ids = set(ctx.node_ids)

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

        source_node_id = str(b.get("node_id", ""))
        source_scope = "local" if source_node_id in selected_node_ids else "inherited"
        for skill in b.get("skills", []):
            if not isinstance(skill, dict):
                continue

            skill_name = str(skill.get("name", "")).strip()
            if not skill_name:
                continue

            incoming_skill = dict(skill)
            incoming_skill.setdefault("source_node_path", node_label)
            incoming_skill.setdefault("source_node_id", source_node_id)
            incoming_skill.setdefault("scope", source_scope)

            key = _skill_merge_key(incoming_skill)
            existing = skill_map.get(key)
            skill_map[key] = _resolve_skill_conflict(existing, incoming_skill)
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
    skills_list = list(skill_map.values())

    preview = SessionPreview(
        node_count=len(bootstraps),
        skill_count=len(skill_map),
        tool_count=len(tool_schemas_list),
        role=ctx.role,
        vector_matches=vector_matches,
    )

    return ComposedContext(
        system_prompt=system_prompt,
        agents_md="\n\n".join(agents_md_parts),
        soul_md="\n\n".join(soul_md_parts),
        tools_md="\n\n".join(tools_md_parts),
        tool_schemas=tool_schemas_list,
        skills=skills_list,
        preview=preview,
        session_meta={
            "role": ctx.role,
            "app_id": ctx.app_id,
            "composed_nodes": ctx.node_ids,
        },
    )


def _skill_merge_key(skill: dict[str, Any]) -> str:
    """Compute deterministic merge key for skills.

    Namespace-aware keying avoids accidental collisions across domains while
    preserving backward compatibility when namespace is omitted.
    """
    name = str(skill.get("name", "")).strip()
    namespace = str(skill.get("namespace") or "").strip()
    return f"{namespace}::{name}" if namespace else name


def _resolve_skill_conflict(
    existing: dict[str, Any] | None,
    incoming: dict[str, Any],
) -> dict[str, Any]:
    """Resolve deterministic conflict between two skill entries.

    Policy:
      - If both have parseable versions, higher version wins.
      - If only one has parseable version, prefer the versioned entry.
      - Otherwise, leaf-wins fallback (incoming overrides existing).
    """
    if existing is None:
        return incoming

    existing_version = _parse_version(existing.get("version"))
    incoming_version = _parse_version(incoming.get("version"))

    if existing_version and incoming_version:
        if _compare_versions(incoming_version, existing_version) >= 0:
            return incoming
        return existing

    if incoming_version and not existing_version:
        return incoming
    if existing_version and not incoming_version:
        return existing

    return incoming


def _parse_version(raw: Any) -> tuple[int, ...] | None:
    """Parse semantic-ish version strings into integer tuples."""
    if not raw:
        return None
    version = str(raw).strip()
    if not version:
        return None

    parts: list[int] = []
    for piece in version.split("."):
        digits = "".join(ch for ch in piece if ch.isdigit())
        if not digits:
            return None
        parts.append(int(digits))

    return tuple(parts)


def _compare_versions(left: tuple[int, ...], right: tuple[int, ...]) -> int:
    """Return positive when left > right, 0 when equal, negative when left < right."""
    for lhs, rhs in zip_longest(left, right, fillvalue=0):
        if lhs > rhs:
            return 1
        if lhs < rhs:
            return -1
    return 0


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
    """Compose the full system prompt from agent bootstrap fields.

    Sections (separated by ``---``):
      - agents_md (agent identity / role)
      - soul_md (guardrails / rules)
      - tools_md (knowledge / reference docs)
      - Skill playbooks (each skill's markdown_body)
      - Session context (username, system_role, app_id, composed nodes)

    Args:
        bootstrap: Merged AgentBootstrap-like dict.
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
        ctx_lines.append(
            f"- **Active node:** {node_path or bootstrap.get('node_id', '')}"
        )

    parts.append("## Session Context\n\n" + "\n".join(ctx_lines))

    return "\n\n---\n\n".join(parts)
