---
description: Runtime-aware context layering rules for Collider sessions (anthropic, pi, pi-shadow)
activation: always
---

# Context Loading Rules

## Source of Truth

- Authoring source: `.agent/` filesystem content (seed input).
- Runtime canonical source: DB `NodeContainer` graph.
- Session delivery: composed context generated per session (`ContextSet`).

## Layering Order

1. Global/root skill context (e.g., `collider-workspace`)
2. Ancestor context (if `inherit_ancestors=true`, root-first)
3. Selected node contexts (`node_ids`, leaf-wins)
4. Session-time deltas (`ContextDelta` updates)

## Runtime Application

- `anthropic`: context rendered through `buildSystemPrompt(...)`.
- `pi`: context rendered by PI context extension state.
- `pi-shadow`: Anthropic stream returned; PI runs in shadow for KPI comparison.

## Skill Injection Policy

- Inject focused top-N model-invocable skills in detail.
- Summarize overflow skills under token budget limits.
- Keep deterministic selection behavior to avoid prompt drift.

## Transport Rules

- Bootstrap context: AgentRunner composition + gRPC bootstrap path.
- Tool execution: DataServer execution endpoint contract.
- Live updates: context delta injection per active session.

## Caching & Freshness

- Session cache is authoritative only for active session state.
- Re-composition required for new session bootstrap changes.
- Shadow KPI metrics are aggregated from runtime event streams; they do not alter session payloads.
