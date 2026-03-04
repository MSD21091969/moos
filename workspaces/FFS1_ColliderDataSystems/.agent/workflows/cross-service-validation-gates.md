# Cross-Service Validation Gates

## Backend (MOOS — Go)

Run from MOOS root (`FFS2_.../moos/`):
- `go test ./...` — 46 tests, 94% model coverage
- `pnpm nx run @moos/source:compat:build`
- `pnpm nx run @moos/source:compat:test`

## Frontend (FFS3)

Run from FFS3 root:
- `pnpm nx test ffs4` — 22 vitest tests (graphStore morphisms)
- `pnpm nx build ffs4`
- `pnpm nx build ffs6`
- `pnpm nx run ffs6:typecheck`

## Full Gate (CI equivalent)

1. Go tests pass
2. FFS4 vitest pass
3. FFS6 typecheck pass
4. FFS4 + FFS6 build succeed
