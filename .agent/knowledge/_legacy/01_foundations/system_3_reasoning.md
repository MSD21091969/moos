# System 3 Reasoning

## Multi-Path DAG Reasoning

mo:os does not retrieve stored answers. It discovers paths through a graph.

Every question maps to: "starting from node X, what nodes are reachable through
edges of type T, and what is the accumulated state along the path?"

This is DAG reasoning — not keyword search, not vector similarity, not chain of
thought. The graph IS the reasoning structure.

## Linear vs Non-Linear Growth

Two growth rates govern the system:

### Linear: Nodes — O(n)

Adding containers is boring. Each container is an independent URN. One new
container costs one row in Postgres. Storage grows linearly. There is nothing
interesting about nodes in isolation.

### Non-Linear: Edges — O(n²) → k

Given n containers, the potential edges are n². But the actual edges are k, where
k ≪ n². The filtering from n² to k is done by rules:

- Permission rules (which users CAN wire to which containers)
- Schema rules (which port types are compatible)
- Temporal rules (which edges are active at time t)
- Environmental rules (which edges are active in environment env)

**The gap between n² and k IS the system's knowledge.** The rules that decide
which potential edges become actual edges ARE the intelligence of the system.

### Cost Implication

- Building the graph (discovery): expensive. Requires evaluating n² potential
  edges against rule sets. This is the "training" equivalent.
- Querying the graph (traversal): cheap. k is small, indexed, and cached.
  This is the "inference" equivalent.

## Morphism Log as Replayable History

The `morphism_log` table records every ADD/LINK/MUTATE/UNLINK with:

```
morphism_type | actor_urn | target_urn | previous_state | new_state | timestamp
```

This log is:

1. **Append-only** — never updated, never deleted
2. **Sufficient** — you can reconstruct any container's `state_payload` by
   replaying all MUTATE entries targeting that container, in order
3. **Auditable** — every state change has an actor and a timestamp
4. **Time-travel capable** — query the state of any node at any past timestamp
   by replaying the log up to that point

The `state_payload` on a container is a performance optimization — a materialized
view of `SELECT new_state FROM morphism_log WHERE target_urn = X ORDER BY id DESC
LIMIT 1`. If you delete all `state_payload` values, you lose nothing. Replay
rebuilds everything.

## Hypergraph Superposition Model

When a node has multiple edges to the same target, it stores parallel graph
versions:

```
Workspace ──CAN_HYDRATE(dev)──→ Model
           ──CAN_HYDRATE(prod)──→ Model
           ──CAN_HYDRATE(staging)──→ Model
```

Each edge represents a different traversal path. The database holds ALL paths
simultaneously — a superposition of all possible graphs.

- **Selecting edges = collapsing the superposition** — choosing which graph to
  instantiate at query time
- **Breadth traversal** = explore all edges from a node (enumerate versions)
- **Depth traversal** = follow one edge type to completion (resolve one version)
- **Task decomposition** = a node that fans out to many targets via different
  edge types, then fans back in — the shape of the subgraph IS the decomposition

Multiple edges between A→B means: there are multiple ways to get from A to B.
Each way is a different graph. All graphs coexist in one database. The query
decides which graph to project.

## Discovery vs Retrieval

| Aspect     | Discovery (building)         | Retrieval (querying)         |
| ---------- | ---------------------------- | ---------------------------- |
| Phase      | Design time / edge creation  | Runtime / edge traversal     |
| Cost       | O(n² × rules)                | O(k) where k = actual edges  |
| Knowledge  | Rules encode WHY edges exist | Paths encode WHAT is related |
| Bottleneck | Rule evaluation              | Cache locality               |
| Output     | New LINK morphisms           | Traversal results (state)    |

The system gets smarter by adding better rules (discovery), not by adding more
nodes (linear growth is boring) or more queries (retrieval is already fast).