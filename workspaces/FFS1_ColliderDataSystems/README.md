# Collider: Recursive Workspace Context for Agentic Skill Engineering

## Vision

Collider is an **application-agnostic context orchestration platform** built on
a single recursive data structure — the **NodeContainer** — that unifies
workspace context, agent instructions, skills, tools, and workflows into a
graph-addressable, version-controlled system.

The core proposition: **workspaces ARE applications**. The workspace graph is
not documentation about the application — it IS the application's operational
DNA. Every node in the graph is simultaneously:

- A **context unit** that an agent can be instantiated with
- A **skill container** that defines what the agent can do
- A **knowledge store** that captures what the agent knows
- A **workflow anchor** that connects declarative logic to executable tools

This enables **recursive functorial composition**: any subgraph of nodes
composes into a valid agent context, and any composed context can be further
composed with others. The composition is associative and preserves structure — a
formal functor from the workspace category to the agent capability category.

---

## The NodeContainer Model

```text
NodeContainer {
  config:        { domain, emoji, description }
  instructions:  InstructionDefinition[]    # What the agent should do
  rules:         RuleDefinition[]           # Behavioral constraints
  knowledge:     KnowledgeEntry[]           # What the agent knows
  skills:        SkillDefinition[]          # What the agent can do
  tools:         ToolDefinition[]           # Executable capabilities
  workflows:     WorkflowDefinition[]       # Multi-step orchestration
}
```

Every workspace node — from the root factory to a leaf feature folder —
carries a `NodeContainer`. The same structure operates at all scales. A root
node's container defines platform-wide instructions; a feature node's
container defines feature-specific skills. When an agent session is created,
the platform **composes** containers along the ancestry path using a
**leaf-wins merge** strategy: child values override parent values, arrays
concatenate, and the result is a single coherent context.

### Recursive Composition

```text
FFS0_Factory (root container: platform rules, global tools)
  └── FFS1_ColliderDataSystems (inherits root, adds Collider-specific instructions)
       └── FFS2_Backends (inherits FFS1, adds backend tools + skills)
            └── NanoClawBridge (inherits FFS2, adds agent-specific skills)
```

Selecting `NanoClawBridge` composes containers bottom-up: NanoClawBridge's
skills + FFS2's tools + FFS1's instructions + FFS0's rules = one complete
agent context. This is not a flat merge — it's a **functorial map** that
preserves the categorical structure of the workspace graph.

### Why This Matters

Traditional agent frameworks define agent capabilities at the application level.
Skills are global. Context is monolithic. When the codebase grows, the agent
either knows too much (context overflow) or too little (missing capabilities).

Collider solves this by making context **graph-addressable**. You don't give the
agent "all the skills." You give it the skills **at the node it's working on**,
inherited through the workspace hierarchy. The graph IS the scope. Task
decomposition follows the same graph: split a large node into children, and each
child's container becomes a sub-agent's context.

---

## Skill Engineering: The Collider Approach

### The 2026 Thesis

Agent skills are the new programming paradigm. The agent's "main loop" is:
**gather knowledge, produce skills, use skills to gather more knowledge**. A
container with a large skill set is split by the agent itself — decomposing
tasks into sub-containers, each with focused skill sets. The program IS the
skill graph.

### SkillDefinition Structure

```typescript
interface SkillDefinition {
  name: string;                    // Unique identifier
  description: string;             // What this skill does
  emoji: string;                   // Visual identifier
  tool_ref: string;                // MCP tool name this skill wraps
  markdown_body: string;           // Full instruction content
  user_invocable: boolean;         // Can users trigger directly
  model_invocable: boolean;        // Can the agent trigger autonomously
  invocation_policy: "auto" | "confirm" | "disabled";
  requires_bins: string[];         // System dependencies
  requires_env: string[];          // Required env vars
}
```

### Compatibility with Agent Skills Open Standard

The [Agent Skills](https://agentskills.io) open standard defines a `SKILL.md` file format with YAML frontmatter:

```yaml
---
name: skill-name
description: What this skill does
version: 1.0.0
tools:
  - tool_name
authors:
  - Author Name
tags:
  - category
---
# Skill Instructions
Markdown body describing how to use this skill...
```

Collider's `SkillDefinition` is a **strict superset** of this standard:

| Agent Skills Field | Collider SkillDefinition Field | Notes |
| ------------------ | ----------------------------------------- | ------------------------------------------ |
| `name` | `name` | Direct map |
| `description` | `description` | Direct map |
| `version` | Handled by NodeContainer versioning | Container-level, not skill-level |
| `tools` | `tool_ref` (single) + container `tools[]` | Collider separates tool ownership |
| `authors` | Container `session_meta.username` | Session-scoped |
| `tags` | Container `config.domain` | Domain-based categorization |
| — | `emoji` | Collider extension |
| — | `user_invocable` / `model_invocable` | Collider extension: invocation control |
| — | `invocation_policy` | Collider extension: auto/confirm/disabled |
| — | `requires_bins` / `requires_env` | Collider extension: dependency declaration |
| — | `markdown_body` | Same as SKILL.md body content |

**Key difference**: Agent Skills stores skills as flat files in `skills/`
directories. Collider stores skills as **JSON objects in a versioned
database**, delivered programmatically via gRPC. The `workspace_writer`
serializes Collider skills TO `SKILL.md` format for Claude Code CLI
compatibility, but the canonical form is the database record.

**Collider skills are more fine-grained** because:

1. **Invocation policies** — The standard doesn't specify who/how a skill can
  be invoked. Collider has `user_invocable`, `model_invocable`, and
  `invocation_policy` to control this precisely.
2. **Dependency declarations** — `requires_bins` and `requires_env` allow
  runtime validation before skill activation.
3. **Graph-scoped visibility** — A skill attached to a node is only visible
  to agent sessions composed from that node's subtree. No global skill
  namespace pollution.
4. **Versioned containers** — Skills version with their container. Rollback a
  container, rollback its skills.
5. **Tool separation** — Skills reference tools by name; tools are defined
  separately with their own schemas. This allows the same tool to be wrapped
  by multiple skills with different contexts.

### Serialization Compatibility

Collider maintains full round-trip compatibility with the Agent Skills standard:

```text
DB (SkillDefinition JSON)
  → workspace_writer → SKILL.md file (Agent Skills format)
  → Claude Code CLI reads SKILL.md → agent has the skill

  OR (new path):

DB (SkillDefinition JSON)
  → gRPC GetBootstrap → ContextChunk.SkillChunk
  → NanoClawBridge SDK → system prompt section (no SKILL.md file)
```

Both paths deliver the same capability to the agent. The standard is the
**interchange format**, the database is the **storage format**, and gRPC is the
**delivery protocol**.

---

## Application Model Templates

An **application model template** is a pre-configured cluster of NodeContainers
that hydrate a workspace graph for a specific use case. Templates are themselves
versioned and stored as container snapshots.

```text
Template: "FastAPI Microservice"
├── root/          # Container: FastAPI instructions, Python rules, deployment tools
│   ├── api/       # Container: Endpoint skills, OpenAPI tools, request validation
│   ├── models/    # Container: Pydantic skills, migration tools, schema knowledge
│   ├── tests/     # Container: pytest skills, coverage tools, test patterns
│   └── deploy/    # Container: Docker skills, CI/CD workflows, env management
```

Applying a template to a workspace node instantiates this container tree as
children of the target node. The template containers inherit from the target's
ancestry — so a "FastAPI Microservice" template applied inside a Collider
workspace automatically inherits Collider's platform rules, authentication
tools, and deployment workflows.

This is **compositional by construction**: templates are not standalone — they
compose with whatever context they're inserted into.

---

## Architecture Overview

### Services

| Service | Port | Role |
| ----------------------- | ------------ | --------------------------------------------------------------- |
| ColliderDataServer | 8000 | Node CRUD, bootstrap rendering, auth, SSE |
| ColliderGraphToolServer | 8001 / 50052 | MCP tool server, gRPC tool registry, tool execution |
| ColliderVectorDbServer | 8002 | Semantic search for tool/skill discovery |
| ColliderAgentRunner | 8004 / 50051 | Context composition, gRPC context streaming, session management |
| NanoClawBridge | 18789 | Anthropic SDK agent sessions, WebSocket RPC, agent teams |
| FFS4 Sidepanel | 4201 | XYFlow graph workspace browser + agent chat |
| FFS6 IDE Viewer | 4200 | Tree-based node viewer, CRUD, auth |

### Context Delivery Pipeline

```text
NodeContainer (DB)
  → DataServer /bootstrap/{node_id} (renders to AgentBootstrap JSON)
    → AgentRunner compose_context_set() (merges multiple bootstraps, leaf-wins)
      → gRPC GetBootstrap (streams to NanoClawBridge)
        → Anthropic SDK session (system prompt + skills + tools)
          → SSE ContextDelta subscription (live updates)
```

### Workspace Sync

The `.agent/` folder in each workspace on disk is the **human-readable** representation of a NodeContainer. The Seeder CLI syncs `.agent/` → DB:

```text
.agent/
├── manifest.yaml          # Container config (domain, emoji, description)
├── instructions/          # InstructionDefinition files
├── rules/                 # RuleDefinition files
├── knowledge/             # KnowledgeEntry files
├── skills/                # SKILL.md files (Agent Skills format)
├── tools/                 # ToolDefinition files
└── workflows/             # WorkflowDefinition files (YAML)
```

This dual representation means workspaces are **editable by both humans and
agents**. Humans edit `.agent/` files in their IDE. The Seeder syncs to DB.
The agent reads from DB via gRPC. Changes flow in both directions.

---

## Network-Deterministic vs Object-Oriented Composition

Traditional OOP builds systems from objects with **emergent** dependencies —
objects discover each other at runtime, and the dependency graph is implicit.
Collider takes the opposite approach: **declared dependencies** in a **network-
deterministic** graph.

Every NodeContainer explicitly declares:

- What it **requires** (tools, bins, env vars)
- What it **provides** (skills, knowledge, workflows)
- What it **inherits** (ancestry path in the workspace graph)

The composition is deterministic: given the same node selection and role, the
same context is always produced. There are no runtime surprises. The graph
topology IS the dependency specification.

This enables:

- **Task decomposition** — Split a large node into children. Each child has a
  well-defined subset of the parent's context.
- **Recursive functorial composition** — Compose any subtree into a valid agent context. The composition preserves the categorical structure.
- **Validated logic** — Tool schemas define input/output contracts. Workflow
  steps reference tools by name. Skills reference tools they wrap. Everything
  is type-checked at the container level.

---

## Do's and Don'ts

### Do

- Store all agent context in NodeContainers — never hardcode instructions in application code
- Use the leaf-wins merge strategy — child containers override parent containers
- Define skills at the most specific node possible — avoid global skill pollution
- Separate tools from skills — tools are capabilities, skills are contextualized usage of tools
- Use invocation policies — not every skill should be auto-invocable by the model
- Version containers alongside application code — context is code
- Keep `.agent/` folders human-readable — they are the documentation AND the context

### Don't

- Don't bypass the container model by writing custom system prompts in application code
- Don't create monolithic skill files — split into focused, composable units
- Don't duplicate tool definitions across containers — reference shared tools by name
- Don't mix workspace structure concerns with application logic — Collider is agnostic
- Don't rely on filesystem-based context delivery for production — use gRPC + SDK path
- Don't flatten the graph for simplicity — the hierarchy IS the information

---

## Getting Started

### Prerequisites

- Python 3.12+, UV package manager
- Node.js 20+, npm
- Chrome browser (for extension)
- API keys: `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`

### Quick Start

```bash
# 1. Seed the database
cd workspaces/FFS1_ColliderDataSystems/FFS2_.../ColliderDataServer
uv run python -m src.seed

# 2. Start backend services
uv run uvicorn src.main:app --port 8000  # DataServer
uv run uvicorn src.main:app --port 8001  # GraphToolServer
uv run uvicorn src.main:app --port 8004  # AgentRunner (add GRPC_CONTEXT_ENABLED=true)

# 3. Start NanoClawBridge
cd .../NanoClawBridge
USE_SDK_AGENT=true USE_GRPC_CONTEXT=true npm run dev

# 4. Start FFS4 sidepanel
cd .../FFS3_.../apps/ffs4
npx vite

# 5. Load Chrome extension
# Chrome -> Extensions -> Load unpacked -> ColliderMultiAgentsChromeExtension/build/
```

### Creating Your First Agent Session

1. Open the Chrome extension sidepanel
2. Switch to the "Agent" tab (loads FFS4 at localhost:4201)
3. Select an application from the dropdown
4. Click nodes in the graph to select context
5. Choose a role (app_user, app_admin, collider_admin, superadmin)
6. Click "Compose" to create a session
7. Chat with Nano — the agent has the composed context from your selected nodes

---

## License

Proprietary. All rights reserved.
