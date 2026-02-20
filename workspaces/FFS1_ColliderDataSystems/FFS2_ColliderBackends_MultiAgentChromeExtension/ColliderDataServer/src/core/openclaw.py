"""OpenClaw rendering logic.

Converts a database ``Node`` + its ``NodeContainer`` into an
``OpenClawBootstrap`` response that an OpenClaw agent workspace can consume
directly.

The bootstrap renderer supports **recursive subtree aggregation**: when
``descendants`` is supplied (a BFS-ordered list of child nodes), skills and
tool schemas from each descendant are merged into the response.  Leaf entries
take precedence over root entries (more-specific wins), mirroring OpenClaw's
own skill-precedence stack (workspace < project < personal < bundled).
"""

from __future__ import annotations

from src.db.models import Node, User
from src.schemas.nodes import NodeContainer
from src.schemas.openclaw import (
    OpenClawBootstrap,
    OpenClawSkillEntry,
    OpenClawToolSchema,
)

# ---------------------------------------------------------------------------
# Execute-workflow tool schema (injected into every bootstrap response)
# ---------------------------------------------------------------------------

_EXECUTE_WORKFLOW_SCHEMA: dict = {
    "type": "function",
    "function": {
        "name": "execute_workflow",
        "description": (
            "Execute a named Collider workflow. "
            "Calls POST /execution/workflow/{workflow_name} on the DataServer."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "workflow_name": {
                    "type": "string",
                    "description": "The workflow name as registered in the NodeContainer.",
                },
                "inputs": {
                    "type": "object",
                    "description": "Key-value inputs passed to the workflow entry step.",
                },
            },
            "required": ["workflow_name"],
        },
    },
}

_EXECUTE_TOOL_SCHEMA: dict = {
    "type": "function",
    "function": {
        "name": "execute_tool",
        "description": (
            "Execute a single registered Collider tool by name. "
            "Calls POST /execution/tool/{tool_name} on the DataServer."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": "The tool name as registered in the NodeContainer.",
                },
                "inputs": {
                    "type": "object",
                    "description": "Key-value inputs matching the tool's params_schema.",
                },
            },
            "required": ["tool_name"],
        },
    },
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _skill_entry(skill) -> OpenClawSkillEntry:
    return OpenClawSkillEntry(
        name=skill.name,
        description=skill.description,
        emoji=skill.emoji,
        requires_bins=skill.requires_bins,
        requires_env=skill.requires_env,
        user_invocable=skill.invocation.user_invocable,
        model_invocable=skill.invocation.model_invocable,
        markdown_body=skill.markdown_body,
    )


def _tool_schema(tool) -> OpenClawToolSchema:
    return OpenClawToolSchema(
        function={
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.params_schema or {"type": "object", "properties": {}},
        }
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def render_bootstrap(
    node: Node,
    current_user: User,
    descendants: list[Node] | None = None,
) -> OpenClawBootstrap:
    """Render a Node's container as an OpenClaw-compatible bootstrap payload.

    Args:
        node: The database Node whose container is rendered (workspace root).
        current_user: The authenticated user (used to populate session_context).
        descendants: Optional BFS-ordered list of child nodes.  Skills and tool
            schemas from each descendant are merged in order; later entries
            (leaves) override earlier ones (root) so the most-specific
            definition wins.

    Returns:
        An ``OpenClawBootstrap`` instance ready to be serialised as JSON.
    """
    container = NodeContainer.model_validate(node.container)

    # --- Context fields → bootstrap markdown files (root node only) ---
    agents_md = "\n\n".join(container.instructions)
    soul_md = "\n\n".join(container.rules)
    tools_md = "\n\n".join(container.knowledge)

    # --- Build skill + tool maps from root (inserted first, lower priority) ---
    skill_map: dict[str, OpenClawSkillEntry] = {
        skill.name: _skill_entry(skill) for skill in container.skills
    }
    tool_schema_map: dict[str, OpenClawToolSchema] = {
        tool.name: _tool_schema(tool) for tool in container.tools
    }

    # --- Merge descendants: leaf entries override root (more-specific wins) ---
    if descendants:
        for desc_node in descendants:
            desc_container = NodeContainer.model_validate(desc_node.container)
            for skill in desc_container.skills:
                skill_map[skill.name] = _skill_entry(skill)
            for tool in desc_container.tools:
                tool_schema_map[tool.name] = _tool_schema(tool)

    return OpenClawBootstrap(
        node_id=str(node.id),
        node_path=node.path,
        kind=container.kind.value,
        agents_md=agents_md,
        soul_md=soul_md,
        tools_md=tools_md,
        skills=list(skill_map.values()),
        tool_schemas=list(tool_schema_map.values()),
        execute_workflow_schema=_EXECUTE_WORKFLOW_SCHEMA,
        execute_tool_schema=_EXECUTE_TOOL_SCHEMA,
        session_context={
            "app_id": str(node.application_id),
            "node_path": node.path,
            "species": container.species.value if container.species else None,
            "user_role": current_user.system_role.value,
        },
    )
