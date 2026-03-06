# Database Schema

## Ground Truth

Postgres is the single source of truth. There is no Redis layer, no in-memory
cache that holds authoritative state. The database holds the graph. Everything
else is a derived view.

## Core Tables

### containers

```sql
CREATE TABLE containers (
    urn         VARCHAR(512) PRIMARY KEY,
    type_id     VARCHAR(128) NOT NULL,
    parent_urn  VARCHAR(512) REFERENCES containers(urn),
    schema      JSONB DEFAULT '{}',
    state_payload JSONB DEFAULT '{}',
    permissions JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);
```

Objects in the category. Each row is a URN — an opaque identifier. The `urn` is
the ONLY identity. All other columns are data ON the node:

| Column        | Role                                                      |
| ------------- | --------------------------------------------------------- |
| type_id       | Category membership (e.g., 'auth_user', 'system_tool')    |
| parent_urn    | Convenience for tree traversal; redundant with OWNS wires |
| schema        | Port type declarations for this container                 |
| state_payload | Accumulated morphism result (materialized morphism cache) |
| permissions   | Node-level access metadata (which identity URNs own this) |

`state_payload` is NOT identity. It is a materialized view of the morphism log.
Delete it and replay morphisms to rebuild.

### wires

```sql
CREATE TABLE wires (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_urn  VARCHAR(512) NOT NULL REFERENCES containers(urn),
    target_urn  VARCHAR(512) NOT NULL REFERENCES containers(urn),
    source_port VARCHAR(128),
    target_port VARCHAR(128),
    wire_config JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source_urn, source_port, target_urn, target_port)
);
```

Morphisms in the category. Each row is an edge from source to target. The UNIQUE
constraint is on the 4-tuple (source, source_port, target, target_port), which
means **multiple wires between the same two containers are allowed** as long as
they use different port names.

This is the hypergraph: same container pair, different ports = different edges =
different graphs coexisting in one table.

| Column      | Role                                                       |
| ----------- | ---------------------------------------------------------- |
| source_urn  | Origin container                                           |
| target_urn  | Destination container                                      |
| source_port | Named output on source (e.g., 'owns', 'hydrate', 'exec')   |
| target_port | Named input on target                                      |
| wire_config | Edge rules: temporal scope, env scope, protocol, any JSONB |

`wire_config` carries the edge's access rules, temporal constraints, and
environment scoping. This is where runtime morphism switching happens:

```json
{
  "active_from": "2026-01-01T00:00:00Z",
  "active_until": null,
  "env": ["production", "staging"],
  "protocol": "http",
  "transitive": true
}
```

### morphism_log

```sql
CREATE TABLE morphism_log (
    id             BIGSERIAL PRIMARY KEY,
    morphism_type  VARCHAR(10) NOT NULL CHECK (morphism_type IN ('ADD','LINK','MUTATE','UNLINK')),
    actor_urn      VARCHAR(512) NOT NULL,
    target_urn     VARCHAR(512) NOT NULL,
    previous_state JSONB,
    new_state      JSONB,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);
```

Append-only audit trail. Every operation is logged. This is the canonical history.
`state_payload` on containers is derived from this log.

| Column         | Role                                 |
| -------------- | ------------------------------------ |
| morphism_type  | One of ADD / LINK / MUTATE / UNLINK  |
| actor_urn      | Who performed the operation          |
| target_urn     | Which container or wire was affected |
| previous_state | State before (NULL for ADD)          |
| new_state      | State after (NULL for UNLINK)        |

### container_embeddings

```sql
CREATE TABLE container_embeddings (
    id            BIGSERIAL PRIMARY KEY,
    container_urn VARCHAR(512) NOT NULL REFERENCES containers(urn),
    embedding     VECTOR(1536),
    created_at    TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ON container_embeddings USING hnsw (embedding vector_cosine_ops);
```

Functor output table. NOT graph data. Derived from `state_payload` via the
Embedding functor. Stored separately to maintain the separation principle.

## Hypergraph in Practice

Multiple wires between the same container pair:

```sql
-- Ownership wire
INSERT INTO wires (source_urn, target_urn, source_port)
VALUES ('urn:moos:identity:user:alice', 'urn:moos:data:doc:1', 'owns');

-- Read-access wire
INSERT INTO wires (source_urn, target_urn, source_port)
VALUES ('urn:moos:identity:user:alice', 'urn:moos:data:doc:1', 'can_read');

-- Write-access wire
INSERT INTO wires (source_urn, target_urn, source_port)
VALUES ('urn:moos:identity:user:alice', 'urn:moos:data:doc:1', 'can_write');
```

Three edges between Alice and Doc:1. Three different relationships. Three
different graphs projected from the same table. Query by port name to select
which graph to traverse.

## Schema as Container

Schemas are NOT functorial constraints enforced by the kernel. A schema is a
container in the graph:

```sql
INSERT INTO containers (urn, type_id, state_payload)
VALUES ('urn:moos:schema:workspace:v1', 'schema', '{"required": ["name"], ...}');
```

Validation is a LINK operation: wire a container to a schema container, then the
kernel checks the container's `state_payload` against the schema container's
`state_payload` on MUTATE. The schema is data in the graph, not code in the kernel.