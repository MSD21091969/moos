# Cross-Service Validation Gates

Run from MOOS root:
- `pnpm nx run @moos/source:compat:build`
- `pnpm nx run @moos/source:compat:test`

Run frontend gate from FFS3 root:
- `pnpm nx build ffs4`
- `pnpm nx build ffs6`
