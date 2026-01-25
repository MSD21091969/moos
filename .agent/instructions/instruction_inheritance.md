# Instruction Inheritance Rules

> Defines how agent instructions cascade through the workspace hierarchy.
> This structure serves multiple agent runtimes with shared rules.

## Agent Runtimes

| Runtime | Reads From | Purpose |
|---------|------------|---------|
| VS Code Copilot | All `.agent/` in workspace | IDE code assistance |
| Local CLI agents | Specific `.agent/` folder | Development automation |
| Gradio/WebUI agents | Workspace `.agent/` | Interactive local AI |
| Application agents | App `.agent/` + inherited | Runtime AI features |

## Inheritance Chain

```
D:\factory\.agent\
├── rules/                    ← GLOBAL (apply everywhere)
├── instructions/             ← GLOBAL instructions
└── workflows/                ← GLOBAL workflows

    ↓ INHERITED BY

D:\factory\workspaces\collider_apps\.agent\
├── rules/                    ← OVERRIDE or EXTEND global
├── instructions/             ← WORKSPACE-SPECIFIC
└── workflows/                ← WORKSPACE-SPECIFIC

    ↓ INHERITED BY

D:\factory\workspaces\collider_apps\applications\my-tiny-data-collider\.agent\
├── rules/                    ← OVERRIDE or EXTEND workspace
├── instructions/             ← APP-SPECIFIC
└── workflows/                ← APP-SPECIFIC
```

## Rule Resolution Order

When an agent needs a rule, it looks in this order:
1. **Application** `.agent/rules/` (most specific)
2. **Workspace** `.agent/rules/` (if not found)
3. **Factory** `.agent/rules/` (global fallback)

## Instruction Loading

Agents MUST load instructions in this order:
1. Factory `.agent/instructions/*.md`
2. Workspace `.agent/instructions/*.md`
3. Application `.agent/instructions/*.md`

Later instructions can **override** earlier ones for the same topic.

## Rule Categories

| Category | Scope | Example |
|----------|-------|---------|
| `sandbox.md` | Access control | File system permissions |
| `identity.md` | Agent persona | Role, capabilities |
| `code_patterns.md` | Coding standards | Style, conventions |
| `[domain]_*.md` | Domain rules | math_coding_style.md |
| `[app].md` | App-specific | collider.md, backend-expert.md |

## Runtime-Specific Configs

Application agents (pydantic-deep based) may have additional configs:
- `configs/` - Runtime settings, model configs
- Tool definitions, skill directories
- SubAgent configurations

These are loaded by the agent runtime, not by IDE agents.

## Override Syntax

To explicitly override a parent rule:

```markdown
# Rule Name

@overrides: factory/rules/sandbox.md

[new rule content]
```

To extend a parent rule:

```markdown
# Rule Name

@extends: factory/rules/code_patterns.md

[additional rules]
```

---
*Factory Instruction System v1.0*
