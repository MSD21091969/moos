# Conversation State Rehydration

Use this runbook to restore workspace context for a new coding session.

## Order
1. Read `D:\FFS0_Factory\CLAUDE.md`.
2. Read the active workspace `CLAUDE.md`.
3. Read that workspace `.agent/index.md`.
4. Load `.agent/manifest.yaml` and resolve `includes` and `exports`.

## Runtime Baseline
- Active backend compatibility runtime: `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/moos`
- FFS3 depends on compatibility surfaces at `:8000`, `:8004`, `:18789`

## Validation
- Ensure all `includes.load` files exist.
- Ensure all manifest `exports` paths exist.
- Confirm active run commands from FFS1 workflow docs.