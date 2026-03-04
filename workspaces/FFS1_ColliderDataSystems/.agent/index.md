# FFS1 Agent Context

FFS1 is the inheritance backbone for FFS2 and FFS3. It provides data governance,
shared contracts, and orchestration context.

## Loads from FFS0

- `rules/sandbox.md`, `rules/code_patterns.md`, `rules/env_and_secrets.md`
- `knowledge/moos_architecture_foundations.md`

## Required Exports (to FFS2/FFS3)

- `instructions/agent_system.md`
- `instructions/filesyst_domain.md`
- `skills/ide_code_assist.md`
- `tools/filesyst_tools.json`
- `rules/stack_standards.md`
- `rules/communication_architecture.md`
- `rules/code_quality.md`
- `rules/project_structure.md`
- `workflows/cross-service-validation-gates.md`
- `workflows/dev-start.md`
- `workflows/markdown-quality.md`
- `workflows/markdown-quality-all.md`

Keep this layer minimal and stable; leaf workspaces add implementation details.
