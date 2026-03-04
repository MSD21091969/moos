# ADR 0002: Persistence Baseline with PostgreSQL JSONB + pgvector

- Status: Accepted
- Date: 2026-03-03

## Context

Phase 0 needs durable storage for containers, graph wiring, and semantic retrieval without adding multiple infrastructure dependencies.

## Decision

Use PostgreSQL as the single persistence baseline with:

- JSONB for container interface/kernel/permissions payloads.
- Relational edge table (`wires`) for explicit port-to-port graph links.
- `morphism_log` as append-only operation history.
- `pgvector` for embedding storage and ANN search.

## Consequences

- Single operational datastore in early phases.
- Straightforward SQL observability and migration tooling.
- Embedding dimension is fixed at schema level in Phase 0 and may require migration if model dimensions change.
