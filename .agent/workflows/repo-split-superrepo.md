---
description: Execute hierarchical repo split with superrepos (FFS0, FFS1) and independent leaf repos (FFS2 backend, FFS3 frontend)
---

# Repo Split Runbook — Hierarchical Superrepos

This runbook preserves your current local experience while enabling independent access and branching.

## Target Repositories

1. `ffs0-factory-super` (superadmin)
   - Root orchestrator repo
   - Includes submodule: `workspaces/FFS1_ColliderDataSystems`
2. `ffs1-collider-super` (collider_admin)
   - Middle orchestrator repo
   - Includes submodules:
     - `FFS2_ColliderBackends_MultiAgentChromeExtension`
     - `FFS3_ColliderApplicationsFrontendServer`
3. `ffs2-collider-backend` (collider_admin)
   - Backend services + extension runtime stack
4. `ffs3-collider-frontend` (app_admin)
   - Nx/Vite frontend apps/libs

## Why this model

- Local checkout still feels like current nested structure.
- Teams clone at their level and push to their own repo.
- Access can be enforced by repository permissions (not only CODEOWNERS).

## Phase 0 — Freeze and Snapshot

1. Freeze merges in current monorepo.
2. Create a safety tag:

```powershell
git tag pre-split-2026-02-28
git push origin pre-split-2026-02-28
```

3. Create migration branch:

```powershell
git checkout -b chore/repo-split-bootstrap
```

## Phase 1 — Create leaf repos (FFS2, FFS3)

Create two new GitHub repositories and import history using subtree split.

```powershell
# Example from monorepo root
# FFS2 split branch
git subtree split --prefix=workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension -b split/ffs2

# FFS3 split branch
git subtree split --prefix=workspaces/FFS1_ColliderDataSystems/FFS3_ColliderApplicationsFrontendServer -b split/ffs3
```

Push each split branch to new remotes:

```powershell
git remote add ffs2 <NEW_FFS2_REPO_URL>
git push ffs2 split/ffs2:main

git remote add ffs3 <NEW_FFS3_REPO_URL>
git push ffs3 split/ffs3:main
```

## Phase 2 — Create FFS1 super repo

Initialize a new repo from current `workspaces/FFS1_ColliderDataSystems` content, then replace FFS2/FFS3 folders with submodules.

```powershell
# In fresh folder for ffs1 super
# Keep .agent, CLAUDE.md, governance docs
# Remove embedded FFS2/FFS3 code and add submodules

git submodule add <NEW_FFS2_REPO_URL> FFS2_ColliderBackends_MultiAgentChromeExtension
git submodule add <NEW_FFS3_REPO_URL> FFS3_ColliderApplicationsFrontendServer

git commit -m "chore: mount FFS2 and FFS3 as submodules"
```

## Phase 3 — Create FFS0 super repo

In the root repo, replace embedded `workspaces/FFS1_ColliderDataSystems` with submodule to `ffs1-collider-super`.

```powershell
git submodule add <NEW_FFS1_REPO_URL> workspaces/FFS1_ColliderDataSystems
git commit -m "chore: mount FFS1 as submodule"
```

## Phase 4 — Team onboarding flows

### Superadmin

```powershell
git clone --recurse-submodules <FFS0_SUPER_URL>
```

### Collider admin

```powershell
git clone --recurse-submodules <FFS1_SUPER_URL>
```

### Appadmin

```powershell
git clone <FFS3_REPO_URL>
```

## Branching policy

- Protected `main` in every repo.
- Work only in `feature/<scope>-<short-name>`.
- PR required with CODEOWNERS approval.
- Superrepos should update submodule pointers only after leaf-repo releases.

## Required GitHub protections

- Require PR before merge
- Require 1-2 reviews
- Require status checks (build/test/lint)
- Restrict who can push to `main`

## Access model (recommended)

- `team-superadmin`: admin on FFS0, maintain on FFS1/FFS2/FFS3
- `team-collider-admin`: write on FFS1+FFS2, read on FFS0, triage on FFS3
- `team-app-admin`: write on FFS3, read on FFS1+FFS2, no write on FFS0
- `team-users`: read only

## Validation checklist

- `git clone --recurse-submodules` works for FFS0 and FFS1
- FFS2 backend boots from FFS1 clone
- FFS3 frontend builds from FFS1 clone
- Submodule pointer bump workflow documented and tested
