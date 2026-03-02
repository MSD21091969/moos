# FFS1 Agent Context

FFS1 is the inheritance backbone for FFS2 and FFS3.

## Required Exports
- `instructions/agent_system.md`
- `instructions/filesyst_domain.md`
- `skills/ide_code_assist.md`
- `tools/filesyst_tools.json`
- `rules/*` listed in manifest
- `workflows/*` listed in manifest

Keep this layer minimal and stable; leaf workspaces add implementation details.
