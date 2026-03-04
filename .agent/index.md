# FFS0 Factory - Agent Context

Root governance layer for inheritance into FFS1 and downstream workspaces.

## Structure

- `instructions/` — base intent contract (agent_system.md)
- `rules/` — global constraints (sandbox, code_patterns, versioning, env_and_secrets, public_repo_safety)
- `configs/` — shared settings (api_providers, users, workspace_defaults)
- `knowledge/` — canonical architecture references and research papers
- `workflows/` — runbooks for rehydration, db-sync, git collab, pre-public readiness
- `skills/`, `tools/` — reserved for future wiring

## Inheritance Chain

`FFS0 .agent` → `FFS1 .agent` → `FFS2/FFS3 .agent` → app-level `.agent` stubs (`ffs4/ffs5/ffs6`)

Strategy: `deep_merge` at every level.

## Canonical References

- [Conversation Rehydration Runbook](workflows/conversation-state-rehydration.md)
- [MOOS Architecture Foundations](knowledge/moos_architecture_foundations.md)
- [MOOS Developer Vision](knowledge/moos_developers_vision.md)
- [MOOS Implementation Details](knowledge/moos_implementation%20_details.md)
- [Git Collaboration Policy](workflows/git-collaboration-policy.md)
- [Workspace-to-DB Sync Contract](workflows/db-sync-contract.md)
- [Pre-Public Readiness Checklist](workflows/pre-public-readiness-checklist.md)
- [Manifest](manifest.yaml)
