"""Agent bootstrap schemas.

These types represent the contract between ColliderDataServer and the
NanoClaw agent workspace.  The bootstrap endpoint renders a NodeContainer into
these structures so that Claude Code can:

1. Hydrate ``CLAUDE.md`` from the node's context fields (instructions, rules,
   knowledge).
2. Inject ``skills`` into the agent's workspace (Agent Skills SKILL.md format).
3. Receive ``tool_schemas`` as OpenAI-compatible function definitions.
4. Call ``execute_workflow`` / ``execute_tool`` to trigger Collider operations.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AgentToolSchema(BaseModel):
    """OpenAI-compatible function schema rendered from a ToolDefinition."""

    type: str = "function"
    function: dict  # {name, description, parameters: JSON Schema}


class AgentSkillEntry(BaseModel):
    """A SkillDefinition rendered into Agent Skills SKILL.md frontmatter format.

    Claude Code reads these at session start and injects them into the agent's
    system prompt.  The ``markdown_body`` field provides the human-readable
    usage docs (when to use, examples, commands).
    """

    name: str
    description: str
    emoji: str = ""
    namespace: str | None = None
    version: str | None = None
    kind: str = "procedural"
    scope: str = "local"
    source_node_path: str | None = None
    source_node_id: str | None = None
    requires_bins: list[str] = Field(default_factory=list)
    requires_env: list[str] = Field(default_factory=list)
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    exposes_tools: list[str] = Field(default_factory=list)
    child_skills: list[str] = Field(default_factory=list)
    user_invocable: bool = True
    model_invocable: bool = True
    markdown_body: str = ""


class AgentBootstrap(BaseModel):
    """Full agent workspace context rendered from a NodeContainer.

    Maps the NodeContainer fields onto NanoClaw workspace bootstrap files:

    - ``agents_md``    → agent identity / instructions
    - ``soul_md``      → guardrails / tone / rules
    - ``tools_md``     → knowledge / reference docs
    - ``skills``       → SKILL.md entries in Agent Skills format
    - ``tool_schemas`` → function definitions sent to the model
    - ``execute_workflow_schema`` → callable tool for POST /execution/workflow/{name}
    """

    node_id: str
    node_path: str
    kind: str  # NodeKind value
    agents_md: str  # From container.instructions joined with double newline
    soul_md: str  # From container.rules joined with double newline
    tools_md: str  # From container.knowledge joined with double newline
    skills: list[AgentSkillEntry]
    tool_schemas: list[AgentToolSchema]
    execute_workflow_schema: dict  # Pre-built schema for the execute_workflow tool
    execute_tool_schema: dict  # Pre-built schema for the execute_tool tool
    session_context: dict  # app_id, node_path, species, user_role
