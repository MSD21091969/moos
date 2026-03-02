# FFS0 Factory - Agent Context

Root governance layer for inheritance into FFS1 and downstream workspaces.

## Structure

- `instructions/` — base intent contract
- `rules/` — global constraints
- `configs/` — shared settings
- `knowledge/` — canonical references
- `skills/`, `tools/`, `workflows/` — minimal placeholders for wiring consistency

## Inheritance Chain

`FFS0 .agent` → `FFS1 .agent` → `FFS2/FFS3 .agent` → app-level `.agent` stubs (`ffs4/ffs5/ffs6`)

## Canonical References

- [Conversation Rehydration Runbook](workflows/conversation-state-rehydration.md)
- [Canonical Glossary v1](knowledge/current-codebase-glossary-canonical-v1.md)
- [Control Plane Governance](knowledge/control-plane-governance.md)
- [RBAC to GitHub Mapping](knowledge/rbac-github-mapping.md)
- [Git Collaboration Policy](workflows/git-collaboration-policy.md)
- [Workspace-to-DB Sync Contract](workflows/db-sync-contract.md)
- [Pre-Public Readiness Checklist](workflows/pre-public-readiness-checklist.md)
- [Manifest](manifest.yaml)
