# Collider Skills Architecture — SDK/gRPC Mode

> Defining how Collider's recursive NodeContainer model maps to Anthropic's 2026 Agent Skills paradigm, with structured JSON delivery via gRPC.

Version: v1.0.0 — 2026-02-23

---

## 1. The Problem

### 1.1 Why Static SKILL.md Fails for Collider

Anthropic's Agent Skills paradigm (2025a) was designed for **flat filesystems**: a `SKILL.md` file with YAML frontmatter sitting in `.claude/skills/<name>/`. This works for standalone developer tooling where skills are hand-authored markdown documents.

Collider's architecture is fundamentally different:

- **NodeContainers are recursive** — the same DNA type (`NodeContainer`) at all scales. A workspace, a tool, and an application are structurally identical.
- **Context is composed from graphs** — an agent's skills come from merging N nodes in a tree with leaf-wins precedence, not from scanning a directory.
- **Skills are dynamic** — SSE deltas can add/remove skills mid-session without restart.
- **Tools ARE workflows ARE applications** — they're the same pattern at different graph depths.

A static `.agent/skills/*.md` file can't express:

- Where a skill came from in the graph (which node? inherited or local?)
- What other skills it depends on
- What dataflow it participates in (inputs, outputs)
- How it relates to the tools and workflows registered at the same node

### 1.2 SkillsBench Design Constraints

The SkillsBench benchmark (arXiv:2602.12670, Feb 2026) tested 7 agent-model
configurations across 7,308 trajectories. Key findings that constrain our
design:

| Finding                                             | Implication for Collider                                                                                                              |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| 2-3 focused skills = +18.6pp improvement            | Don't flood the system prompt with every container's skills. Compose 2-3 focused views.                                               |
| 4+ skills = only +5.9pp                             | Diminishing returns. More context != better.                                                                                          |
| Comprehensive skills hurt (-2.9pp)                  | Compact, procedural skills outperform exhaustive docs. Keep skills narrow and actionable.                                             |
| Self-generated skills = -1.3pp                      | Agents can't author the procedural knowledge they benefit from consuming. Skills must be curated.                                     |
| Curated skills = +16.2pp average                    | Human-authored procedural guidance for specialized workflows is the highest-value augmentation.                                       |
| Domains with poor pretraining coverage benefit most | Healthcare +51.9pp, Manufacturing +41.9pp vs Software Engineering +4.5pp. Collider's custom domain workflows will benefit enormously. |

### 1.3 The Opportunity

Collider's `NodeContainer` already carries everything a skill needs: `instructions`, `rules`, `knowledge`, `skills[]`, `tools[]`, `workflows[]`. A skill isn't a separate artifact — it's a **computed view** of a container subtree that tells the agent:

1. What this workspace **IS** (identity, position in graph)
2. What it **CAN DO** (available tools, workflows, skills)
3. How to **NAVIGATE** (parent, children, related nodes)
4. What it should **PRODUCE** (outputs, deliverables)

---

## 2. Three-Layer Skill Model

```text
Layer 3: INTERFACE        What the agent sees
          │                (system prompt sections / SDK SkillDefinition JSON)
          │ computed at session time by prompt-builder.ts
          │
Layer 2: CONTAINER        What the graph holds
          │                (NodeContainer.skills[] + .tools[] + .workflows[])
          │ composed by AgentRunner.compose_context_set()
          │
Layer 1: GRAPH            How containers relate
                           (Node tree with ancestors, children, leaf-wins merge)
                           Navigated via DataServer REST + gRPC
```

### Layer 1 — Graph (exists, unchanged)

The node tree in the DB. Each node has a `parent_id`, `path`, and `container` JSON field holding a `NodeContainer`. Navigation:

```text
GET :8000/api/v1/apps/{id}/nodes/{node_id}/ancestors   → root-first chain
GET :8000/api/v1/apps/{id}/nodes/{node_id}/children     → direct children
GET :8000/api/v1/agent/bootstrap/{node_id}?depth=N      → full subtree context
```

The graph IS the skill topology. A skill's scope, inheritance, and composition
all derive from the node's position in the tree.

### Layer 2 — Container (enhance with graph-aware metadata)

Each `NodeContainer` carries skills as structured `SkillDefinition` objects. Currently:

```python
# Current model (ColliderDataServer/src/schemas/nodes.py)
class SkillDefinition(BaseModel):
    name: str
    description: str = ""
    emoji: str = ""
    tool_ref: str | None = None
    requires_bins: list[str] = []
    requires_env: list[str] = []
    invocation: SkillInvocationPolicy = SkillInvocationPolicy()
    markdown_body: str = ""
```

This is a flat, node-local skill. It doesn't know where it came from, what it
depends on, or what outputs it produces. See Section 3 for the proposed
enhancement.

### Layer 3 — Interface (computed, never stored)

What the agent receives in its system prompt. Currently `prompt-builder.ts` renders skills as flat markdown:

```markdown
# Available Skills

## collider-graph

**Application -> Workflow -> Tool — the Collider execution pattern**
...
```

This should become **structured workspace state** — see Section 7.

---

## 3. Data Model — Enhanced SkillDefinition

### 3.1 New Enums

```python
class SkillKind(str, Enum):
    """Declares what role a skill plays in the container."""

    PROCEDURAL = "procedural"   # How-to guidance (the standard skill type)
    NAVIGATION = "navigation"   # How to discover/traverse the container graph
    WORKFLOW = "workflow"        # Wraps a WorkflowDefinition as an agent skill
    COMPOSITE = "composite"     # Auto-composed from child container skills

class SkillScope(str, Enum):
    """Computed at composition time — where did this skill come from?"""

    LOCAL = "local"             # Defined on this exact node
    INHERITED = "inherited"     # Propagated from an ancestor node
    COMPOSED = "composed"       # Merged from a ContextSet with multiple nodes
    GLOBAL = "global"           # Available everywhere (root-level skills)
```

### 3.2 Enhanced SkillDefinition

Backward-compatible additions to the existing model:

```python
class SkillDefinition(BaseModel):
    """An agent-compatible skill entry backed by a Collider NodeContainer.

    Maps to the agent SKILL.md format for CLI mode, and to structured
    JSON SkillChunk for SDK/gRPC mode.
    """

    # --- Existing fields (unchanged) ---
    name: str
    description: str = ""
    emoji: str = ""
    tool_ref: str | None = None
    requires_bins: list[str] = []
    requires_env: list[str] = []
    invocation: SkillInvocationPolicy = SkillInvocationPolicy()
    markdown_body: str = ""

    # --- NEW: Graph-aware metadata ---
    kind: SkillKind = SkillKind.PROCEDURAL
    scope: SkillScope = SkillScope.LOCAL      # Set at composition time

    # Origin tracking (set by compose_context_set)
    source_node_path: str | None = None       # "factory/ffs2/agent-runner"
    source_node_id: str | None = None         # UUID of the originating node

    # Dataflow declarations (what this skill expects and produces)
    inputs: list[str] = []                    # Semantic tags: ["ContextSet", "node_ids"]
    outputs: list[str] = []                   # Semantic tags: ["BootstrapResponse", "system_prompt"]

    # Graph references (for navigation and composition)
    depends_on: list[str] = []                # Other skill names this requires
    exposes_tools: list[str] = []             # Tool names available via this skill
    child_skills: list[str] = []              # Skills from child nodes (for composite)
```

### 3.3 ContainerSkillView (computed at session time)

A new schema in `ColliderAgentRunner` that represents the **agent's view** of a skill after composition. Not stored in DB — generated by `compose_context_set()`.

```python
class ContainerSkillView(BaseModel):
    """The computed skill view the agent receives. Generated from the
    composed container graph, not stored anywhere."""

    # Core identity
    name: str
    description: str
    kind: SkillKind
    scope: SkillScope
    emoji: str = ""

    # Procedural content (the "how-to")
    instructions: str = ""                    # From markdown_body or composed

    # Available actions (resolved from the container's tools/workflows)
    available_tools: list[ToolSummary] = []
    available_workflows: list[WorkflowSummary] = []

    # Graph context (so the agent knows where it is)
    source_node_path: str | None = None
    ancestor_paths: list[str] = []            # Root-first
    child_paths: list[str] = []

    # Dataflow
    inputs: list[str] = []
    outputs: list[str] = []
    depends_on: list[str] = []

    # Anthropic compatibility metadata
    user_invocable: bool = True
    model_invocable: bool = True
    tool_ref: str | None = None

class ToolSummary(BaseModel):
    name: str
    description: str = ""
    code_ref: str = ""
    visibility: str = "local"

class WorkflowSummary(BaseModel):
    name: str
    steps: list[str] = []
    description: str = ""
```

### 3.4 TypeScript Interface (SDK types.ts)

```typescript
/** Enhanced skill definition with graph-aware metadata. */
export interface SkillDefinition {
  // --- Existing fields ---
  name: string;
  description: string;
  emoji?: string;
  requires_bins?: string[];
  requires_env?: string[];
  user_invocable: boolean;
  model_invocable: boolean;
  markdown_body: string;
  tool_ref?: string;
  invocation_policy?: "auto" | "confirm" | "disabled";

  // --- NEW: Graph-aware fields ---
  kind?: "procedural" | "navigation" | "workflow" | "composite";
  scope?: "local" | "inherited" | "composed" | "global";
  source_node_path?: string;
  source_node_id?: string;
  inputs?: string[];
  outputs?: string[];
  depends_on?: string[];
  exposes_tools?: string[];
  child_skills?: string[];
}
```

### 3.5 Proto Extension (SkillChunk)

```protobuf
message SkillChunk {
  // Existing fields (unchanged)
  string name = 1;
  string description = 2;
  string emoji = 3;
  string markdown_body = 4;
  string tool_ref = 5;
  bool user_invocable = 6;
  bool model_invocable = 7;
  string invocation_policy = 8;
  repeated string requires_bins = 9;
  repeated string requires_env = 10;

  // NEW: Graph-aware fields
  string kind = 20;                    // "procedural" | "navigation" | etc.
  string scope = 21;                   // "local" | "inherited" | etc.
  string source_node_path = 22;
  string source_node_id = 23;
  repeated string inputs = 24;
  repeated string outputs = 25;
  repeated string depends_on = 26;
  repeated string exposes_tools = 27;
  repeated string child_skills = 28;
}
```

Field numbers start at 20 to leave room for future existing-field additions. All
new fields are optional (proto3 default behavior).

---

## 4. The collider-workspace Meta-Skill

### 4.1 Design Rationale

Every Collider agent needs to understand the recursive container model to be
effective. Instead of documenting this in lengthy system prompts, we create ONE
global navigation skill that:

- Teaches the `NodeContainer` pattern (same DNA at all scales)
- Provides the bootstrap, discovery, and execution APIs
- Explains the Application -> Workflow -> Tool hierarchy
- Describes the leaf-wins merge strategy

This follows SkillsBench best practice: **one focused, procedural skill** that closes the domain knowledge gap. It's `kind: navigation`, `scope: global`, and auto-inherited by all sessions.

### 4.2 Content Structure

```text
FFS0_Factory/.agent/skills/collider-workspace/
├── SKILL.md           # Core navigation instructions (~200 lines)
└── api-reference.md   # Supporting file with endpoint details
```

**SKILL.md frontmatter:**

```yaml
---
name: collider-workspace
description: >
  Navigate and operate within Collider's recursive workspace container model.
  Use when working with nodes, tools, workflows, or composing agent contexts.
kind: navigation
scope: global
user_invocable: false
model_invocable: true
exposes_tools:
  - bootstrap_context
  - discover_tools
  - execute_workflow
  - execute_tool
---
```

**SKILL.md body** (procedural, not comprehensive):

1. **The Pattern**: NodeContainer is the same type at all scales. `kind` field discriminates: `workspace` (context), `tool` (execution), `workflow` (orchestration).

2. **Bootstrap**: `GET :8000/api/v1/agent/bootstrap/{node_id}?depth=N` returns `AgentBootstrap` with all context fields. Leaf-wins: later node_ids in a ContextSet override earlier ones for skills and tools.

3. **Discovery**: `POST :8001/api/v1/registry/tools/discover` with `{ query, visibility_filter }`. Semantic search via ChromaDB.

4. **Execution**: MCP SSE at `http://localhost:8001/mcp/sse` (preferred) or REST `POST :8000/api/v1/execution/tool/{name}`.

5. **Navigation**: Ancestor chain = `GET .../ancestors`. Children = `GET .../children`. Full tree = bootstrap with `depth=-1`.

### 4.3 Relationship to Existing collider-graph.md

The current `.agent/skills/collider-graph.md` contains similar content but as a flat markdown skill in the old format. It should be **migrated into** the `collider-workspace/SKILL.md` structure, with `collider-graph.md` becoming a reference in the supporting files or deprecated.

---

## 5. Skill Resolution & Composition

### 5.1 Resolution Chain

Skills are resolved through the container graph, not from a filesystem scan:

```text
Priority (leaf wins):

1. Session-injected skills    (SSE delta → ContextDelta.skill)
   ↑ highest — runtime injection
2. Node-local skills          (NodeContainer.skills[] on selected nodes)
   ↑ from ContextSet.node_ids
3. Ancestor-inherited skills  (if ContextSet.inherit_ancestors = true)
   ↑ walked root-first, child overrides parent
4. Root-global skills         (FFS0 root node's container.skills[])
   ↑ lowest — always present
```

The `compose_context_set()` function in `ColliderAgentRunner/src/agent/runner.py` already implements this merge. The enhancement: **stamp each resulting skill with `scope` and `source_node_path`** so the agent knows provenance.

### 5.2 Why Skills Are NOT Stored Per-Workspace

In the current `.agent/skills/` filesystem approach, skills are static files discovered by the seeder (`sdk/seeder/agent_walker.py`). This creates several problems:

- **Duplication**: The same skill repeated in multiple workspace `.agent/` directories
- **Staleness**: Filesystem skills diverge from the DB container skills
- **No composition**: Two nodes can't merge their skills at query time

In the SDK/gRPC model, skills live in `NodeContainer.skills[]` in the DB. The `.agent/skills/` filesystem is only a **seeding source** — the seeder reads them once and writes them into the container. After that, the DB is the source of truth.

**Exception**: The `collider-workspace` global skill should exist as a filesystem SKILL.md (for CLI mode compatibility) AND as a root container skill (for SDK mode). The seeder ensures parity.

### 5.3 ContextSet Composition Flow

```text
Chrome Extension selects nodes [A, B, C]
    ↓
POST :8004/agent/session { node_ids: [A, B, C], inherit_ancestors: true }
    ↓
AgentRunner.compose_context_set():
    1. Fetch ancestors of A, B, C (root-first)
    2. Fetch bootstrap for each node (with descendants)
    3. Merge: instructions concatenated, skills leaf-wins by name
    4. For each resulting skill:
       - Set scope = "inherited" if from ancestor, "local" if from selected node
       - Set source_node_path from the originating node
       - Resolve exposes_tools against the merged tool_schemas
    5. Return ComposedContext with ContainerSkillView[]
    ↓
gRPC GetBootstrap → BootstrapResponse with enhanced SkillChunks
    ↓
NanoClawBridge prompt-builder.ts → structured workspace state in system prompt
```

---

## 6. SDK Mode Pipeline

### 6.1 gRPC Delivery (GetBootstrap)

The `ColliderContext.GetBootstrap` RPC returns a `BootstrapResponse` containing `repeated SkillChunk skills`. With the enhanced proto (Section 3.5), each SkillChunk now carries graph-aware fields.

The `context_service.py` `_skill_to_chunk()` function maps:

```python
def _skill_to_chunk(skill: ContainerSkillView) -> SkillChunk:
    return SkillChunk(
        name=skill.name,
        description=skill.description,
        emoji=skill.emoji,
        markdown_body=skill.instructions,
        tool_ref=skill.tool_ref or "",
        user_invocable=skill.user_invocable,
        model_invocable=skill.model_invocable,
        # NEW graph-aware fields
        kind=skill.kind.value,
        scope=skill.scope.value,
        source_node_path=skill.source_node_path or "",
        source_node_id=skill.source_node_id or "",
        inputs=skill.inputs,
        outputs=skill.outputs,
        depends_on=skill.depends_on,
        exposes_tools=[t.name for t in skill.available_tools],
        child_skills=skill.child_skills,
    )
```

### 6.2 Streaming Context (StreamContext)

For large context sets, `StreamContext` delivers skills as individual `ContextChunk` messages. Each chunk is self-contained — the client can build the skill list incrementally.

### 6.3 Mid-Session Injection (SSE Deltas)

The `ContextSubscriber` in NanoClawBridge watches for SSE events at `:8000/api/v1/context/stream/{sessionId}`. When a node's skills change:

```text
SSE event: { type: "skill_changed", node_id: "...", skill: { ...SkillDefinition } }
    ↓
ContextSubscriber parses → ContextDelta { type: "skill", operation: "update", skill }
    ↓
applyDeltaToContext() mutates ComposedContext.skills[]
    ↓
buildSystemPrompt() regenerates system prompt
    ↓
Next agent turn uses updated skill context (no restart)
```

### 6.4 Token Budget Strategy

Per SkillsBench: compact > comprehensive. The system prompt rendering should
apply a token budget:

1. **Always include**: `collider-workspace` navigation skill (global, ~200 lines)
2. **Include 1-2**: Domain-specific skills from the composed context (highest relevance)
3. **Summarize**: Additional skills as name + description only (not full markdown_body)
4. **Exclude**: Skills with `model_invocable: false`

Total skill budget target: **~2000 tokens** (approximately 2% of a 100K context
window, matching Claude Code's default skill budget).

---

## 7. System Prompt Rendering — Structured Workspace State

### 7.1 Current Format (flat)

```markdown
# Available Skills

## collider-graph
**Application -> Workflow -> Tool — the Collider execution pattern**
...

---

# Session Context
- **Role**: superadmin
- **Application**: c57ab23a-...
- **Composed nodes**: factory/ffs2, factory/ffs2/agent-runner
```

### 7.2 Proposed Format (structured, graph-aware)

```markdown
# Workspace Context

## Position in Graph
- **Node**: factory/ffs2/agent-runner
- **Ancestors**: factory → factory/ffs1 → factory/ffs2
- **Children**: (none — leaf node)
- **Kind**: workspace
- **Depth**: 3

## Available Skills

### collider-workspace [navigation | global]
Navigate and operate within Collider's recursive workspace container model.
- Exposes: `bootstrap_context`, `discover_tools`, `execute_workflow`, `execute_tool`
- Source: factory (root)

### grpc-context-delivery [procedural | local]
gRPC context streaming pipeline for agent sessions.
- Inputs: ContextSet, node_ids, role
- Outputs: BootstrapResponse, ContextChunk stream
- Depends on: collider-workspace
- Exposes: `stream_context`, `get_bootstrap`
- Source: factory/ffs2/agent-runner

## Available Tools (5)
| Tool             | Description                             | Visibility |
| ---------------- | --------------------------------------- | ---------- |
| stream_context   | Stream composed context as typed chunks | local      |
| get_bootstrap    | One-shot full context retrieval         | local      |
| discover_tools   | Semantic tool search via ChromaDB       | group      |
| execute_tool     | Execute a registered tool by name       | global     |
| execute_workflow | Execute a workflow subgraph             | global     |

## Session
- **Role**: superadmin
- **User**: Sam
- **Application**: c57ab23a-... (App 2XZ)
- **Composed from**: factory/ffs2, factory/ffs2/agent-runner
```

### 7.3 Why This Format

1. **Spatial awareness**: The agent knows where it is in the graph (depth 3, ancestors listed, no children)
2. **Skill provenance**: Each skill shows `[kind | scope]` and its source node — the agent knows what's inherited vs local
3. **Dataflow visibility**: Inputs/outputs/dependencies declared per skill — the agent can reason about data flow
4. **Tool inventory**: Flat table of available tools with visibility — the agent can plan which tools to use
5. **Compact**: Follows SkillsBench "detailed but compact" principle — structured metadata, not prose

### 7.4 Implementation in prompt-builder.ts

The `formatSkills()` function changes from flat markdown rendering to the structured format above. The key change:

```typescript
function formatWorkspaceContext(context: ComposedContext): string {
  const sections: string[] = [];

  // 1. Position in Graph
  sections.push(formatGraphPosition(context.session_meta));

  // 2. Available Skills (with graph metadata)
  sections.push(formatSkillsStructured(context.skills));

  // 3. Available Tools (table format)
  sections.push(formatToolTable(context.tool_schemas));

  // 4. Session metadata
  sections.push(formatSession(context.session_meta));

  return `# Workspace Context\n\n${sections.join("\n\n")}`;
}
```

---

## 8. Agent Teams Skill Composition

### 8.1 Leader vs Member Skills

The `TeamManager` in `NanoClawBridge/src/sdk/team-manager.ts` creates teams with a leader and N members. Skill composition differs:

**Leader (merged context)**:

- Receives ALL composed skills from the full ContextSet
- Plus: auto-injected `team-coordinator` skill (how to delegate, use mailbox, track member status)
- `scope` for each skill reflects the full composition

**Members (isolated context)**:

- Receive ONLY skills from their assigned node(s)
- Plus: `collider-workspace` global skill (so they can navigate if needed)
- `scope` is always `local` (their view is their node only)

### 8.2 team-coordinator Auto-Skill

Injected into the leader's context when `createTeam()` is called:

```typescript
const teamCoordinatorSkill: SkillDefinition = {
  name: "team-coordinator",
  description: "Coordinate multi-agent team with isolated workspace members",
  kind: "navigation",
  scope: "composed",
  model_invocable: true,
  user_invocable: false,
  markdown_body: `
## Team Structure
- Leader: ${leaderId} (you) — merged context from all nodes
- Members: ${members.map(m => `${m.id} → ${m.nodePath}`).join(", ")}

## Delegation
Use mailbox to delegate tasks to members by their workspace focus:
${members.map(m => `- ${m.id}: specialized in ${m.nodePath}`).join("\n")}

## Communication
- sendTask(memberId, message): Assign work to a member
- broadcast(message): Send to all members
- Members report results back via mailbox

## Coordination Rules
- Each member sees ONLY their node's skills and tools
- The leader (you) sees ALL composed skills
- Delegate domain-specific work to the member whose node owns it
  `,
  exposes_tools: ["sendTask", "broadcast"],
  inputs: ["task_description", "member_id"],
  outputs: ["member_result"],
};
```

### 8.3 Skill-Aware Task Routing

When the leader delegates a task, it should consider skill coverage:

```text
Leader knows: Member A has skills [grpc-context, proto-validation]
              Member B has skills [api-conventions, rest-endpoints]

Task: "Fix the gRPC context delivery bug"
→ Route to Member A (their node's skills match the domain)

Task: "Add a new REST endpoint"
→ Route to Member B (their node's skills match)
```

The `exposes_tools` field on each member's skills enables this reasoning.

---

## 9. Mapping to Anthropic's 2026 Skill System

### 9.1 Concept Mapping

| Anthropic Concept                   | Collider Equivalent                                    | Notes                                              |
| ----------------------------------- | ------------------------------------------------------ | -------------------------------------------------- |
| `SKILL.md` file                     | `ContainerSkillView` rendered as system prompt section | In SDK mode, never a file — always structured JSON |
| Skill directory (`skills/<name>/`)  | NodeContainer subtree                                  | Children = supporting context                      |
| `description` frontmatter           | `SkillDefinition.description`                          | Used for auto-invocation matching                  |
| `allowed-tools` frontmatter         | `ContainerSkillView.available_tools`                   | Resolved from node's tool_schemas                  |
| `context: fork`                     | Team member with isolated node context                 | Each node CAN be a forked subagent                 |
| `disable-model-invocation`          | `SkillInvocationPolicy.model_invocable = false`        | Already implemented                                |
| `user-invocable: false`             | `SkillInvocationPolicy.user_invocable = false`         | Already implemented                                |
| `$ARGUMENTS` substitution           | ContextSet parameters (node_ids, role, etc.)           | Dynamic at session creation                        |
| Dynamic context (`!`cmd``)          | SSE context deltas / gRPC streaming                    | Real-time, not pre-execution                       |
| Sub-agent `skills` preload          | gRPC `GetBootstrap` with specific node_ids             | Same mechanism, different entry point              |
| Skill in `/` menu                   | Chrome Extension WorkspaceBrowser node selection       | Node = skill scope selector                        |
| `agent` frontmatter (subagent type) | `NodeKind` (workspace/tool/workflow)                   | Semantic role matching                             |
| Persistent memory (`memory` field)  | Node container persistence in DB                       | Skills persist across sessions via DB              |

### 9.2 CLI Mode Compatibility

For `USE_SDK_AGENT=false`, `workspace_writer.py` generates SKILL.md files from `ContainerSkillView`:

```python
def _write_skill_md(view: ContainerSkillView, path: Path) -> None:
    frontmatter = {
        "name": view.name,
        "description": view.description,
        # Map graph-aware fields to closest Anthropic equivalents
        "disable-model-invocation": not view.model_invocable,
        "user-invocable": view.user_invocable,
    }
    if view.available_tools:
        frontmatter["allowed-tools"] = ", ".join(t.name for t in view.available_tools)

    content = f"---\n{yaml.dump(frontmatter)}---\n\n{view.instructions}"
    (path / f"{view.name}.SKILL.md").write_text(content)
```

This maintains backward compatibility while the SDK mode is the primary path.

### 9.3 Agent Skills Open Standard Alignment

Collider's enhanced SkillDefinition is a **superset** of the Agent Skills standard (agentskills.io). The graph-aware fields (`kind`, `scope`, `source_node_path`, `inputs`, `outputs`, `depends_on`, `exposes_tools`) are Collider-specific extensions that don't break standard compliance. Any skill can be exported as a standard-compliant SKILL.md by omitting the extension fields.

---

## 10. Implementation Roadmap

### Phase 1: Data Models

**Effort**: 1-2 days

| File                                                | Change                                                                                                                |
| --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `ColliderDataServer/src/schemas/nodes.py`           | Add `SkillKind`, `SkillScope` enums. Add graph-aware fields to `SkillDefinition` (all optional, backward compatible). |
| `ColliderDataServer/src/schemas/agent_bootstrap.py` | Update `AgentSkillEntry` to include new fields.                                                                       |
| `ColliderDataServer/src/core/agent_bootstrap.py`    | Update `render_bootstrap()` to populate `source_node_path`, `scope`, and `exposes_tools` from the node context.       |
| `ColliderAgentRunner/src/schemas/skill_view.py`     | **NEW** — `ContainerSkillView`, `ToolSummary`, `WorkflowSummary`.                                                     |

### Phase 2: Composition Pipeline

**Effort**: 2-3 days

| File                                              | Change                                                                                                  |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `ColliderAgentRunner/src/agent/runner.py`         | Update `compose_context_set()` to build `ContainerSkillView[]` with scope tracking and tool resolution. |
| `proto/collider_graph.proto`                      | Extend `SkillChunk` with fields 20-28 (graph-aware).                                                    |
| `ColliderAgentRunner/src/grpc/context_service.py` | Update `_skill_to_chunk()` to serialize new fields.                                                     |

### Phase 3: Meta-Skill

**Effort**: 0.5 days

| File                                        | Change                                                            |
| ------------------------------------------- | ----------------------------------------------------------------- |
| `.agent/skills/collider-workspace/SKILL.md` | **NEW** — The global navigation meta-skill.                       |
| `.agent/skills/collider-graph.md`           | Deprecate or redirect to collider-workspace.                      |
| `sdk/seeder/agent_walker.py`                | Support subdirectory skill format (`skills/<name>/SKILL.md`).     |
| `sdk/seeder/node_upserter.py`               | Populate `kind`, `scope` when building container from filesystem. |

### Phase 4: Prompt Builder

**Effort**: 1-2 days

| File                                        | Change                                                                                       |
| ------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `NanoClawBridge/src/sdk/types.ts`           | Add graph-aware fields to `SkillDefinition` interface.                                       |
| `NanoClawBridge/src/sdk/prompt-builder.ts`  | Replace `formatSkills()` with `formatWorkspaceContext()` — structured graph-aware rendering. |
| `NanoClawBridge/src/grpc/context-client.ts` | Parse new SkillChunk fields in proto → SkillDefinition mapping.                              |

### Phase 5: Agent Teams

**Effort**: 1-2 days

| File                                     | Change                                                                               |
| ---------------------------------------- | ------------------------------------------------------------------------------------ |
| `NanoClawBridge/src/sdk/team-manager.ts` | Inject `team-coordinator` auto-skill for leaders. Filter skills by node for members. |

### Total estimated effort: 5-9 days

---

## Appendix A: Decision Log

### Q: Should every workspace have its own skill files?

**A: No.** Skills are computed from the container graph at session time. The `.agent/skills/` directory is a seeding source only. The DB container is the source of truth.

### Q: One big skill or many small ones?

**A: 2-3 focused skills per session.** Per SkillsBench, this is the sweet spot. The `collider-workspace` meta-skill teaches navigation. 1-2 domain skills come from the composed context. Additional skills are summarized (name + description only) to stay within token budget.

### Q: Static SKILL.md or dynamic JSON?

**A: Dynamic JSON via gRPC (SDK mode primary).** SKILL.md generation via workspace_writer is maintained for CLI mode backward compatibility. The container graph in the DB is always the source of truth.

### Q: Where does the agent get "state"?

**A: The system prompt IS the state.** `prompt-builder.ts` renders the composed `ContainerSkillView[]` into structured workspace state. Mid-session updates come via SSE deltas. The agent reads its own system prompt, which is the graph rendered as structured text.

### Q: How does this relate to Anthropic's sub-agents?

**A: Each NodeContainer can be a sub-agent scope.** Setting `context: fork` (or creating a team member) for a specific node gives an isolated agent that sees only that node's skills and tools. The `collider-workspace` global skill ensures even isolated agents can navigate the broader graph if needed.

---

_Architecture document for the Collider ecosystem. References: SkillsBench
(2602.12670v1), Claude Code Skills docs (code.claude.com), Anthropic Agent
Skills specification (agentskills.io)._
