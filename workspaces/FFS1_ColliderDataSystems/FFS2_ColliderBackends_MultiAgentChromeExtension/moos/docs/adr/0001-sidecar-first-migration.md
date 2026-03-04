# ADR 0001: Sidecar-First Migration Strategy

- Status: Accepted
- Date: 2026-03-03

## Context

The current production-facing path for frontend applications depends on existing compatibility services and websocket behavior. We need to introduce the mo:os kernel incrementally without breaking current app behavior.

## Decision

Adopt a sidecar-first migration strategy:

1. Introduce new mo:os kernel contracts and persistence artifacts in parallel.
2. Keep existing compatibility runtime and websocket contract operational.
3. Route selected traffic through sidecar adapters first, then progressively increase coverage.

## Consequences

- Low migration risk for active frontend surfaces.
- Slightly higher short-term operational complexity due to dual paths.
- Enables reversible rollout during Phase 0 and Phase 1.
