# Workspace-to-DB Sync Contract

This contract defines how local workspaces feed IDE-focused context into DB containers.

## Source of Truth
- Code and `.agent` context are authored in workspace folders.
- Sync process publishes selected context to DB containers for application runtime use.

## Required Properties
- Synced context is IDE-focused and application-scoped.
- Inheritance remains deterministic (FFS0 → FFS1 → FFS2/FFS3 → app stubs).
- No secrets are committed or synced from tracked files.

## Sync Flow
1. Admins update workspace code/context on feature branches.
2. Changes are reviewed and merged in GitHub.
3. Sync tooling ingests workspace context into DB container nodes.
4. Applications (including 1xz surfaces) consume container context.

## Validation Gates
- Includes/exports paths resolve.
- Role permissions remain aligned with GitHub team policy.
- Runtime contract docs still match active ports and services.
