# Kernel Architecture

## The Morphism Executor

The MOOS kernel is a morphism executor. It receives morphism requests (JSON
documents describing ADD/LINK/MUTATE/UNLINK operations), validates them against
the graph, and commits them to Postgres.

The kernel does not contain business logic. Business logic is encoded in the
graph — which containers exist, which wires connect them, what `wire_config`
rules govern traversal. The kernel only knows how to:

1. Parse a morphism request
2. Validate permissions (does this actor have a wire to this target?)
3. Execute the morphism (INSERT/UPDATE/DELETE on containers/wires)
4. Log the morphism (INSERT into morphism_log)
5. Return the result

## Pipeline: Event → Route → Dispatch → Transform → Commit

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Event   │───→│  Route   │───→│ Dispatch │───→│Transform │───→│  Commit  │
│ (JSON)   │    │ (match)  │    │ (select) │    │ (execute)│    │ (persist)│
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

### Event
An incoming morphism request — JSON body on HTTP, WebSocket message, or internal
pipeline call. Contains: `morphism_type`, `actor_urn`, `target_urn`, `payload`.

### Route
Match the target URN to a container. Verify the container exists. Resolve the
container's type and schema.

### Dispatch
Select the appropriate handler based on `morphism_type` (one of ADD/LINK/MUTATE/
UNLINK). The kernel reads the container's category from the graph — not from
hardcoded switch statements. Categories are containers. This means dispatching is
itself a graph traversal: "given this container type, which handler container is
wired to it?"

### Transform
Execute the morphism. For ADD: create a row in containers. For LINK: create a row
in wires. For MUTATE: update `state_payload` in containers. For UNLINK: delete a
row in wires. Each transform is one SQL transaction.

### Commit
Write to `morphism_log`. Return the result (new state, affected URNs, error if
validation failed). Emit event for any subscribed listeners (WebSocket push,
Prometheus counter increment).

## Go Implementation

- **Language**: Go 1.23+
- **Router**: Chi (HTTP) + gorilla/websocket (WS)
- **Database**: pgx/v5 direct (no ORM — the graph IS the model)
- **Metrics**: Prometheus counters per morphism type
- **Docker**: Single multi-stage container (`moos-kernel:dev`)

The kernel reads categories from the graph. It does not have Go types for
"workspace" or "model" or "tool". It has Go types for "container" and "wire" and
"morphism". Everything else is data in the graph.

## Kernel Does Not Store Code

The kernel binary contains:
- HTTP/WS server
- Morphism executor (the 4 operations)
- Permission checker (wire existence check)
- Morphism logger

The kernel binary does NOT contain:
- Business rules (these live in `wire_config` JSONB on wires)
- Schema definitions (these live in `schema` JSONB on containers)
- UI logic (this lives in FFS3 frontend)
- Agent reasoning (this lives in LLM provider calls)

This is the "code separated from metadata" principle applied to the runtime. The
kernel is a thin executor. The graph holds everything else.