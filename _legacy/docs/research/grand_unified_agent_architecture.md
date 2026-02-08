# Grand Unified Agent Architecture

> **Research Document**: Workspace ↔ Runtime Symmetry Model  
> **Date**: 2026-01-25  
> **Status**: Research Complete

## Executive Summary

The key insight is: **Runtime environment should mirror workspace environment**. This document maps how the existing `.agent/` workspace pattern can translate directly into runtime agent configuration, creating a unified model where agents at any level (workspace, application, runtime) follow the same structural pattern.

---

## 1. The Grand Unified Model

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          GRAND UNIFIED AGENT PATTERN                         │
│                                                                              │
│  Both WORKSPACE agents (VS Code Copilot) and RUNTIME agents (pydantic-deep) │
│  use the SAME structural pattern:                                            │
│                                                                              │
│    .agent/                                                                   │
│    ├── manifest.yaml      # What to include/inherit                         │
│    ├── rules/             # Behavioral constraints                          │
│    ├── instructions/      # System instruction fragments                    │
│    ├── workflows/         # Process definitions                             │
│    ├── configs/           # Runtime-specific settings                       │
│    └── [skills/]          # Optional: skill packages                        │
│                                                                              │
│    knowledge/             # Domain knowledge (read-only from downstream)    │
│    ├── domains/           # Expertise areas                                 │
│    └── [junctions]        # Symlinks to parent knowledge                    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Workspace ↔ Runtime Symmetry Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   WORKSPACE DOMAIN                          RUNTIME DOMAIN                  │
│   (VS Code / IDE)                           (pydantic-deep / Agents)        │
│                                                                             │
│   ┌─────────────────┐                       ┌─────────────────┐             │
│   │  .agent/        │  ════════════════════ │  DeepAgentDeps  │             │
│   │                 │      MIRRORS          │                 │             │
│   │  manifest.yaml  │──────────────────────▶│  skill_dirs     │             │
│   │  rules/         │──────────────────────▶│  instructions   │             │
│   │  instructions/  │──────────────────────▶│  system_prompt  │             │
│   │  workflows/     │──────────────────────▶│  tools          │             │
│   │  configs/       │──────────────────────▶│  subagents      │             │
│   └─────────────────┘                       └─────────────────┘             │
│           │                                         │                       │
│           │ inheritance                             │ deps.clone_for_       │
│           ▼                                         ▼ subagent()            │
│   ┌─────────────────┐                       ┌─────────────────┐             │
│   │  parent .agent/ │                       │  parent deps    │             │
│   │  (workspace/    │                       │  (shared        │             │
│   │   factory)      │                       │   backend)      │             │
│   └─────────────────┘                       └─────────────────┘             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Current .agent Structure at Factory Level

### D:\factory\.agent\manifest.yaml
```yaml
# Agent Context Manifest - Factory Root
# This is the root level - no parent includes
includes: []

# Local rules and instructions
local:
  rules: "./rules/"
  instructions: "./instructions/"
  workflows: "./workflows/"

# This context is inherited by all child workspaces
exports:
  - rules/sandbox.md         # Access control (what agents can read/write)
  - rules/identity.md        # Agent persona
  - rules/code_patterns.md   # Coding standards
  - rules/math_*.md          # Domain-specific rules
  - instructions/knowledge_hierarchy.md
  - instructions/instruction_inheritance.md
```

### Factory .agent/ Contents
```
D:\factory\.agent\
├── manifest.yaml           # Root manifest (no includes, exports to children)
├── rules/
│   ├── sandbox.md          # Write: CWD only, Read: knowledge/, parts/
│   ├── identity.md         # Agent persona definition
│   ├── code_patterns.md    # Factory-wide coding standards
│   ├── math_coding_style.md
│   ├── math_maintenance.md
│   └── math_testing.md
├── instructions/
│   ├── knowledge_hierarchy.md    # How knowledge flows upstream/downstream
│   └── instruction_inheritance.md  # How .agent/ cascade works
└── workflows/
    └── screenshots/        # Workflow visual aids
```

---

## 3. How .agent Pattern Translates to Runtime

### pydantic-deep Runtime Equivalents

| Workspace (.agent/)         | Runtime (pydantic-deep)                    |
|-----------------------------|-------------------------------------------|
| `manifest.yaml`             | `create_deep_agent()` configuration       |
| `rules/*.md`                | Base `instructions` parameter             |
| `instructions/*.md`         | Dynamic system prompt fragments           |
| `workflows/*.md`            | Skill packages or tool configurations     |
| `configs/*.json`            | `SubAgentConfig`, interrupt_on, etc.      |
| Parent inheritance          | `deps.clone_for_subagent()`               |

### pydantic-deep Dynamic System Instruction Capability

From the pydantic-deep research, `create_deep_agent()` supports:

```python
# 1. Static instructions (base prompt - like rules/*.md)
agent = create_deep_agent(
    instructions="You are a helpful assistant...",  # Base persona
)

# 2. Dynamic system prompts (auto-composed at runtime)
@agent.instructions
def dynamic_instructions(ctx: RunContext[DeepAgentDeps]) -> str:
    """Generated at EVERY call based on current state."""
    parts = []
    
    # Equivalent to loading .agent/instructions/*.md
    uploads_prompt = ctx.deps.get_uploads_summary()      # Context
    todo_prompt = get_todo_system_prompt(ctx.deps)       # Planning state
    console_prompt = get_console_system_prompt()         # Filesystem rules
    subagent_prompt = get_subagent_system_prompt(...)    # Delegation
    skills_prompt = get_skills_system_prompt(...)        # Loaded skills
    
    return "\n\n".join(parts)

# 3. Skill directories (like .agent/workflows/ or external skills/)
agent = create_deep_agent(
    skill_directories=[
        {"path": "./.agent/workflows", "recursive": True},  # Can be .agent!
        {"path": "./skills", "recursive": True},
    ],
)
```

### Key Insight: Skills ARE Runtime .agent/

pydantic-deep's **Skills** system is exactly the runtime equivalent of `.agent/`:

```
SKILL.md Format (pydantic-deep)        │  .agent/ Instruction Format
───────────────────────────────────────│────────────────────────────────
---                                    │  ---
name: code-review                      │  trigger: always_on
description: Review code...            │  description: Code review rules
version: 1.0.0                         │  ---
---                                    │
# Instructions                         │  # Instructions
Follow these guidelines...             │  Follow these guidelines...
```

**The SKILL.md format IS the .agent/ instruction format!**

---

## 4. Application-Level .agent Structure

### D:\factory\workspaces\collider_apps\applications\my-tiny-data-collider\.agent\

```yaml
# manifest.yaml
includes:
  # Factory level (global)
  - path: "../../../.agent"
    type: "factory"
    load:
      - rules/sandbox.md
      - rules/identity.md
      - rules/code_patterns.md
      - instructions/knowledge_hierarchy.md

  # Workspace level
  - path: "../../.agent"
    type: "workspace"
    load:
      - rules/pilot.md
      - instructions/workspace.md

# Local rules and instructions are always loaded
local:
  rules: "./rules/"
  instructions: "./instructions/"
  configs: "./configs/"
  workflows: "./workflows/"
```

**Contents:**
```
.agent/
├── manifest.yaml
├── configs/
│   └── notion_map.json           # External service configs
├── instructions/
│   └── application.md            # App-specific context
├── rules/
│   ├── backend-expert.md         # Role: backend dev
│   ├── frontend-artist.md        # Role: frontend dev
│   ├── collider.md               # Master controller identity
│   └── environment.md            # Env/config management
└── workflows/
    ├── dev.md                    # /dev command
    ├── test.md                   # /test command
    ├── lint.md                   # /lint command
    └── ...                       # Other workflows
```

---

## 5. Frontend Pilot: Where Runtime Injection Happens

### Current Implementation (pilotService.ts)

```typescript
// Current: Hardcoded PilotSpec objects
const STUDIO_PILOT_SPEC: PilotSpec = {
  id: "studio-pilot",
  instructions: `You are the Collider Studio Pilot...`,  // STATIC
  // ...
};

// Dynamic context injection happens here:
private buildSystemPrompt(): string {
  let prompt = this.spec.instructions;  // Base instructions
  
  if (this.context) {
    prompt += "\n\n## Current Context\n";
    // Add breadcrumbs, container name, file count, staged files...
  }
  
  return prompt;
}
```

### Proposed: Read from .agent/ at Runtime

```typescript
// PROPOSED: Load from .agent/ structure
interface AgentManifest {
  includes: Array<{path: string; load: string[]}>;
  local: {rules: string; instructions: string; workflows: string};
}

class AgentContextLoader {
  private manifest: AgentManifest;
  
  async loadFromAgent(agentPath: string): Promise<PilotSpec> {
    // 1. Load manifest.yaml
    this.manifest = await this.loadManifest(agentPath);
    
    // 2. Resolve inheritance chain
    const inheritedRules = await this.loadInheritedRules();
    
    // 3. Load local rules/instructions
    const localRules = await this.loadLocalRules(agentPath);
    
    // 4. Compose system instruction
    return {
      id: this.manifest.id,
      instructions: [...inheritedRules, ...localRules].join('\n\n'),
      // ...
    };
  }
}

// Usage in pilotService.ts
const agentLoader = new AgentContextLoader();
const spec = await agentLoader.loadFromAgent('./.agent/');
```

---

## 6. Knowledge Folder Nesting Pattern

### Current Factory Knowledge Structure
```
D:\factory\knowledge\
├── .sync_manifest.json
├── development/        # Implementation patterns
├── domains/            # Domain expertise
├── journal/            # Temporal notes
├── projects/           # Project knowledge
├── references/         # External docs
├── research/           # New insights
└── workflows/          # Process definitions
```

### Workspace Knowledge (with junctions to factory)
```
D:\factory\workspaces\collider_apps\knowledge\
├── collider/           # Local: Collider-specific
├── collider.md
├── pilot_behaviors.md
├── factory_development → D:\factory\knowledge\development\  (junction)
├── factory_domains     → D:\factory\knowledge\domains\      (junction)
└── factory_research    → D:\factory\knowledge\research\     (junction)
```

### Application Knowledge (with junctions)
```
D:\factory\workspaces\collider_apps\applications\my-tiny-data-collider\knowledge\
├── project             → knowledge/projects/collider/       (junction)
├── math                → knowledge/domains/mathematics/     (junction)
└── [local impl notes]
```

### Knowledge Flow Rules

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        KNOWLEDGE PROMOTION FLOW                         │
│                                                                         │
│   Application (specific) ─────▶ Workspace (patterns) ─────▶ Factory    │
│        ▲                              ▲                        │        │
│        │ WRITE                        │ WRITE                  │ WRITE  │
│        │                              │                        ▼        │
│   App agents               Workspace agents              Factory arch.  │
│                                                                         │
│   ◀──────────────────────── READ-ONLY ──────────────────────────────── │
│   (downstream reads upstream via junctions)                             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Nested Structure Model: Complete Inheritance Chain

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     FACTORY → WORKSPACE → APP → RUNTIME                     │
│                                                                             │
│   D:\factory\                                                               │
│   ├── .agent/                      ◀──── ROOT: Exports sandbox, identity    │
│   │   ├── rules/sandbox.md              code_patterns, knowledge rules      │
│   │   └── instructions/...                                                  │
│   ├── knowledge/                   ◀──── SOURCE: All domain knowledge       │
│   │                                                                         │
│   └── workspaces/                                                           │
│       └── collider_apps/                                                    │
│           ├── .agent/              ◀──── INHERITS: factory .agent/          │
│           │   ├── manifest.yaml          ADDS: workspace-specific rules     │
│           │   └── rules/pilot.md                                            │
│           ├── knowledge/           ◀──── JUNCTIONS: to factory/knowledge    │
│           │   └── factory_*              LOCAL: workspace-specific          │
│           │                                                                 │
│           └── applications/                                                 │
│               └── my-tiny-data-collider/                                    │
│                   ├── .agent/      ◀──── INHERITS: workspace + factory      │
│                   │   ├── rules/         ADDS: app-specific roles           │
│                   │   ├── workflows/     ADDS: /dev, /test commands         │
│                   │   └── configs/       ADDS: runtime configs              │
│                   ├── knowledge/   ◀──── JUNCTIONS: project, math           │
│                   │                                                         │
│                   └── runtime/           RUNTIME AGENTS                     │
│                       └── agents/  ◀──── READS: .agent/ at init time        │
│                           │              COMPOSES: system prompt from       │
│                           │              inherited rules + instructions     │
│                           │                                                 │
│                           ▼                                                 │
│                   ┌─────────────────────────────────────────────────┐       │
│                   │  create_deep_agent(                             │       │
│                   │    instructions=compose_from_agent(".agent/"),  │       │
│                   │    skill_directories=[".agent/workflows"],      │       │
│                   │    subagents=[...],                             │       │
│                   │  )                                              │       │
│                   └─────────────────────────────────────────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. pydantic-deep Capabilities That Enable This

### 8.1 Dynamic System Prompt Composition

pydantic-deep already supports dynamic instruction injection at runtime:

```python
# From agent.py lines 310-355
@agent.instructions
def dynamic_instructions(ctx: RunContext[DeepAgentDeps]) -> str:
    """Generate dynamic instructions based on current state."""
    parts = []
    
    # 1. Uploaded files context
    uploads_prompt = ctx.deps.get_uploads_summary()
    if uploads_prompt:
        parts.append(uploads_prompt)
    
    # 2. Todo state (planning)
    todo_prompt = get_todo_system_prompt(ctx.deps)
    if todo_prompt:
        parts.append(todo_prompt)
    
    # 3. Filesystem rules
    console_prompt = get_console_system_prompt()
    if console_prompt:
        parts.append(console_prompt)
    
    # 4. Subagent availability
    subagent_prompt = get_subagent_system_prompt(prompt_configs)
    if subagent_prompt:
        parts.append(subagent_prompt)
    
    # 5. Skills available
    skills_prompt = get_skills_system_prompt(ctx.deps, loaded_skills)
    if skills_prompt:
        parts.append(skills_prompt)
    
    return "\n\n".join(parts)
```

**This is THE mechanism for injecting .agent/ content at runtime!**

### 8.2 Skill Directory Discovery

Skills work exactly like `.agent/workflows/`:

```python
# Skills are discovered from filesystem at agent creation
agent = create_deep_agent(
    skill_directories=[
        {"path": "./.agent/workflows", "recursive": True},
        {"path": "./skills", "recursive": True},
    ],
)

# Each skill is a SKILL.md with frontmatter + instructions
# Exactly like .agent/instructions/*.md format!
```

### 8.3 Subagent Inheritance via deps.clone_for_subagent()

```python
# From deps.py - subagents inherit parent's backend but get isolated state
def clone_for_subagent(self, max_depth: int = 0) -> DeepAgentDeps:
    """Clone deps for a subagent with isolated todos but shared backend."""
    return DeepAgentDeps(
        backend=self.backend,      # SHARED: Same filesystem
        files=self.files,          # SHARED: Same file cache
        todos=[],                  # ISOLATED: Fresh todo list
        subagents={},              # ISOLATED: No nested delegation
        uploads=self.uploads,      # SHARED: Same uploads
    )
```

---

## 9. Changes Needed to Implement This

### 9.1 Create AgentContextLoader Library

```python
# factory/parts/agent_context/loader.py

from pathlib import Path
from typing import TypedDict
import yaml

class AgentManifest(TypedDict):
    includes: list[dict]
    local: dict
    exports: list[str]

class AgentContextLoader:
    """Load and compose .agent/ context for runtime agents."""
    
    def __init__(self, agent_path: str):
        self.agent_path = Path(agent_path)
        self.manifest = self._load_manifest()
    
    def _load_manifest(self) -> AgentManifest:
        manifest_file = self.agent_path / "manifest.yaml"
        return yaml.safe_load(manifest_file.read_text())
    
    def compose_instructions(self) -> str:
        """Compose full system instructions from inheritance chain."""
        parts = []
        
        # 1. Load inherited instructions (resolve includes)
        for include in self.manifest.get("includes", []):
            parent_path = self.agent_path / include["path"]
            for file in include.get("load", []):
                content = (parent_path / file).read_text()
                parts.append(content)
        
        # 2. Load local rules
        rules_dir = self.agent_path / self.manifest["local"]["rules"]
        for rule_file in rules_dir.glob("*.md"):
            parts.append(rule_file.read_text())
        
        # 3. Load local instructions
        inst_dir = self.agent_path / self.manifest["local"]["instructions"]
        for inst_file in inst_dir.glob("*.md"):
            parts.append(inst_file.read_text())
        
        return "\n\n---\n\n".join(parts)
    
    def get_skill_directories(self) -> list[dict]:
        """Get skill directories from .agent/workflows."""
        workflows = self.agent_path / self.manifest["local"].get("workflows", "workflows")
        return [{"path": str(workflows), "recursive": True}]
    
    def create_deep_agent_kwargs(self) -> dict:
        """Return kwargs for create_deep_agent()."""
        return {
            "instructions": self.compose_instructions(),
            "skill_directories": self.get_skill_directories(),
        }
```

### 9.2 Modify Runtime Agents to Use Loader

```python
# runtime/agents/collider_pilot.py

from factory.parts.agent_context import AgentContextLoader
from pydantic_deep import create_deep_agent

# Load context from .agent/
loader = AgentContextLoader(".agent/")

# Create agent with composed context
agent = create_deep_agent(
    model="google-vertex:gemini-2.5-flash",
    **loader.create_deep_agent_kwargs(),  # Injects rules + instructions
    include_filesystem=True,
    include_todo=True,
)
```

### 9.3 Update Frontend Pilot to Read from .agent/

```typescript
// frontend/src/pilot/agentContextLoader.ts

export async function loadAgentContext(agentPath: string): Promise<PilotSpec> {
  // 1. Fetch manifest.yaml
  const manifest = await fetch(`${agentPath}/manifest.yaml`).then(r => r.text());
  
  // 2. Resolve includes and load rules/instructions
  // ... (implement YAML parsing and file loading)
  
  // 3. Return composed PilotSpec
  return {
    id: "dynamic-pilot",
    instructions: composedInstructions,
    // ...
  };
}
```

### 9.4 Standardize SKILL.md ↔ Instruction.md Format

Both formats should be interchangeable:

```markdown
---
name: backend-expert          # For skills: name
trigger: model_decision       # For instructions: when to apply
description: Backend dev role
version: 1.0.0
---

# Backend Expert Instructions

When working on backend code...
```

---

## 10. Summary: The Unified Model

### Core Principle

> **"An agent's environment is defined by the same structure whether it runs in an IDE or at runtime."**

### The Pattern

```
.agent/
├── manifest.yaml      →  Defines inheritance, exports, local paths
├── rules/             →  Behavioral constraints (sandbox, identity)
├── instructions/      →  System prompt fragments (composed at runtime)
├── workflows/         →  Skills/processes (loaded as pydantic-deep skills)
└── configs/           →  Runtime-specific settings

knowledge/
├── [junctions]        →  Read-only access to parent knowledge
└── [local]            →  Write access for this level's agents
```

### Benefits

1. **Consistency**: Same mental model for workspace and runtime agents
2. **Inheritance**: Natural cascade from factory → workspace → app → runtime
3. **Separation of Concerns**: Rules vs Instructions vs Workflows vs Configs
4. **Tooling**: Same loader works for IDE and runtime agents
5. **Knowledge Flow**: Clear upstream/downstream read/write patterns

### pydantic-deep Enablers

| Feature | How It Enables Unified Model |
|---------|------------------------------|
| `instructions` parameter | Load composed rules/instructions from .agent/ |
| `@agent.instructions` decorator | Dynamic injection at runtime |
| `skill_directories` | Treat .agent/workflows/ as skill packages |
| `SubAgentConfig` | Define delegation in .agent/configs/ |
| `deps.clone_for_subagent()` | Preserve inheritance in subagent chain |
| `get_*_system_prompt()` | Modular prompt composition |

---

## Appendix A: File References

| File | Purpose |
|------|---------|
| [manifest.yaml](D:\factory\.agent\manifest.yaml) | Factory root manifest |
| [knowledge_hierarchy.md](D:\factory\.agent\instructions\knowledge_hierarchy.md) | Knowledge flow rules |
| [instruction_inheritance.md](D:\factory\.agent\instructions\instruction_inheritance.md) | .agent/ cascade rules |
| [sandbox.md](D:\factory\.agent\rules\sandbox.md) | Access control |
| [pilotService.ts](D:\factory\workspaces\collider_apps\applications\my-tiny-data-collider\frontend\src\pilot\pilotService.ts) | Frontend pilot (current) |
| [coordinator.py](D:\factory\agent-studio\backend\app\agents\coordinator.py) | Agent-studio coordinator |
| [pydantic-deep/agent.py](https://github.com/vstorm-co/pydantic-deepagents/blob/main/pydantic_deep/agent.py) | Dynamic instruction injection |

## Appendix B: Implementation Checklist

- [ ] Create `factory/parts/agent_context/` library
- [ ] Implement `AgentContextLoader` class
- [ ] Update runtime agents to use loader
- [ ] Create TypeScript version for frontend
- [ ] Standardize SKILL.md / instruction.md format
- [ ] Document the unified model in workspace-guide.md
- [ ] Create example "runtime .agent/" structure
