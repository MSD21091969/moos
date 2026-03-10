# Hypergraph Implementation Approach

**Date:** 2026-03-09  
**Status:** Design analysis — no code changes proposed yet  
**Depends on:** ../doctrine/hypergraph.md (categorical justification)

---

## What the kernel already has

- **AX4 superposition**: $G_{\text{stored}} = \bigcup_{p \in \text{Ports}} G_p$ — the stored graph IS a hypergraph in König encoding
- **Ports as role markers**: port labels on Wires distinguish the _position_ a node occupies in a relation — this IS hyperedge incidence
- **Typed multi-relations**: the SemanticRegistry's PortTarget whitelist constrains which Kinds can participate in which roles — this IS a colored operad signature
- **Programs as composed rewrites**: `[]Envelope` with all-or-nothing = an atomic N-step rewrite rule

---

## What's genuinely missing

- **No hyperedge identity**: a Wire has no URN — you can't refer to "this relationship" as a first-class citizen, only to its endpoints
- **No N-ary atomic LINK**: creating a 5-node relationship requires 4+ separate LINK envelopes — the "hyperedge" is an emergent pattern, not a declared entity
- **No incidence query**: "give me all nodes participating in hyperedge $e$" requires reconstructing $e$ from multiple Wire queries — the kernel has no concept of "wires that belong to the same hyperedge"
- **No hyperedge-level MUTATE**: you can mutate a node's payload, but you can't mutate a relationship's properties atomically (Wire.Config exists but has no version, no CAS, no MUTATE envelope)

---

## Four categorical approaches evaluated

### A. Simplicial sets — $X: \Delta^{\text{op}} \to \mathbf{Set}$

- 0-simplices $X_0$ = nodes, 1-simplices $X_1$ = binary wires, $n$-simplices $X_n$ = $(n+1)$-ary relations
- Face maps $d_i: X_n \to X_{n-1}$ = "drop the $i$-th participant" (boundary)
- Degeneracy maps $s_i: X_n \to X_{n+1}$ = "repeat the $i$-th participant" (identity inclusion)
- **Pro**: standard ∞-categorical model — homotopy-coherent composition for free
- **Con**: massive conceptual overhead; face/degeneracy bookkeeping for every wire; simplicial identities are non-trivial invariants to maintain in a mutable store
- **Verdict**: overkill — the system doesn't need higher homotopies between relations

### B. Hypergraph cospans (Fong/Spivak) — morphisms are cospans $L \to G \leftarrow R$

- Composition via pushout: $A \to G_1 \leftarrow B$ and $B \to G_2 \leftarrow C$ compose to $A \to G_1 +_B G_2 \leftarrow C$
- **Pro**: compositional — build complex hypergraphs by gluing simpler ones along shared interfaces
- **Con**: requires fundamentally different state representation; cospans don't map onto append-only logs naturally; pushout computation is non-trivial at runtime
- **Verdict**: right theory for federated/distributed graph merging (MOR12 CAN_FEDERATE), wrong granularity for single-kernel mutations

### C. Colored operad — the ontology already IS one

- Colors = Kinds (OBJ01–OBJ13)
- Operations = morphism types (MOR01–MOR16), each with typed input/output signature
- An algebra over the operad = a valid graph state (one that satisfies all port constraints)
- A hyperedge IS an operation application: `OWNS(User, NodeContainer)` is a 2-ary operation
- **Pro**: ontology ALREADY defines this — `source_connections` and `target_connections` ARE operation arities; PortTarget list IS the typing discipline
- **Con**: operads encode the _schema_ of valid relations, not individual instances; still need a carrier structure for actual graph
- **Verdict**: use as the type theory, pair with another approach for runtime

### D. König with explicit hyperedge nodes — promote relationships to first-class objects

- A **HyperEdge** is a Node whose Kind declares it as relational
- Its Wires are incidence arcs — each Wire carries a Port labeling the role
- Creating a hyperedge = `ADD(he, Kind=HyperEdge)` + `LINK(he, role_1, v_1, member)` + ... + `LINK(he, role_k, v_k, member)`
- Already a Program — composed rewrite rule, atomic
- **Pro**: ZERO changes to the four NTs, ZERO changes to GraphState, ZERO changes to the store
- **Con**: hyperedge creation is multi-step (not single LINK); incidence queries require typed traversal
- **Verdict**: the DRY path — works within existing algebra

---

## Recommendation: D, typed by C

- **The operad (C) defines what hyperedges are legal** — which Kinds can participate in which roles, with what arities, under what port constraints
- **The König encoding (D) instantiates them** — a HyperEdge node + its incidence Wires is the runtime representation
- **The four NTs remain the only primitives** — no new rewrite rules needed
- **Programs become the hyperedge-level operation** — a Program that ADDs a HyperEdge node and LINKs all participants atomically IS the N-ary LINK

---

## What concretely changes

- **Ontology**: add HyperEdge as a Kind (or a Kind family — one per relation arity/type). Each HyperEdge Kind has N out-ports, one per role. PortTarget list on each out-port constrains which Kinds can fill that role.

- **Convention, not mechanism**: a hyperedge is **any Node whose Kind has > 1 out-port and whose semantic role is relational** (connecting others) rather than substantive (carrying domain payload). Declared in ontology, not enforced by special-case code.

- **Wire.Config gets versioning**: if hyperedge properties need MUTATE semantics, store them on the HyperEdge _node's_ Payload (already has version + CAS), not on Wire.Config. The HyperEdge node IS the relationship — its Payload IS the relationship's properties.

- **Incidence query**: `GET /state/traversal/outgoing/{hyperEdgeURN}` already returns all member nodes. Missing piece: `GET /state/nodes?kind=HyperEdge&participant={urn}` — "which hyperedges is this node part of?" This is an incoming-wire query filtered by source Kind.

- **Subobject classifier alignment**: in the presheaf topos $[\mathcal{O}^{\text{op}}, \mathbf{Set}]$, hyperedge nodes are objects in a subcategory. The characteristic morphism $\chi_{\text{HyperEdge}}: G \to \Omega$ classifies exactly the relational substructure. Queries that filter by HyperEdge Kinds compute this subobject.

---

## What does NOT change

- `GraphState` struct — still `Nodes map[URN]Node` + `Wires map[string]Wire`
- `EvaluateWithRegistry` — still the pure algebra map over the four NTs
- `Wire` type — still binary, still 4-tuple keyed
- `MorphismStore` — still append-only envelopes
- The catamorphism — `foldl Apply ∅ log[0..t]` remains the state reconstruction

---

## DPO rewriting frame (future — multiway system)

- When concurrent actors and branching histories are needed, the DPO construction applies:
  - $L$ = match pattern (which HyperEdge nodes and members must exist)
  - $K$ = interface (preserved — member nodes stay, old HyperEdge removed)
  - $R$ = replacement (new HyperEdge with updated incidence)
  - This is a Program: UNLINK old incidence, MUTATE or ADD new HyperEdge, LINK new incidence
- Confluence (Church-Rosser) = do two concurrent hyperedge rewrites on disjoint subgraphs commute? Yes, if node sets are disjoint — `Scope` field already partitions into independent causal cones
- Requires relaxing serial `RWMutex` to **scope-partitioned lock** where disjoint scopes proceed in parallel
- No data model changes — only concurrency changes

---

## Summary

- The hypergraph is already there (AX4, ports, König encoding)
- What's missing is **hyperedge identity** — a first-class node representing a relationship
- The fix is a **Kind convention** (operad-typed), not a structural change
- Programs already provide atomic N-ary operations
- The four NTs are sufficient — they are the primitive rewrite rules
- DPO rewriting and multiway branching are future extensions requiring concurrency changes, not data model changes
