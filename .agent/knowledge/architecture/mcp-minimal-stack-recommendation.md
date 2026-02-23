# MCP Minimal Stack Recommendation (Collider)

Date: 2026-02-23

## Goal

Use a small, high-signal MCP stack that supports your recursive graph/container architecture without flooding context.

## Recommended active now

1. `collider-tools` (already active)
   - Source: `http://localhost:8001/mcp/sse`
   - Purpose: execute Collider-registered tools from graph runtime.

## Recommended next (enable one at a time)

2. `filesystem-workspace`
   - Scoped to workspace roots only.
   - Purpose: safe file-level introspection/edit operations.

3. `git-root`
   - Scoped to `D:/FFS0_Factory` repo.
   - Purpose: diff/history/provenance; crucial for debugging harness regressions.

4. `sqlite-collider`
   - Scoped to Collider DB path.
   - Purpose: inspect node/container/permission records during composition debugging.

5. `http-fetch`
   - Purpose: inspect API payloads/contracts and docs from internal/external endpoints.

## Defer for now

- MCP `prompts/resources` exposure for skills/graph topology.
- Keep this for phase-2+ after runtime adapter contract stabilizes.

## Why this order

- Maintains current production path.
- Adds visibility first, then diagnostics, then interoperability.
- Avoids overloading the agent with duplicate capabilities.

## Files

- Active config: `.vscode/mcp.json`
- Staged template: `.vscode/mcp.recommended.jsonc`

## Operational rule

Enable one server, run validation, keep or rollback. Do not activate all servers at once.
