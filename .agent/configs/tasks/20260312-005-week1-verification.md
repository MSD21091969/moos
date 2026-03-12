# Task: Week 1 Verification — Full Boot Test

**Status:** pending
**Priority:** p0
**Delegated:** 2026-03-12
**Depends on:** 001, 002, 003, 004

## Objective

Verify the complete Week 1 deliverable works end-to-end.

## Verification Steps

1. Clean state (remove morphism log)
2. Build: `cd platform/kernel && go build ./cmd/moos`
3. Boot: `./moos --kb <kb-path> --hydrate`
4. `GET /healthz` — node_count ≥ 50, wire_count ≥ 80
5. `GET /state/nodes` — all 21 type_ids present
6. `GET /log` — ≥ 50 entries
7. Restart with existing log — same counts (idempotent replay)
8. `GET /semantics/registry` — 21 kinds loaded
9. `go test ./...` — all green
10. `go test -race ./...` — no data races

## Deliverable

Commit: `feat: week 1 complete — KB-aware boot + full hydration [task:20260312-005]`
Push to main. Fill in Notes from Execution below.

## Notes from Execution

