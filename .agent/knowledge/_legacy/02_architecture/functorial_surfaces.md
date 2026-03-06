# Functorial Surfaces

## What Is a Surface?

A surface is a functor — a structure-preserving map from the mo:os category 𝒞 to
another domain 𝒟. It reads containers and wires and produces output in a target
system (filesystem, browser, network, vector space).

Surfaces are **code, not data**. They are implemented in Go, TypeScript, or SQL.
They are NEVER stored as metadata on graph nodes. This is the physical separation
principle: functorial (possibly neural-symbolic) code is kept in git-managed
source files, while metadata lives in `state_payload` on containers in Postgres.

Why separate? Because functorial code operates on graph STRUCTURE (which edges
connect which nodes), while metadata describes graph CONTENT (what text or config a
node holds). Mixing them causes a failure mode: metadata written for one structural
context gets consumed in a different context where the structural assumptions no
longer hold.

## Active Surfaces

### FileSystem Functor

```
F_fs : manifest.yaml → wires table
```

Maps IDE workspace artifacts (files in `.agent/`) to graph edges. The manifest
declares which knowledge, rules, instructions, and configs exist for a workspace.
Each declaration becomes a CAN_HYDRATE wire from the workspace container to the
declared artifact container.

**Direction**: codebase → graph (import)

### UI_Lens Functor

```
F_ui : containers × wires → React component tree
```

Maps graph structure to visual representation. Implemented in FFS3/FFS4 using
@xyflow/react. Each container becomes a node in XYFlow. Each wire becomes an edge.
The functor preserves composition: if A→B→C in the graph, the visual shows the
same path.

**Direction**: graph → browser (render)

### Protocol Functor

```
F_proto : wires → HTTP routes ∪ WS channels ∪ gRPC services
```

Maps graph edges to network surfaces. A wire with `wire_config.protocol = "http"`
exposes an HTTP endpoint. A wire with `wire_config.protocol = "ws"` opens a
WebSocket channel. The MOOS kernel uses this functor to construct its router at
startup — reading wires from the graph to determine which endpoints to serve.

**Direction**: graph → network (expose)

### Embedding Functor

```
F_embed : state_payload → ℝ¹⁵³⁶ (pgvector)
```

Maps container content to a continuous vector space for approximate search. This
is the RAG surface. It does not replace graph traversal — it provides a
complementary discovery mechanism when the user does not know which node to start
from.

**Direction**: graph → vector space (embed)

## Functor Composition

Functors can compose:

```
F_ui ∘ F_fs : manifest.yaml → React component tree
```

This is how the IDE viewer works: read the manifest (FileSystem functor), then
render the result (UI_Lens functor). Composing functors preserves structure at
each step — the intermediate graph representation acts as the common language.

## Anti-Pattern: Functor-as-Metadata

Storing functor output (rendered HTML, computed embeddings, formatted API specs)
back as `state_payload` on containers breaks the separation principle. The graph
should contain source data. Functor outputs should be computed on demand or cached
in dedicated tables (like `container_embeddings`), never mixed into the graph's
own content.