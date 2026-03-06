# Codebase Improvements (2026-03-06)

This document proposes 10 concrete improvements based on current `moos` backend and `ffs4/ffs6` frontend code.

## 1. Make Morphism Apply Fully Transactional
- Problem: State write and morphism log append are separate operations.
- Risk: Partial success can mutate state without an audit log entry.
- Improve:
  - Wrap `Create/Link/Mutate/Unlink + AppendMorphismLog` in one DB transaction.
  - Add a store-level `ApplyEnvelopeTx(...)` path to enforce atomicity.
- References: `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/moos/internal/morphism/executor.go`, `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/moos/internal/container/store.go`

## 2. Enforce Secure-By-Default API Auth
- Problem: Auth is optional when `MOOS_BEARER_TOKEN` is unset.
- Risk: Endpoints can be unintentionally exposed without auth.
- Improve:
  - Require explicit `MOOS_AUTH_MODE` (`strict`, `disabled-local-dev`).
  - In strict mode, fail fast at startup if token/identity config is missing.
  - Add startup warning/error when binding non-localhost without auth.
- References: `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/moos/internal/config/config.go`, `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/moos/cmd/kernel/main.go`

## 3. Tighten WebSocket Origin and Admission Controls
- Problem: `CheckOrigin` currently returns true for all origins.
- Risk: Cross-origin connection abuse and CSWSH risk in browser contexts.
- Improve:
  - Add allowlisted origins in config.
  - Enforce per-connection auth/session checks.
  - Add rate limits on inbound messages per client/session.
- References: `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/moos/cmd/kernel/websocket_gateway.go`

## 4. Remove Hardcoded Default Credentials in Frontend
- Problem: Frontend defaults include `Sam/Sam` for MVP login.
- Risk: Accidental credential reuse and insecure defaults in deployed builds.
- Improve:
  - Remove default credential fallbacks.
  - Require env values only for non-interactive login flows.
  - Add build-time checks that fail if placeholder credentials are present.
- References: `workspaces/FFS1_ColliderDataSystems/FFS3_ColliderApplicationsFrontendServer/apps/ffs4/src/lib/api.ts`

## 5. Replace Implicit Re-Login on 401 with Token Refresh Strategy
- Problem: `authedFetch` retries by re-running login with configured credentials.
- Risk: Hidden auth behavior, fragile session handling, and confusing failures.
- Improve:
  - Introduce explicit refresh-token flow.
  - If refresh fails, force sign-out and route to login screen.
  - Add retry limits and typed error handling.
- References: `workspaces/FFS1_ColliderDataSystems/FFS3_ColliderApplicationsFrontendServer/apps/ffs4/src/lib/api.ts`

## 6. Harden WebSocket Client Reconnect and Timeout Handling
- Problem: Reconnect is fixed 3s; pending RPC entries can accumulate on disconnect; timeout handling is per-call timer only.
- Risk: Memory growth and noisy reconnect loops under unstable networks.
- Improve:
  - Add exponential backoff + jitter and max retry window.
  - Reject/flush `pending` map on close/disconnect.
  - Centralize request timeout/cancellation strategy.
- References: `workspaces/FFS1_ColliderDataSystems/FFS3_ColliderApplicationsFrontendServer/apps/ffs4/src/lib/nanoclaw-client.ts`

## 7. Reduce `any`/`unknown` at API and Event Boundaries
- Problem: Many event/morphism paths are weakly typed.
- Risk: Runtime schema drift and hard-to-debug UI behavior.
- Improve:
  - Introduce shared runtime schemas (e.g., Zod) for WS and REST payloads.
  - Validate incoming envelope/event frames before state updates.
  - Replace broad `unknown[]` and `Record<string, unknown>` with discriminated unions.
- References: `workspaces/FFS1_ColliderDataSystems/FFS3_ColliderApplicationsFrontendServer/apps/ffs4/src/lib/nanoclaw-client.ts`, `workspaces/FFS1_ColliderDataSystems/FFS3_ColliderApplicationsFrontendServer/apps/ffs4/src/stores/graphStore.ts`

## 8. Eliminate `context.Background()` in Session Event Processing
- Problem: Session manager uses background contexts for executor/tool operations.
- Risk: Missing cancellation, runaway tasks, and weak request lifecycle control.
- Improve:
  - Thread request/session-scoped contexts into executor/tool dispatch.
  - Add explicit per-operation deadlines and cancellation propagation.
  - Emit structured timeout vs cancellation errors separately.
- References: `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/moos/internal/session/manager.go`

## 9. Expand Tool Policy from Name/Size Checks to Capability Policy
- Problem: Tool policy mostly checks input size and blocked prefixes.
- Risk: Insufficient governance controls for high-risk tool calls.
- Improve:
  - Add allow/deny by actor role, tool name, and argument patterns.
  - Add per-tool timeout/memory ceilings.
  - Add auditable policy decision logging.
- References: `workspaces/FFS1_ColliderDataSystems/FFS2_ColliderBackends_MultiAgentChromeExtension/moos/internal/tool/policy.go`

## 10. Strengthen Test Coverage for Frontend State and Auth Flows
- Problem: Backend has many `*_test.go` files; frontend `ffs4/ffs6` has little/no colocated test coverage for API/session/WS stores.
- Risk: Regressions in message streaming, auth retry, and morphism application logic.
- Improve:
  - Add unit tests for `api.ts`, `sessionStore.ts`, and `nanoclaw-client.ts`.
  - Add integration tests for graph morphism apply behavior.
  - Add scenario tests for auth-expiry and reconnect.
- References: `workspaces/FFS1_ColliderDataSystems/FFS3_ColliderApplicationsFrontendServer/apps/ffs4/src/lib/api.ts`, `workspaces/FFS1_ColliderDataSystems/FFS3_ColliderApplicationsFrontendServer/apps/ffs4/src/stores/sessionStore.ts`, `workspaces/FFS1_ColliderDataSystems/FFS3_ColliderApplicationsFrontendServer/apps/ffs4/src/lib/nanoclaw-client.ts`

## Quick Wins (1-2 Days)

These are high-impact, low-complexity fixes that can be delivered quickly.

1. Secure WebSocket origin checks.
   - Implement origin allowlist in `websocket_gateway.go`.
2. Remove default MVP credentials from frontend fallback paths.
   - Eliminate `Sam/Sam` defaults in `apps/ffs4/src/lib/api.ts`.
3. Flush pending RPC map on socket close.
   - Prevent memory growth in `apps/ffs4/src/lib/nanoclaw-client.ts`.
4. Add startup warning/error when running without auth on non-localhost.
   - Add guardrails in `internal/config/config.go` and `cmd/kernel/main.go`.
5. Add unit tests for frontend session/auth behavior.
   - Cover `api.ts`, `sessionStore.ts`, and reconnect path in `nanoclaw-client.ts`.

## Phased Implementation Plan

### Phase 1 - Security and Reliability Baseline
- Scope: Items 2, 3, 4, 6 (partial), 10 (partial)
- Goal: Eliminate insecure defaults and fragile connection/session behavior.
- Deliverables:
  - Auth mode guardrails (`strict` vs `disabled-local-dev`).
  - WebSocket origin allowlist and admission checks.
  - Frontend credentials fallback removal.
  - Reconnect/backoff and pending-map cleanup.
  - Initial frontend tests for auth/reconnect.

### Phase 2 - Transactional Consistency and Execution Control
- Scope: Items 1, 8, 9
- Goal: Make mutation/logging atomic and execution paths cancel-safe/policy-safe.
- Deliverables:
  - Transactional morphism apply path in store layer.
  - Session-scoped context propagation for executor/tool dispatch.
  - Capability-driven tool policy (role/tool/arg constraints + decision logs).

### Phase 3 - Type and Contract Hardening
- Scope: Items 5, 7, 10 (remaining)
- Goal: Reduce runtime drift and improve maintainability at API/event boundaries.
- Deliverables:
  - Explicit token refresh flow and typed auth error handling.
  - Runtime schema validation for REST/WS payloads.
  - Broader frontend integration tests for morphism/state transitions.

### Phase 4 - Validation and Rollout
- Scope: Cross-cutting validation for all completed items.
- Goal: De-risk deployment and lock in quality.
- Deliverables:
  - Regression suite run + targeted load tests for WS and session flows.
  - Security validation for auth/origin/policy controls.
  - Operational dashboards/alerts for reconnect churn, auth failures, and policy denials.

## Effort/Risk Matrix

| ID  | Improvement (Short Name)                            | Effort | Risk if Delayed | Priority |
| --- | --------------------------------------------------- | ------ | --------------- | -------- |
| 1   | Transactional morphism apply                        | M      | High            | P0       |
| 2   | Secure-by-default API auth                          | S      | High            | P0       |
| 3   | WebSocket origin/admission control                  | S      | High            | P0       |
| 4   | Remove default credentials                          | S      | High            | P0       |
| 5   | Replace implicit re-login flow                      | M      | Medium          | P1       |
| 6   | Harden WS reconnect/timeout                         | S      | Medium          | P1       |
| 7   | Reduce `any`/`unknown` boundaries                   | M      | Medium          | P1       |
| 8   | Remove `context.Background()` in session processing | M      | Medium          | P1       |
| 9   | Expand tool capability policy                       | M      | High            | P0       |
| 10  | Strengthen frontend test coverage                   | M      | Medium          | P1       |

Legend:
- Effort: `S` (< 1 sprint), `M` (1 sprint), `L` (> 1 sprint)
- Priority: `P0` urgent, `P1` next, `P2` later
