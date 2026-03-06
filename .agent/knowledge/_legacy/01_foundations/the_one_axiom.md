# The One Axiom

> Everything is a URN with morphisms. There is nothing else.

## Statement

A node is an opaque identifier. It has no behavior, no methods, no internal
logic. It is a blind box with a label. The label is a URN. What the node "is"
emerges entirely from the edges that touch it — the morphisms it participates in.

```
Node = URN + Σ(morphisms applied from t₀ to t)
```

The `state_payload` on a node is not identity. It is the **accumulated result of
every MUTATE morphism** applied to that node across time. A performance cache — a
materialized view of the morphism log. You could delete it and reconstruct it by
replaying the log.

## Consequences

### 1. No Meta, Only Recursion

The prefix "meta" implies a level above. There are no levels. A category that
contains categories is recursive, not hierarchical. Metadata does not exist as a
separate concern — it lives on nodes as `state_payload`, which is itself the trace
of morphisms. Description, tags, labels, documentation — these are all
`state_payload` values on containers, governed by the same four morphisms as
everything else.

### 2. User Is a Label on a Blind Box

An authenticated user is a URN: `urn:moos:identity:user:alice`. Nothing more. What
Alice "can do" is the set of wires originating from her URN. What Alice "owns" is
the set of containers where an OWNS wire exists from her URN. What Alice "sees" is
the subgraph reachable by traversing her wires. Alice IS her edges. Remove all her
wires and she is an empty URN — a key with no graph.

All data follows this pattern. A document is a URN. A tool is a URN. A model is a
URN. A workspace is a URN. The user is no different from any other node — just
metadata on the node it owns, consisting of the edge(s) it uses to pass state.

### 3. Code Separated from Metadata

Functorial code (the actual logic — Go, TypeScript, SQL) lives in git-managed
files. Metadata (descriptions, tags, semantic labels, documentation) lives in
`state_payload` on graph nodes. These are **physically separated** to prevent a
failure mode: feeding deep-graph metadata to reasoning systems that consume words
without understanding the dependency structure those words were written for.

A Python function's docstring was written for THAT function's callers. Extracted
into a flat metadata pool and fed to graph reasoning over a 5×5×5 search space,
those words lose their structural binding. The docstring describes a dependency
relationship — but in the graph, dependencies don't exist. There are only edges.

Therefore: code is atomic. Each morphism is a standalone operation without internal
wiring or split edges. The semantic meaning lives in the graph structure (which
edges connect which nodes), not in natural-language descriptions attached to nodes.

### 4. Semantic Folders Start Empty

The semantic categories in the Collider graph (`knowledge/`, `rules/`,
`instructions/`) are empty containers from the start. Code gets loaded into them.
The folders impose structure (01_foundations → 02_architecture →
03_implementation → 04_developer_guide), but the structure is a DAG of
dependencies, not a hierarchy of importance.

### 5. Discovery vs Retrieval

Building the graph (discovering which edges should exist) is expensive — O(n²)
potential edges filtered to k actual edges by rules. Querying the graph (traversing
existing edges) is cheap — k is small and indexed.

The gap between n² and k IS the system's knowledge. The rules that filter potential
edges into actual edges ARE the intelligence.

## Formal Definition

```
Axiom: ∀ x ∈ System, x = (urn, Σ morphisms)
Where:
  urn    ∈ URN         (opaque identifier, the only identity)
  Σ      : Log → State (fold over morphism history produces current state)
  System = (Containers, Wires, MorphismLog)
```