from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, model_validator

from src.db.models import AppRole


# ---------------------------------------------------------------------------
# Container classification & boundary types
# ---------------------------------------------------------------------------


class ContainerSpecies(str, Enum):
    """Human-readable template classification for workspace visualization.

    NOT an access control gate — helps users see what kind of context a
    node carries.  For AI, it's all just typed JSON/protobuf.
    """

    OFFICE = "office"  # Doc / productivity context
    SETTINGS = "settings"  # Configuration / admin context
    IDE = "ide"  # Code context (synced to local FS)
    CLOUD = "cloud"  # Cloud-only API context
    CUSTOM = "custom"  # User-defined


class ApiBoundary(BaseModel):
    """Per-node protocol permissions.

    The app creator controls which protocols each node is allowed to use.
    Species can provide DEFAULTS, but the node owner overrides.
    """

    rest: bool = True
    sse: bool = True
    websocket: bool = False
    webrtc: bool = False
    native_messaging: bool = False
    grpc: bool = False


# ---------------------------------------------------------------------------
# Node kind — semantic role discriminator
# ---------------------------------------------------------------------------


class NodeKind(str, Enum):
    """Declares the semantic role of a NodeContainer.

    Workspace — provides context, rules, knowledge, and child nodes.
    Tool      — leaf unit; exposes ToolDefinition(s) for direct execution.
    Workflow  — orchestration unit; sequences tool calls via WorkflowDefinition(s).
    """

    WORKSPACE = "workspace"
    TOOL = "tool"
    WORKFLOW = "workflow"


# ---------------------------------------------------------------------------
# Skill definitions — Agent Skills interface layer
# ---------------------------------------------------------------------------


class SkillInvocationPolicy(BaseModel):
    """Controls who can invoke this skill."""

    user_invocable: bool = True
    model_invocable: bool = True


class SkillKind(str, Enum):
    """Classification of a skill's execution mechanism."""

    PRIMITIVE = "primitive"
    COMPOSITE = "composite"
    META = "meta"


class SkillScope(str, Enum):
    """Visibility and applicability of the skill."""

    NODE = "node"
    APP = "app"
    GLOBAL = "global"


class SkillDefinition(BaseModel):
    """An agent-compatible skill entry backed by a Collider ToolDefinition.

    Maps to the agent ``SkillEntry`` / SKILL.md frontmatter format.
    When the bootstrap endpoint is called, each SkillDefinition is rendered
    into a SKILL.md-compatible entry that the agent runtime injects into the
    system prompt.
    """

    name: str
    description: str = ""
    emoji: str = ""
    
    # --- Graph-Aware Metadata ---
    kind: SkillKind = SkillKind.PRIMITIVE
    scope: SkillScope = SkillScope.NODE
    source_node_path: str | None = None
    inputs: list[dict] = []
    outputs: list[dict] = []
    depends_on: list[str] = []
    child_skills: list[str] = []

    # --- Execution Context ---
    tool_ref: str | None = None  # References ToolDefinition.name in same container
    requires_bins: list[str] = []  # CLI binaries needed, e.g. ["gh", "curl"]
    requires_env: list[str] = []  # Env vars needed, e.g. ["GITHUB_TOKEN"]
    invocation: SkillInvocationPolicy = SkillInvocationPolicy()
    markdown_body: str = ""  # Usage docs: when to use, examples, avoid


# ---------------------------------------------------------------------------
# Typed tool & workflow definitions inside a container
# ---------------------------------------------------------------------------


class ToolDefinition(BaseModel):
    """A typed tool contract living inside a NodeContainer.

    When registered on the GraphToolServer, ``params_schema`` is used by
    ``pydantic.create_model()`` to build a dynamic args model, and the
    tool becomes a Pydantic Graph Beta step discoverable to all agents.
    """

    name: str
    description: str = ""
    params_schema: dict = {}  # JSON Schema (from create_model)
    code_ref: str = ""  # Module path or script reference
    visibility: Literal["local", "group", "global"] = "local"


class WorkflowStep(BaseModel):
    """One step in a workflow sequence."""

    tool_name: str  # References a ToolDefinition.name
    condition: str | None = None  # Edge condition expression
    inputs_map: dict = {}  # Maps step inputs from prior outputs


class WorkflowDefinition(BaseModel):
    """A workflow = ordered tool calls with conditions.

    Translatable to Pydantic Graph Beta nodes on the GraphToolServer.
    """

    name: str
    description: str = ""
    steps: list[WorkflowStep] = []
    entry_step: str | None = None  # First step name


# ---------------------------------------------------------------------------
# NodeContainer — the single recursive DNA type
# ---------------------------------------------------------------------------


class NodeContainer(BaseModel):
    """The recursive DNA unit.  Same type at all scales.

    ``kind`` declares the semantic role so agents can reason about scope:
    - ``workspace`` — provides context (instructions, rules, knowledge) and may
      have child nodes.  The default.
    - ``tool`` — leaf unit exposing one or more ToolDefinitions for execution.
    - ``workflow`` — orchestration unit sequencing tool calls.

    ``skills`` replaces the former ``list[str]`` stub with properly typed
    SkillDefinition entries that map 1-to-1 onto SKILL.md format,
    enabling the agent bootstrap endpoint to render the container as an
    agent workspace with full skill injection.
    """

    version: str = "1.0.0"
    kind: NodeKind = NodeKind.WORKSPACE  # semantic role discriminator
    species: ContainerSpecies | None = None
    api_boundary: ApiBoundary = ApiBoundary()

    # Context (the .agent structure)
    manifest: dict = {}
    instructions: list[str] = []
    rules: list[str] = []
    knowledge: list[str] = []
    configs: dict = {}

    # Skills interface — Agent-compatible (was list[str], now typed)
    skills: list[SkillDefinition] = []

    # Executable definitions
    tools: list[ToolDefinition] = []
    workflows: list[WorkflowDefinition] = []

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_skills(cls, values: Any) -> Any:
        """Convert legacy ``skills: list[str]`` to ``list[SkillDefinition]``.

        Nodes seeded before the typed skill model was introduced stored plain
        strings (e.g. filenames from .agent/skills/).  This validator converts
        them so old data keeps deserializing cleanly.
        """
        skills = values.get("skills", [])
        if skills and isinstance(skills[0], str):
            values["skills"] = [
                {"name": s.strip(), "description": s.strip()}
                for s in skills
                if isinstance(s, str) and s.strip()
            ]
        return values


class NodeCreate(BaseModel):
    path: str
    parent_id: str | None = None
    container: NodeContainer = NodeContainer()
    metadata: dict = {}


class NodeUpdate(BaseModel):
    path: str | None = None
    container: NodeContainer | None = None
    metadata: dict | None = None


class NodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    application_id: str
    parent_id: str | None
    path: str
    container: dict
    metadata_: dict
    created_at: datetime
    updated_at: datetime


class NodeTreeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    path: str
    container: dict
    metadata_: dict
    children: list[NodeTreeResponse] = []


class PermissionCreate(BaseModel):
    user_id: str
    application_id: str
    role: AppRole = AppRole.APP_USER


class PermissionUpdate(BaseModel):
    role: AppRole | None = None


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    application_id: str
    role: AppRole
    created_at: datetime


class AppAccessRequestCreate(BaseModel):
    """Request access to an application."""

    application_id: str
    message: str | None = None


class AppAccessRequestResponse(BaseModel):
    """Response for access request."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    application_id: str
    message: str | None
    status: str
    requested_at: datetime
    resolved_at: datetime | None
    resolved_by: str | None


class AppAccessRequestApprove(BaseModel):
    """Approve access request with specified role."""

    role: AppRole = AppRole.APP_USER
