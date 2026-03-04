# ADR 0003: Freeze Morphism Names for Compatibility

- Status: Accepted
- Date: 2026-03-03

## Context

The current and future runtime contracts rely on a stable mutation vocabulary used across services, logs, and UI projections.

## Decision

Freeze the Phase 0 morphism names as:

- `ADD`
- `LINK`
- `MUTATE`
- `UNLINK`

These names are canonical for protocol payloads, persisted logs, and compatibility adapters.

## Consequences

- Stable naming across sidecar and compatibility layers.
- Reduces migration risk for websocket event consumers.
- Future semantic expansion should be implemented through payload evolution, not renaming these operations.
