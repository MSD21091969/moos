# Agent Specification Pattern

> The unified pattern for agent configuration across Factory workspaces.

## Overview

`AgentSpec` is the generic template for defining agents. It works for:

- **L1 Workspace Agents**: Read from `.agent/` hierarchy (IDE, local CLI tools)
- **L2 Application Pilots**: Read from `pilots/{id}/` folders (frontend, Gradio tools)

Both use the **same folder structure** and **same loading mechanism**.

## Folder Structure Convention

```
{agent_dir}/
├── __init__.py      # Optional: AGENT_SPEC or PILOT_SPEC definition
├── instructions.md  # System prompt - WHO you are
├── rules/           # Behavioral constraints - HOW you behave
│   └── *.md
├── workflows/       # Task sequences - WHAT you can do
│   └── *.md
└── knowledge/       # Domain context - WHAT you know
    └── *.md
```

### File Purposes

| File/Folder | Purpose | pydantic-deep Equivalent |
|-------------|---------|--------------------------|
| `instructions.md` | Base system prompt | `instructions` parameter |
| `rules/*.md` | Behavioral rules appended to prompt | Part of system prompt |
| `workflows/*.md` | Task definitions with triggers | `skill_directories` |
| `knowledge/*.md` | Domain knowledge context | `context` / uploads |
| `__init__.py` | Spec config (model, capabilities) | Agent configuration |

## Usage Examples

### L2 Pilot (Application)

```python
from agent_factory.parts.templates.agent_spec import AgentSpec, load_agent_spec
from pathlib import Path

# Option 1: Load from folder
pilot = load_agent_spec("container", base_dir=Path("shared/pilots"))
full_prompt = pilot.get_full_instructions()
config = pilot.to_dict()

# Option 2: Define inline with folder loading
pilot = AgentSpec(
    id="container-pilot",
    name="Container Pilot",
    model="gemini-2.0-flash",
    agent_dir=Path("shared/pilots/container")
).load()
```

### L1 Workspace Agent

```python
from agent_factory.parts.templates.agent_spec import AgentSpec
from pathlib import Path

# Load workspace agent from .agent/ folder
agent = AgentSpec(
    id="workspace-agent",
    name="Workspace Agent",
    agent_dir=Path(".agent")
).load()

# Compose with inheritance (manual for now)
# Factory → Workspace → Application
```

## Folder Content Conventions

### instructions.md

The main system prompt. Supports YAML frontmatter:

```markdown
---
version: "1.0"
author: your-name
updated: 2026-01-25
---

# Agent Name

You are [agent description].

## Your Role
[What this agent does]

## Capabilities
[What tools/abilities are available]

## Communication Style
[How to respond]
```

### rules/*.md

Behavioral constraints. Each file is appended to the system prompt:

```markdown
# Rule: Context Awareness

- Always acknowledge the user's current context
- Reference specific files/containers by name
- Warn about unsaved changes
```

### workflows/*.md

Task sequences with optional frontmatter for triggers:

```markdown
---
description: "How to share a container with collaborators"
triggers: [share, sharing, collaborate, permission]
---

# Share Container Workflow

1. Identify the container to share
2. Ask for collaborator email
3. Explain permission levels:
   - **view**: Read-only access
   - **edit**: Can modify content
   - **admin**: Full control including sharing
4. Confirm the share action
```

### knowledge/*.md

Domain context loaded into the prompt:

```markdown
# Collider Concepts

## What is a Container?
A Collider container is a context wrapper that organizes user work.
NOT a Docker container.

## Container Hierarchy
Containers can be nested (containers within containers).
```

## Spec Definition (`__init__.py`)

Minimal configuration in the folder:

```python
from agent_factory.parts.templates.agent_spec import AgentSpec
from pathlib import Path

PILOT_SPEC = AgentSpec(
    id="container-pilot",
    name="Container Pilot",
    version="1.0.0",
    model="gemini-2.0-flash",
    temperature=0.7,
    max_tokens=2048,
    include_filesystem=False,
    include_todo=True,
    include_subagents=False,
    interrupt_on={},
)

# For dynamic loading
PILOT_DIR = Path(__file__).parent
```

## Instruction Composition

The `get_full_instructions()` method composes the final prompt:

```
[instructions.md content]

## Behavioral Rules
[rules/*.md content]

## Context
[knowledge/*.md content]
```

Workflows are NOT included in the prompt - they're available for programmatic access via `get_workflow()` and `get_workflow_by_trigger()`.

## Export for Frontend

```python
config = pilot.to_dict()
# Returns:
{
    "id": "container-pilot",
    "name": "Container Pilot",
    "version": "1.0.0",
    "instructions": "[full composed prompt]",
    "model": "gemini-2.0-flash",
    "temperature": 0.7,
    "maxTokens": 2048,
    "includeFilesystem": false,
    "includeTodo": true,
    "subagents": [...],
    "workflows": [...],
    "interruptOn": {}
}
```

## Relation to pydantic-deep

This pattern mirrors pydantic-deep's `create_deep_agent()`:

| AgentSpec | pydantic-deep |
|-----------|---------------|
| `instructions` | `instructions` parameter |
| `rules/` | Part of system prompt |
| `workflows/` | `skill_directories` |
| `knowledge/` | Context / uploads |
| `subagents` | `subagents` parameter |
| `interrupt_on` | `interrupt_on` parameter |

The same folder can be used by both:
- **Frontend**: Loads via API, uses Gemini JS SDK directly
- **Backend/CLI**: Uses `create_deep_agent()` with `skill_directories` pointing to `workflows/`

## Best Practices

1. **Keep instructions.md focused**: Who the agent is, not implementation details
2. **Use rules/ for constraints**: Things that should always apply
3. **Use workflows/ for procedures**: Step-by-step guides with triggers
4. **Use knowledge/ for context**: Domain knowledge the agent needs
5. **Version your specs**: Use frontmatter for tracking changes
6. **Test both modes**: Inline and folder-loaded should produce same behavior
