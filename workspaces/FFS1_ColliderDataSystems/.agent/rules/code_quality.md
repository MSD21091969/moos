# Code Quality

## General

- Keep changes minimal and contract-preserving.
- Prefer deterministic includes/exports in manifest wiring.
- Update docs when runtime ownership changes.

## Go (MOOS)

- Follow standard Go project layout (`cmd/`, `internal/`, `apps/`).
- Use interfaces for testability (e.g. `Adapter` interface, injectable `http.Client`).
- Maintain test coverage ≥90% on core packages (`internal/model`).
- Use `go test ./...` from MOOS root to validate.

## TypeScript (FFS3)

- Strict TypeScript — no `any` without justification.
- Zustand stores must be pure state + actions, no side effects in store definitions.
- Vitest tests colocated with source (`*.spec.ts` next to `*.ts`).
- Run `pnpm nx run ffs6:typecheck` before commits.
