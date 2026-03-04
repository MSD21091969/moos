# Go Kernel Bootstrap (Phase 1)

This workspace now includes a minimal Go kernel scaffold and migration CLI.

## Layout

- `cmd/kernel/main.go` — HTTP kernel bootstrap with `/health` and optional `/health/db`
- `cmd/migrate/main.go` — migration CLI (`up`, `status`)
- `internal/config/config.go` — env-based config loader
- `internal/migrate/runner.go` — SQL migration runner and `schema_migrations` tracking
- `go.mod` — Go module root (`github.com/collider/moos`)

## Run

From `moos/`:

```bash
go run ./cmd/kernel
```

Env vars:

- `MOOS_HTTP_ADDR` (default `:8080`)
- `MOOS_WS_ADDR` (default `:18789`)
- `DATABASE_URL` (required for DB health and migrations)
- `MOOS_MIGRATIONS_DIR` (default `./migrations`)
- `MOOS_MIGRATIONS_AUTO_APPLY` (default `false`; set `true`/`1`/`yes`/`on` to auto-apply on kernel start)
- `MOOS_BEARER_TOKEN` (optional; when set, all `/api/v1/*` routes require `Authorization: Bearer <token>`)
- `MOOS_MODEL_PROVIDER` (default `anthropic`; supports `anthropic` and `gemini`)
- `MOOS_SESSION_TTL` (default `30m`)
- `MOOS_SESSION_CLEANUP_EVERY` (default `1m`)
- `REDIS_URL` (optional; when set, session snapshots persist in Redis; fallback is in-memory)

When `DATABASE_URL` is set, `GET /health/db` checks DB connectivity.

Current minimal API surface (Phase 1 scaffold):

- `POST /api/v1/containers` creates a container record from JSON body.
- `GET /api/v1/containers/{urn}` returns a container record when present.
- `GET /api/v1/containers/{urn}/children` returns direct children for a parent URN.
- `GET /api/v1/containers/{urn}/tree` returns recursive subtree records rooted at `{urn}`.
- `PATCH /api/v1/containers/{urn}` mutates `kernel_json` with optimistic concurrency (`expected_version`).
- `POST /api/v1/containers/{urn}/wires` creates a wire from `{urn}` to `to_urn` using `from_port`/`to_port`.
- `DELETE /api/v1/containers/{urn}/wires` removes a wire identified by `from_port`, `to_urn`, `to_port`.
- `POST /api/v1/morphisms` applies a single typed morphism envelope (`ADD`, `LINK`, `MUTATE`, `UNLINK`).
- `GET /api/v1/morphisms/log` returns append-only morphism events (filters: `scope_urn`, `type`, `limit`).

Mutation operations now append to `morphism_log` using system provenance:

- `actor_urn = urn:moos:actor:system`
- `scope_urn = target container urn`
- `type` values: `ADD`, `LINK`, `MUTATE`, `UNLINK`

WebSocket compatibility surface (Phase 1 basic):

- JSON-RPC over WebSocket on `:18789`
- Methods:
	- `morphism.submit` with `{"envelope": {...}}` params
	- `session.create`
	- `session.send` with `{"session_id":"...","text":"..."}`
	- `session.list`
	- `session.close` with `{"session_id":"..."}`
- Stream notifications:
	- `stream.thinking`
	- `stream.morphism`
	- `stream.tool_result`
	- `stream.text_delta`
	- `stream.end`
	- `stream.error`

Phase 2 session runtime behavior (minimal implementation):

- Goroutine per session with event-driven queue processing.
- Session lifecycle via `session.create/list/close`.
- In-memory active state cache (`messages`) with TTL-based cleanup.
- Model dispatcher with provider adapter abstraction (`anthropic`/`gemini` stubs).
- Morphism extraction from structured JSON fences in model text.

## Run migrations

```bash
DATABASE_URL="postgres://user:pass@localhost:5432/moos?sslmode=disable" go run ./cmd/migrate --action up
```

Status:

```bash
DATABASE_URL="postgres://user:pass@localhost:5432/moos?sslmode=disable" go run ./cmd/migrate --action status
```

Optional flags:

- `--dir` migration folder path (default `./migrations`)
- `--database-url` explicit connection string

## Seed data

Phase 1 seed migration is included as:

- `migrations/0003_phase1_seed_data.sql`

It inserts idempotent baseline rows for:

- Root container: `urn:moos:root`
- App template: `urn:moos:app:2XZ`
- Identity containers: `urn:moos:user:admin`, `urn:moos:user:demo`

## Docker

Build and run the Phase 1 kernel + PostgreSQL stack:

```bash
docker compose up -d --build
```

Exposed ports:

- HTTP API: `8000` (container `8080`)
- WebSocket JSON-RPC: `18789`
