# Categorical Foundations

## The mo:os Category 𝒞

mo:os is a category where:

| Concept             | In 𝒞                                                          |
| ------------------- | ------------------------------------------------------------- |
| Objects             | URNs (opaque identifiers, rows in `containers` table)         |
| Morphisms Hom(A, B) | Wires (rows in `wires` table, source_urn → target_urn)        |
| Composition g ∘ f   | Traversal: follow wire f from A to B, then wire g from B to C |
| Identity id_A       | Self-state: the node's own `state_payload` (no traversal)     |

This is **not** a classical category in the Set-theoretic sense. Objects have no
internal structure by definition (see `the_one_axiom.md`). What this category
provides is:

- A composition law (traversal of wires is associative)
- Identity morphisms (every container has a self-reference through its own state)
- A finite, enumerable set of objects (all containers in Postgres)
- A finite, enumerable set of morphisms (all wires in Postgres)

## Semi-Discrete with Recursion

The category is **semi-discrete**: most objects in the database have no wire
between them. The adjacency matrix is sparse. The wires that DO exist carry all
the system's meaning.

Recursion enters because containers can represent entire subgraphs. A workspace
container `urn:moos:infra:workspace:ffs0` has wires to its child containers. Each
child may have its own children. The graph is not acyclic in general — cycles are
permitted and meaningful (mutual dependencies).

## The Four Invariant Morphisms

There are exactly four natural transformations (see `the_four_morphisms.md`):

```
ADD    : ∅ → Container           (object creation)
LINK   : Container × Container → Wire  (morphism creation)
MUTATE : Container → Container   (endomorphism)
UNLINK : Wire → ∅               (morphism deletion)
```

EVERY operation in the system decomposes into a sequence of these four. There is
no fifth operation. Authentication checks, permission grants, data migrations,
schema changes — all are compositions of ADD/LINK/MUTATE/UNLINK.

## Hypergraph Structure

When multiple wires exist between the same pair of nodes (A, B), the graph
becomes a **hypergraph**. Each wire represents a distinct path — a different
morphism between the same objects.

```
Node A ──wire₁(CAN_HYDRATE)──→ Node B
       ──wire₂(OWNS)──────────→ Node B
       ──wire₃(SYNC_STATE)────→ Node B
```

This is not an edge case; it is the **general case**. The hypergraph stores
**all possible graphs as a superposition in one database**.

- A query collapses the superposition by selecting which edge types to traverse
- Breadth traversal = explore all edges between A→B (all relationship types)
- Depth traversal = follow one edge type all the way to leaves
- Each combination of edge-type selections produces a different projected graph
- The same containers + wires store: ownership trees, permission graphs, data flow
  DAGs, template hierarchies, and agent capability graphs simultaneously

This means the database does not store A graph. It stores THE graph — the
superposition of every possible subgraph derivable from those containers and wires.

## Functors

A functor F: 𝒞 → 𝒟 maps the mo:os category to another domain:

| Functor    | Source (𝒞)    | Target (𝒟)           | Purpose                         |
| ---------- | ------------- | -------------------- | ------------------------------- |
| FileSystem | manifest.yaml | wires table          | IDE artifact → graph edges      |
| UI_Lens    | containers    | React components     | Graph → visual representation   |
| Protocol   | wires         | HTTP/WS/gRPC routes  | Graph edges → network surface   |
| Embedding  | state_payload | vector space (ℝ¹⁵³⁶) | Content → semantic search space |

Functors are **separate from the graph**. They are code that reads the graph and
produces output in another domain. They are never stored AS metadata on graph
nodes (see `the_one_axiom.md` §3 — code separated from metadata).