# Phase 5 MVP Execution Checklist — PI Context + Tools Extensions

Status: Complete — Sections A-F and final validation gates passed  
Date: 2026-02-24  
Owner: FFS2 / NanoClawBridge  
Depends on: Phase 0-4 complete and compatibility gate green

---

## 0) Scope and MVP Boundaries

### In Scope (Phase 5 MVP)

1. PI session bootstrap from gRPC `GetBootstrap`.
2. PI context extension that injects structured workspace context.
3. PI tools extension that maps bootstrap tool schemas to DataServer execution API.
4. Provider/model resolver for `gemini`, `anthropic`, and optional `ollama`.
5. Minimal runtime widget (session identity + counts).
6. Basic integration tests that prove PI session creates and can execute one Collider tool.

### Out of Scope (deferred)

1. Full policy hooks and approvals (Phase 6).
2. WS event parity hardening suite (Phase 6).
3. Team extensions and pipeline runner (Phase 7).
4. Prompt-builder migration for Anthropic path (Phase 8).

---

## 1) Prerequisites Gate (Must Be True Before Starting)

- AgentRunner tests: green.
- DataServer `test_execution_api.py`: green.
- `ffs4` build: green.
- Proto changes from prior phases already regenerated and checked in.
- Anthropic runtime path remains default and healthy.

Quick commands:

```bash
# AgentRunner
cd workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/ColliderAgentRunner
uv run pytest -q

# DataServer contract test
cd ../ColliderDataServer
uv run pytest tests/test_execution_api.py -q

# FFS4 build
cd ../../FFS3_ColliderApplicationsFrontendServer
pnpm nx build ffs4 --verbose
```

---

## 1.1) Execution Progress (2026-02-24)

- [x] A. PI Adapter Skeleton Finalization
- [x] B. Context Extension
- [x] C. Tools Extension
- [x] D. Model Resolver
- [x] E. Widget Extension (Minimal)
- [x] F. Runtime Wiring

Validation snapshot:

- [x] `npm run build` (NanoClawBridge)
- [x] `npm test -- test/pi` (PI-focused suite)
- [x] `npm test` (full NanoClawBridge regression, incl. sdk/integration)

Final gate closure:

- [x] Added the two integration tests listed in Section 3.B with explicit gRPC bootstrap + real tool execution assertions.
- [x] Re-ran cross-service compatibility gate (AgentRunner/DataServer/ffs4) as final pre-Phase-6 checkpoint.

Cross-service validation snapshot:

- [x] `uv run pytest -q` (ColliderAgentRunner) → `53 passed, 1 skipped`
- [x] `uv run pytest tests/test_execution_api.py -q` (ColliderDataServer) → `6 passed`
- [x] `pnpm nx build ffs4 --verbose` (FFS3) → success

---

## 2) File-by-File Implementation Tasks

### A. PI Adapter Skeleton Finalization

- File: `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/NanoClawBridge/src/pi/pi-adapter.ts`
- Tasks:
  1. Ensure class implements `IAgentSession` contract.
  2. `createSession`: call gRPC `GetBootstrap`, initialize PI runtime with extension stack.
  3. `sendMessage`: route user input through PI runtime and yield canonical `AgentEvent` stream.
  4. `injectContext`: accept `ContextDelta` and update PI runtime session context.
  5. `terminateSession`: cleanup resources and internal state.

Acceptance:

- Compiles cleanly.
- Can create PI session without breaking Anthropic path.

### B. Context Extension

- File: `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/NanoClawBridge/src/pi/extensions/collider-context.ts`
- Tasks:
  1. Transform `BootstrapResponse` into structured workspace context blocks.
  2. Reuse existing ranking policy (top 2-3 detailed skills, summarized remainder).
  3. Include node/session identity metadata in extension state.
  4. Expose update method for context deltas.

Acceptance:

- PI runtime receives readable structured context.
- Token budget behavior follows existing top-N strategy.

### C. Tools Extension

- File: `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/NanoClawBridge/src/pi/extensions/collider-tools.ts`
- Tasks:
  1. Register PI tools from `bootstrap.tool_schemas`.
  2. Execute via DataServer endpoint `/api/v1/execution/tool/{name}`.
  3. Preserve argument pass-through and normalized result serialization.
  4. Handle transport/execution errors into runtime-safe tool errors.

Acceptance:

- At least one known Collider tool executes successfully from PI runtime.

### D. Model Resolver

- File: `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/NanoClawBridge/src/pi/model-resolver.ts`
- Tasks:
  1. Map `COLLIDER_AGENT_PROVIDER` and optional model override.
  2. Support `gemini` and `anthropic` first; keep optional `ollama` guarded.
  3. Fail fast with explicit error for unknown provider.

Acceptance:

- Runtime selection is deterministic and config-driven only.

### E. Widget Extension (Minimal)

- File: `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/NanoClawBridge/src/pi/extensions/collider-widget.ts`
- Tasks:
  1. Display session id (short), node scope, skill count, tool count.
  2. Keep UI passive (no actions, no policy logic).

Acceptance:

- Widget renders in PI session and does not affect behavior.

### F. Runtime Wiring

- Files:
  - `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/NanoClawBridge/src/session-manager.ts`
  - `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/NanoClawBridge/src/ws-bridge.ts`
- Tasks:
  1. Ensure feature flag routes to PI adapter for new sessions.
  2. Keep Anthropic path default/fallback.
  3. Preserve request identity threading (`role`, `appId`, `nodeIds`).

Acceptance:

- Toggleable runtime selection without frontend contract break.

---

## 3) Test Plan (MVP)

### A. Unit Tests

Create:

- `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/NanoClawBridge/test/pi/collider-context-extension.test.ts`
- `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/NanoClawBridge/test/pi/collider-tools-extension.test.ts`
- `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/NanoClawBridge/test/pi/model-resolver.test.ts`

Minimum assertions:

- Context ranking includes top-N and summaries remainder.
- Tool call builds correct DataServer URL + payload.
- Unknown provider throws deterministic error.

### B. Integration Tests

Create:

- `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/NanoClawBridge/test/pi/pi-session-bootstrap.integration.test.ts`
- `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/NanoClawBridge/test/pi/pi-tool-execution.integration.test.ts`

Minimum assertions:

- PI session can bootstrap from gRPC.
- PI session can execute one real Collider tool through DataServer.

### C. Smoke Validation

1. Start DataServer, GraphToolServer, AgentRunner, NanoClawBridge.
2. Set `COLLIDER_AGENT_RUNTIME=pi`.
3. Create session from ffs4 flow.
4. Send one tool-using prompt.
5. Confirm tool result and normal session completion.

---

## 4) Exit Criteria (Phase 5 Done)

All must pass:

1. PI runtime can create session and chat end-to-end from current UI flow.
2. PI runtime can execute at least one Collider tool via DataServer endpoint.
3. Anthropic runtime remains functional with no codepath regression.
4. New PI unit + integration tests are green in CI/local.
5. No schema/proto contract regressions introduced in AgentRunner/DataServer.

---

## 5) Fast Rollback Plan

If Phase 5 destabilizes runtime:

1. Set `COLLIDER_AGENT_RUNTIME=anthropic`.
2. Disable PI adapter selection branch in `session-manager.ts` if needed.
3. Keep PI files in tree but out of active path.
4. Re-run compatibility gate suite to confirm restore.

---

## 6) Suggested Commit Slices

1. `feat(pi): add model resolver and context/tools/widget extension skeletons`
2. `feat(pi): wire pi adapter into session manager runtime switch`
3. `test(pi): add unit tests for context/tools/model resolver`
4. `test(pi): add bootstrap and tool execution integration tests`
5. `docs(architecture): mark phase 5 checklist complete`

---

## 7) Operator Notes

- Keep implementation additive and feature-flagged.
- Avoid changing frontend payload/event contracts in this phase.
- Prefer deterministic behavior over optimization in MVP.
- Any policy/approval logic belongs to Phase 6, not Phase 5.
