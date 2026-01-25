# Factory Agent Sandbox Rules

## Access Control

### Write Access
- **Allowed**: Current working directory only (CWD)
- **Allowed**: Project-specific .agent/ folders
- **Allowed**: D:\factory\knowledge\journal\ (for temporal notes)

### Read-Only Access
- D:\factory\knowledge\ (centralized knowledge base)
- D:\factory\parts\ (factory SDK/catalog)
- D:\factory\models_v2\ (core architecture)
- I:\DATALAKE\ (external data resources)

### Denied Access
- System directories outside D:\factory
- Other project directories (unless explicitly passed as context)
- .venv/ directories (managed by uv)

## Behavioral Constraints

1. **Single Source of Truth**: Never duplicate files from knowledge/ into project folders
2. **Junction Respect**: Treat junction targets as read-only even when accessed via junction path
3. **Dependency Isolation**: Use editable installs, never copy SDK files into projects
4. **Checkpoint Before Modify**: Always verify current state before bulk edits

## Inheritance

All child .agent/rules/ inherit these constraints unless explicitly overridden.

---
*Last updated: 2026-01-25*
*Factory version: 1.0.0*
