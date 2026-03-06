# Phase 5 MVP UX Baseline (MOOS sidepanel/viewer)

Date: 2026-03-05

## 1) What is running right now (dev compose)

Defined in `docker-compose.dev.yml`:

- `postgres` (pgvector/pg16) on host `5432`
- `redis` on host `6379`
- `kernel` (Go runtime) on host ports:
  - `8000 -> 8080` (HTTP compatibility API)
  - `8001 -> 8080` (tool compatibility alias)
  - `8004 -> 8080` (agent compatibility alias)
  - `18789 -> 18789` (WebSocket JSON-RPC)
- `frontend-deps` (one-shot `pnpm install` bootstrap)
- `sidepanel` (Vite app) on host `4201`
- `viewer` (Vite app) on host `4203`

### Clarification on services

In this dev stack, there are **not** separate long-running `data-server` and `tool-server` containers.
The **single `kernel` service** provides compatibility endpoints and is exposed on multiple host ports (`8000`, `8001`, `8004`).

## 2) Code ownership and runtime surfaces

- Kernel/API/WS runtime: `cmd/kernel/main.go`
- Container persistence and traversal: `internal/container/store.go`
- Shared surface diagnostics logic: `packages/shared-ui/src/index.ts`
- Sidepanel UI surface: `apps/sidepanel/src/app/app.tsx`
- Viewer UI surface: `apps/viewer/src/app/app.tsx`

## 3) Current UX intent (MVP lens)

### Sidepanel (4201)

Expected in MVP:

- Surface diagnostics panel (link/age/health, api status, probe)
- Workspace tree visualization (basic nested list)
- Tree source: `GET /api/v1/containers/{rootURN}/tree` (currently root `urn:moos:root`)

Current status:

- Tree is intentionally basic (list only, no graph interactions yet)
- This is a **placeholder + minimal lens**, not final Phase 5 UX

### Viewer (4203)

Expected in MVP:

- Surface diagnostics panel
- Bootstrap preview status from backend

Current status:

- Viewer is still scaffold-level diagnostics (no advanced domain UI yet)

## 4) Data model and storage location

Primary persistence is Postgres (`containers`, `wires`, `morphism_log`), accessed by `internal/container/store.go`.

Core record shape (`container.Record`):

- `URN` (primary logical identity)
- `ParentURN` (hierarchy)
- `Kind` (e.g., composite, identity, data)
- `InterfaceJSON` (presentation-facing payload)
- `KernelJSON` (runtime/internal payload)
- `PermissionsJSON` (access policy payload)
- `Version` (optimistic concurrency)

Graph connectivity:

- `wires` table links container ports (`from_container_urn/from_port -> to_container_urn/to_port`)

Mutation log:

- `morphism_log` append-only operations (`ADD`, `LINK`, `MUTATE`, `UNLINK`)

Seeded baseline nodes from migrations/docs:

- `urn:moos:root`
- `urn:moos:app:2XZ`
- `urn:moos:user:admin`
- `urn:moos:user:demo`

## 5) Operational hierarchy

### Runtime hierarchy

1. Infrastructure services (`postgres`, `redis`)
2. Kernel service (`main.go`) as single compatibility runtime
3. Frontend surfaces (`sidepanel`, `viewer`) consuming kernel HTTP/WS

### Container hierarchy (domain)

- Root composite container (`urn:moos:root`)
- Child containers via `parent_urn`
- Tree queries materialize hierarchy with recursive CTE (`TreeTraversal`)

## 6) Dataflow (request-level)

## 6.1 Sidepanel tree fetch

1. Browser loads `http://localhost:4201`
2. Sidepanel app calls `fetch('/moos-api/api/v1/containers/urn%3Amoos%3Aroot/tree')` with bearer header
3. Vite proxy forwards `/moos-api/*` to kernel (`http://kernel:8080`) and rewrites prefix
4. Kernel route `/api/v1/containers/{urn}/tree` executes `containerStore.TreeTraversal`
5. Store runs recursive SQL over `containers`
6. Flat records return to sidepanel
7. Sidepanel builds parent-child map and renders nested tree list

## 6.2 Surface diagnostics loop

Both sidepanel and viewer run `startSurfaceSync`:

- periodic `GET /moos-api/health`
- viewer calls bootstrap preview endpoint
- sidepanel shows data server and tree status

## 7) API/compatibility surface snapshot

From `cmd/kernel/main.go` and tests:

- `GET /health`
- `GET /health/db`
- `GET /metrics`
- `POST /api/v1/containers`
- `GET /api/v1/containers/{urn}`
- `GET /api/v1/containers/{urn}/children`
- `GET /api/v1/containers/{urn}/tree`
- `PATCH /api/v1/containers/{urn}`
- `POST|DELETE /api/v1/containers/{urn}/wires`
- `POST /api/v1/morphisms`
- `GET /api/v1/morphisms/log`
- WebSocket JSON-RPC on `:18789`

Auth model:

- `/api/v1/*` requires bearer when `MOOS_BEARER_TOKEN` is set

## 8) MVP completion assessment (current)

### Done

- Compose runtime stable for kernel + sidepanel + viewer
- Sidepanel and viewer reachable on `4201`/`4203`
- Sidepanel tree endpoint integrated and rendering seeded hierarchy
- Shared health parsing corrected for plain-text `/health`
- Same-origin Vite proxy path (`/moos-api`) avoids browser CORS/preflight issues

### Not done (still scaffold / next phase)

- Viewer is still a diagnostics scaffold (not full product surface)
- Sidepanel tree is basic list (no richer interactions yet)
- No dedicated e2e target suite for these surfaces in this local MOOS app pair
- UX polish/system styling still intentionally minimal

## 9) Suggested gate before Phase 5 implementation expansion

- Keep this baseline behavior as acceptance floor:
  - `4201` up and tree visible
  - `4203` up and diagnostics ticking
  - `8000/8001/8004` reachable
  - `/moos-api/health` and `/moos-api/api/v1/containers/{urn}/tree` return success
- Then move to Phase 5 feature build on top of this baseline rather than replacing runtime wiring again.
