# RBAC to GitHub Mapping

This document maps Collider roles to GitHub repository CRUD authority.

## Roles

### `superadmin`
- Full control of org/repo settings.
- Can manage teams, branch protections, and release policy.
- Final authority for merge and access escalations.

### `collider_admin`
- Maintainer/write authority in FFS1/FFS2/FFS3 repositories.
- Can create feature branches, open/merge PRs (subject to branch protections).
- Can maintain CI and operational docs in their assigned surfaces.

### `app_admin`
- Write authority scoped to app/frontend surfaces (primarily FFS3 and app folders).
- Can create feature branches and PRs for assigned applications.
- No global governance/repo-settings authority.

### `app_user`
- Read/clone only.
- No write/push/merge rights.

## Public Repo Model
- Repositories may be public for read access.
- Write operations remain role-gated by GitHub team permissions.
- Branch protection enforces review and quality gates.

## Recommended Team Model
- `superadmin` team: Admin on critical repos.
- `collider-admins` team: Maintain on FFS1/FFS2/FFS3.
- `app-admins` team: Write/Maintain on assigned app repos or paths.
- Public users: Read only.
