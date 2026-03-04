# Pre-Public Readiness Checklist

Use this gate before switching repositories from private to public.

## 1) Access & Roles
- Confirm GitHub team mapping matches Collider roles:
  - `superadmin` → admin controls
  - `collider_admin` → maintain/write on FFS1/FFS2/FFS3
  - `app_admin` → scoped write on app surfaces (FFS3)
  - `app_user` → read/clone only
- Verify branch protections are enabled on default branches.

## 2) Repository Hygiene
- Confirm no secrets are committed.
- Confirm no machine-local credentials or tokens in tracked files.
- Confirm `.env` variants with secrets are ignored.
- Confirm local secret files are absent before publish (`.env`, `secrets/*.json`, `secrets/*.env`), except approved examples.
- Confirm generated/local runtime artifacts are ignored.

## 3) Context & Inheritance Integrity
- Validate all `.agent/manifest.yaml` include paths resolve.
- Validate all `includes.load` files exist.
- Validate all `exports` paths exist.
- Validate FFS0 → FFS1 → FFS2/FFS3 → ffs4/ffs5/ffs6 chain remains deterministic.

## 4) Runtime Contract Sanity
- Confirm MOOS compatibility surfaces are documented and reachable:
  - `:8000`, `:8001`, `:8004`, `:8080`, `:18789`
- Confirm FFS3 env requirements are documented:
  - `VITE_DATA_SERVER_URL`
  - `VITE_AGENT_RUNNER_URL`

## 5) Collaboration Flow
- Confirm feature-branch workflow is active for all admins.
- Confirm PR review requirements are enforced.
- Confirm required checks for merge are active.

## 6) DB Sync Contract
- Confirm workspace context synced to DB is IDE-focused and app-scoped.
- Confirm sync tooling ingests only approved context artifacts.
- Confirm public-read safety constraints are applied before sync.

## Decision
If any gate fails, do not flip visibility to public until remediated.
