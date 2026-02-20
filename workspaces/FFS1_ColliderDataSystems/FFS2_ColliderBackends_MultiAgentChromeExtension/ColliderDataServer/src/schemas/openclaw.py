"""OpenClaw integration schemas.

These types represent the contract between ColliderDataServer and an OpenClaw
agent workspace.  The bootstrap endpoint renders a NodeContainer into these
structures so that OpenClaw can:

1. Hydrate ``AGENTS.md``, ``SOUL.md``, ``TOOLS.md`` from the node's context
   fields (instructions, rules, knowledge).
2. Inject ``skills`` into the agent's system prompt (SKILL.md format).
3. Receive ``tool_schemas`` as OpenAI-compatible function definitions sent
   directly to the model.
4. Call ``execute_workflow`` to trigger Collider workflows from the agent.
"""

from __future__ import annotations

from pydantic import BaseModel


class OpenClawToolSchema(BaseModel):
    """OpenAI-compatible function schema rendered from a ToolDefinition."""

    type: str = "function"
    function: dict  # {name, description, parameters: JSON Schema}


class OpenClawSkillEntry(BaseModel):
    """A SkillDefinition rendered into OpenClaw SKILL.md frontmatter format.

    OpenClaw reads these at session start and injects them into the agent's
    system prompt.  The ``markdown_body`` field provides the human-readable
    usage docs (when to use, examples, commands).
    """

    name: str
    description: str
    emoji: str = ""
    requires_bins: list[str] = []
    requires_env: list[str] = []
    user_invocable: bool = True
    model_invocable: bool = True
    markdown_body: str = ""


class OpenClawBootstrap(BaseModel):
    """Full OpenClaw workspace context rendered from a NodeContainer.

    Maps the NodeContainer fields onto OpenClaw workspace bootstrap files:

    - ``agents_md``    → ``AGENTS.md``   (agent identity / instructions)
    - ``soul_md``      → ``SOUL.md``     (guardrails / tone / rules)
    - ``tools_md``     → ``TOOLS.md``    (knowledge / reference docs)
    - ``skills``       → SKILL.md entries injected into system prompt
    - ``tool_schemas`` → function definitions sent to the model
    - ``execute_workflow_schema`` → callable tool for POST /execution/workflow/{name}
    """

    node_id: str
    node_path: str
    kind: str  # NodeKind value
    agents_md: str  # From container.instructions joined with double newline
    soul_md: str  # From container.rules joined with double newline
    tools_md: str  # From container.knowledge joined with double newline
    skills: list[OpenClawSkillEntry]
    tool_schemas: list[OpenClawToolSchema]
    execute_workflow_schema: dict  # Pre-built schema for the execute_workflow tool
    execute_tool_schema: dict  # Pre-built schema for the execute_tool tool
    session_context: dict  # app_id, node_path, species, user_role
