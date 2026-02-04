# FFS0 Factory - Agent System Instruction

> Root workspace instruction for all child workspaces.

## Role

You are assisting in the FFS0_Factory root workspace. This is the top-level container for:

- Agent Studio (AI development tools)
- Collider Data Systems (FFS1)
- Supporting infrastructure

## Workspace Structure

```
FFS0_Factory/
├── .agent/              ← This context (root)
├── agent-studio/        ← AI development tools
├── docs/                ← Documentation
├── models_v2/           ← Data models
├── parts/               ← Shared components
├── secrets/             ← Credentials (gitignored)
└── workspaces/
    └── FFS1_ColliderDataSystems/  ← Child workspace
        └── FFS2, FFS3...          ← Grandchildren
```

## Inheritance

This workspace exports rules and configs to all children:

- `rules/` - Coding patterns, sandbox, identity
- `configs/` - Users, API providers, defaults

Child workspaces inherit via their `manifest.yaml`.

## Key Rules

- Follow code patterns in `rules/`
- Respect sandbox boundaries
- Use established identity patterns
