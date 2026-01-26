# Factory Agent Context

> Root `.agent/` for the Factory workspace. Inherited by all child workspaces.

## Quick Reference

| Command                    | Description                            |
| -------------------------- | -------------------------------------- |
| `local-ux agent`           | Run workspace agent (merges hierarchy) |
| `local-ux pilot container` | Run Container Pilot                    |
| `local-ux pilot studio`    | Run Studio Pilot                       |
| `local-ux info`            | Show config status                     |

---

## 🤖 FOR AI AGENTS: How to Read This System

If you are an AI (Copilot, Agent, or Assistant) entering this workspace, understand your anatomy:

### 1. The Manifest (`manifest.yaml`) = Your Wiring Diagram

- **Role**: Defines your identity and inheritance.
- **Action**: Read this FIRST. It tells you which `rules` and `instructions` apply to you.
- **Inheritance**: You embody the **Factory Architect** (Root) + **Workspace Expert** (Child) + **Application Specialist** (Leaf).

### 2. The Components = Your Brain Lobes

| Component           | Mental Faculty        | Directive                                                                                              |
| :------------------ | :-------------------- | :----------------------------------------------------------------------------------------------------- |
| **`rules/`**        | **Conscience**        | **HARD CONSTRAINTS**. Never violate these. (e.g., "Do not write outside CWD").                         |
| **`instructions/`** | **Methodology**       | **HOW-TO GUIDES**. Follow these patterns for consistency. (e.g., "Knowledge Hierarchy").               |
| **`knowledge/`**    | **Long-Term Memory**  | **CONTEXT**. Read-only patterns, domains, and project history. Check here before inventing new things. |
| **`workflows/`**    | **Motor Skills**      | **TASKS**. Repeatable processes. (e.g., "Run Dev Environment").                                        |
| **`configs/`**      | **Senses & Settings** | **CONFIGURATION**. API keys, user profiles, default settings.                                          |

> **Directive**: You are a unified intelligence. When operating in a child workspace, you MUST respect the Factory's "Conscience" (Rules) while applying the Application's "Methodology" (Instructions).

---

## Folder Structure

```
D:\factory\.agent\
├── index.md              ← You are here
├── manifest.yaml         ← Declares exports (inherited by children)
├── instructions/         ← How-to guides
│   ├── instruction_inheritance.md
│   └── knowledge_hierarchy.md
├── rules/                ← Behavioral constraints (6 files)
│   ├── sandbox.md        ← Security boundaries
│   ├── identity.md       ← Agent persona
│   ├── code_patterns.md  ← Coding standards
│   ├── math_coding_style.md
│   ├── math_maintenance.md
│   └── math_testing.md
├── knowledge/            ← Domain context
│   ├── domains/          ← Per-domain knowledge
│   ├── journal/          ← Session logs
│   ├── projects/         ← Project-specific context
│   ├── references/       ← External resources
│   └── research/         ← Research notes
├── workflows/            ← Task sequences
│   └── screenshots/      ← Visual guides
└── configs/              ← Shared settings
    ├── users.yaml        ← User profiles
    ├── api_providers.yaml← API endpoints
    ├── local_ux.yaml     ← CLI config
    └── workspace_defaults.yaml
```

---

## Hierarchy Flow

```
D:\factory\.agent\                    ← ROOT (this folder)
    │
    ├── inherits nothing (root level)
    │
    └── exports to children:
            ↓
D:\factory\workspaces\*\.agent\       ← WORKSPACE LEVEL
            ↓
D:\factory\workspaces\*\apps\*\.agent\← APP LEVEL
```

**Merge Rules:**

- `instructions/` → Last wins (child overrides parent)
- `rules/` → Accumulate (all apply)
- `knowledge/` → Accumulate (all available)
- `workflows/` → Accumulate (all available)

---

## For Workspace Agents

The `local-ux agent` command:

1. **Discovers** `.agent/` folders from CWD up to factory root
2. **Merges** using `AgentSpec.load()` pattern
3. **Builds** workspace context (git branch, structure)
4. **Starts** interactive chat via `DeepAgentCLI`

```python
# parts/runtimes/local_ux/workspace_agent.py
agent_dirs = find_agent_dirs(workspace_path)  # [child, parent, root]
spec = merge_agent_specs(agent_dirs)          # Merged AgentSpec
cli = DeepAgentCLI.from_spec(spec, context)   # Rich terminal UI
```

---

## For IDE / Copilot

VS Code and GitHub Copilot can read `.agent/` context:

| File                | IDE Usage              |
| ------------------- | ---------------------- |
| `instructions/*.md` | Custom instructions    |
| `rules/*.md`        | Behavioral constraints |
| `knowledge/*.md`    | Domain context for RAG |
| `manifest.yaml`     | Defines what to export |

**Copilot Instructions** (`.github/copilot-instructions.md`) can reference:

```markdown
Refer to .agent/rules/ for coding standards.
```

---

## For Pilots (Collider SDK)

Pilots are **app-specific agents** in `shared/collider_sdk/pilots/`:

```
my-tiny-data-collider/shared/collider_sdk/pilots/
├── container/            ← Container Pilot
│   ├── __init__.py       ← PILOT_SPEC definition
│   ├── instructions.md
│   ├── rules/
│   ├── workflows/
│   └── knowledge/
└── studio/               ← Studio Pilot
    └── ...
```

**Different from `.agent/`:**

- Pilots use `ColliderPilotSpec` (extends `AgentSpec`)
- Pilots inject runtime container context
- Pilots are loaded via `load_pilot("container")`

---

## Key Files

| File                         | Purpose                               |
| ---------------------------- | ------------------------------------- |
| `manifest.yaml`              | Declares exports for child workspaces |
| `configs/local_ux.yaml`      | CLI tool configuration                |
| `configs/api_providers.yaml` | Model endpoints                       |
| `rules/sandbox.md`           | Security boundaries                   |
| `rules/identity.md`          | Agent persona                         |

---

## Related Locations

| Path                                | Purpose                    |
| ----------------------------------- | -------------------------- |
| `parts/templates/agent_spec.py`     | Base `AgentSpec` class     |
| `parts/interfaces/cli_interface.py` | `DeepAgentCLI` terminal UI |
| `parts/runtimes/local_ux/`          | CLI entry points           |
| `secrets/api_keys.env`              | API keys (not committed)   |
