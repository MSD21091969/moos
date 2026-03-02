# Git Collaboration Policy

## Branching
- All implementation work occurs on feature branches.
- Branch naming: `feat/<scope>-<short>`, `fix/<scope>-<short>`, `chore/<scope>-<short>`.

## Pull Requests
- PR required for merge to protected branches.
- At least one reviewer from the owning admin group.
- Keep PR scope small and traceable to a single intent.

## Merge Rules
- No direct pushes to protected branches.
- Required checks must pass before merge.
- Use conventional commits in PR titles or squash commit messages.

## Ownership
- FFS0: governance/control-plane docs and contracts.
- FFS1: shared contracts and inheritance provider.
- FFS2: backend compatibility runtime.
- FFS3: frontend applications and app-level contexts.
