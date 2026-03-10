# The moos Hypergraph — Why Binary Wires Encode a Hypergraph

**Date:** 2026-03-09  
**Context:** Corrective analysis after initial mischaracterization of the kernel graph model as a "directed multigraph, not a hypergraph."

---

## AX4 already says it

Axiom AX4 — `Hypergraph_Superposition` — states:

> "DB stores THE graph — superposition of all projected graphs. Multiple wires between same (A,B) via different ports. UNIQUE on 4-tuple. **Query collapses superposition.**"

The formal statement: $G_{\text{stored}} = \bigcup_{p \in \text{Ports}} G_p$

This is not a directed multigraph. It is the **superposition of all port-typed graphs** into a single structure. A query with a port filter _collapses_ the superposition into a projected subgraph — the same way a measurement collapses a quantum state. The stored object is genuinely a hypergraph; what the Go kernel exposes is its **König representation** (incidence encoding), which happens to use binary wires as notation.

---

## The König presentation is not the thing

Every hypergraph $H = (V, E)$ where $E \subseteq \mathcal{P}(V)$ has a **bipartite incidence graph** $G_H$:

- For each hyperedge $e = \{v_1, \ldots, v_k\} \in E$, create a bipartite node $e$ and binary edges $e \to v_i$ for each incident vertex.

In the moos model:

- A **Node** with Kind K and ports $\{p_1, p_2, \ldots, p_n\}$ each wired to different target nodes **IS** the hyperedge node in the König encoding.
- The **Wires** from those ports to their targets **ARE** the incidence arcs.
- The **Port labels** ARE the position indexes in the hyperedge — they distinguish the role each vertex plays.

So when a `NodeContainer` has `LINK_NODES`, `SYNC_ACTIVE_STATE` as source connections and `OWNS`, `CAN_HYDRATE`, `LINK_NODES`, `ADD_NODE_CONTAINER` as target connections — that's a **6-arity typed hyperedge signature**. The binary Wire representation is an encoding detail, not the mathematical structure.

The claim "it's a directed multigraph, not a hypergraph" confused the **presentation** for the **thing presented**.

---

## Wolfram's hypergraph rewriting — categorically

In the Wolfram Physics Project, the universe is a hypergraph evolving by **rules rewriting**. A rule like:

$$\{\{x, y\}, \{y, z\}\} \to \{\{x, y\}, \{y, w\}, \{w, z\}\}$$

is a **span in the category of hypergraphs**:

$$L \xleftarrow{\iota} K \xrightarrow{\rho} R$$

Where:

- $L$ = the **left-hand side** (pattern to match): two hyperedges sharing vertex $y$
- $K$ = the **interface** (preserved structure): the shared vertices/edges
- $R$ = the **right-hand side** (replacement): three hyperedges with new vertex $w$

Application to a host hypergraph $G$ uses the **Double Pushout (DPO) construction**:

$$L \xleftarrow{} K \xrightarrow{} R$$
$$\downarrow m \quad\quad \downarrow \quad\quad \downarrow$$
$$G \xleftarrow{} D \xrightarrow{} H$$

where $m: L \to G$ is the pattern match, $D$ is the context (what remains after removing $L \setminus K$), and $H$ is the rewritten hypergraph.

**The key Wolfram insight**: from the same initial state, multiple matches of the same rule can exist at different locations. Applying all of them generates a **multiway system** — a branching graph of all possible evolution histories. The **causal graph** tracks which rule applications depend on which prior ones.

**Categorically**: the multiway system is a presheaf on the causal partial order — it is a functor $\mathcal{M}: \mathbf{Causal}^{\text{op}} \to \mathbf{Hyp}$ where $\mathbf{Hyp}$ is the category of hypergraphs.

---

## Mapping onto the moos model

The four invariant NTs are **already rewrite rules** — they just happen to be maximally atomic:

| NT         | As Wolfram-style rewrite rule                                                                                                |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **ADD**    | $\emptyset \to \{v\}$ — introduce a new vertex into the hypergraph                                                           |
| **LINK**   | $\{v_1, v_2\} \to \{v_1, v_2, e(v_1 \xrightarrow{p_s} v_2, p_t)\}$ — introduce a labeled hyperedge between existing vertices |
| **MUTATE** | $\{v[\sigma]\} \to \{v[\sigma']\}$ — rewrite a vertex label (payload) in place, with CAS guard as the match condition        |
| **UNLINK** | $\{e(v_1 \xrightarrow{p_s} v_2, p_t)\} \to \{v_1, v_2\}$ — remove a hyperedge                                                |

These are **primitive rewrite rules** from which all 16 ontology morphisms (MOR01–MOR16) are composed. Look at the decompositions:

- `MOR05 ADD_NODE_CONTAINER = ADD(container) ; LINK(parent, 'owns', container, 'child')` — two primitive rewrites composed sequentially
- `MOR01 OWNS = LINK(owner, 'owns', target, 'child')` — single primitive rewrite
- `MOR03 PRE_FLIGHT_CONFIG = MUTATE(surface, config_payload)` — single primitive rewrite

The `Program` type (ordered `[]Envelope` with all-or-nothing semantics) is exactly a **composed rewrite rule** — a span $L \leftarrow K \rightarrow R$ where $L$ is the pre-match condition (all `expected_version` checks, node existence), $K$ is the preserved context, and $R$ is the fully rewritten state.

So the kernel IS a hypergraph rewriting system. The catamorphism IS the sequential application of rewrite rules. The morphism log IS the causal trace.

---

## What's missing is the multiway system

Where the moos kernel diverges from Wolfram is that it **serializes** rule application. The `sync.RWMutex` forces a total order on morphisms — there is exactly one evolution path, not a branching multiway system.

This is a design choice, not a limitation of the model. AX3 says `state(x, t) = fold(morphism\_log(x, 0..t))` — the fold requires a linear sequence. But categorically, nothing prevents:

1. A **branching log** where concurrent morphisms from different actors produce multiple candidate states
2. A **confluence check** — do the branches produce the same result regardless of order? (this is the Church-Rosser property from term rewriting)
3. A **causal partial order** instead of a total order — morphisms that touch disjoint subgraphs commute; those that touch overlapping subgraphs have causal dependency

The `Scope` field on `Envelope` already hints at this — it partitions morphisms into independent causal cones. If morphisms in `Scope A` and `Scope B` touch disjoint node sets, they commute and can be applied in parallel. The partial order is implicit in the port/ownership topology.

---

## Hyperdimensional Computing (HDC) — the representation layer

The ontology already defines this as EXT01:

> $\mathcal{H}$ — symmetric monoidal, semiadditive. Objects: hypervectors in $\{-1, +1\}^d$. Monoidal product: bind $\otimes$ (element-wise XOR for BSC). Coproduct: bundle $\oplus$ (element-wise addition, biproduct). Endofunctor: permute $\pi$ (circular shift).

This is a **monoidal category** with three operations that map directly to hypergraph structure:

| HDC operation       | Category structure                     | Hypergraph interpretation                                                                                                                                           |
| ------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Bind** $\otimes$  | Monoidal product in $\mathcal{H}$      | Compose two hyperedge representations into a single relational vector — the vector for "A OWNS B" is $\text{bind}(\vec{A}, \text{perm}(\vec{B}))$                   |
| **Bundle** $\oplus$ | Coproduct (biproduct) in $\mathcal{H}$ | Superpose multiple relations into a single representation — the vector for "everything A connects to" is $\bigoplus_i \text{bind}(\vec{A}, \text{perm}(\vec{B_i}))$ |
| **Permute** $\pi$   | Endofunctor on $\mathcal{H}$           | Encode position/role — $\pi^k(\vec{x})$ marks $x$ as occupying the $k$-th slot in a hyperedge                                                                       |

The Embedding functor (FUN03: $F_{\text{embed}}: \text{state\_payload} \to \mathbb{R}^{1536}$) is currently a plain vector embedding. But in the HDC model, it becomes a **structure-preserving functor** $F_{\text{HDC}}: \mathcal{C} \to \mathcal{H}$:

$$F_{\text{HDC}}(\text{Node}) = \vec{v} \in \{-1,+1\}^d$$
$$F_{\text{HDC}}(\text{Wire}(A \xrightarrow{p_s} B, p_t)) = \text{bind}(\vec{A}, \pi^{p_s}(\vec{B}))$$

This functor **preserves the hypergraph structure** — the relational topology is encoded in the algebra of the hypervector space, not lost in a flat embedding. You can reconstruct wire existence from cosine similarity: $\cos(\text{bundle}(\vec{A}), \text{bind}(\vec{A}, \pi^{p}(\vec{B}))) \approx 1$ implies a wire $(A, p) \to B$ likely exists.

The three-pillar model from the paper structures is:

1. **Pillar 1**: The hypergraph (categorical, structural truth — $\mathcal{C}$)
2. **Pillar 2**: The rewriting system (morphisms, programs, replay — the catamorphism)
3. **Pillar 3**: The representation layer (HDC — $\mathcal{H}$), connected to Pillar 1 via $F_{\text{HDC}}$

---

## What "everything is an object/morphism" means concretely

The categorical frame that unifies all three (hypergraph, rules rewriting, HDC) is a **presheaf topos**.

Let $\mathcal{O}$ be the **ontology category** — the category whose:

- Objects = the 13 Kinds (OBJ01–OBJ13) + their port signatures
- Morphisms = the admissible wire types (the PortTarget whitelist from the SemanticRegistry)

Then a **hypergraph state** is a presheaf $G: \mathcal{O}^{\text{op}} \to \mathbf{Set}$:

- $G(\text{User})$ = the set of all User nodes currently in the graph
- $G(\text{OWNS}: \text{User} \to \text{Any})$ = the set of all OWNS wires from User nodes

A **morphism** (ADD/LINK/MUTATE/UNLINK) is a **natural transformation** between presheaves:
$$\alpha: G \Rightarrow G'$$
where $G$ is the pre-state and $G'$ is the post-state.

A **rewrite rule** is a span of presheaf morphisms:
$$L \xleftarrow{} K \xrightarrow{} R$$

The category of presheaves $[\mathcal{O}^{\text{op}}, \mathbf{Set}]$ is an **elementary topos** (presheaves on any small category form a topos). It has:

- Finite limits (pullbacks = pattern matching)
- Exponentials (function spaces = higher-order graph constructions)
- A subobject classifier $\Omega$ (subgraph predicates = query filters)

**The subobject classifier is the query system.** A query like `GET /state/nodes?kind=User&stratum=S2` is a characteristic morphism $\chi: G \to \Omega$ in the presheaf topos — it classifies the subpresheaf of User nodes at S2.

**Functors FUN01–FUN05 are geometric morphisms** between toposes:

- $F_{\text{ui}}: [\mathcal{O}^{\text{op}}, \mathbf{Set}] \to [\mathcal{R}^{\text{op}}, \mathbf{Set}]$ where $\mathcal{R}$ is the React component category
- These are structure-preserving but information-losing (S4 projections) — exactly as AX2 and AX4 require

---

## The bottom line

The moos model is already a hypergraph. The four invariant NTs are primitive rewrite rules. Programs are composed rewrites. The morphism log is the causal trace of a rewriting system. The ontology is a colored operad whose algebras are admissible graph states. The whole thing lives in a presheaf topos where queries are subobject classifiers and functors are geometric morphisms.

What the binary `Wire` type in Go does is provide the **König incidence encoding** of this structure — the same way a matrix of 0s and 1s encodes a graph without being a graph. The categorical reality was always there; the Go code just chose this particular presentation.

---

## References

- [Wolfram — A Class of Models with the Potential to Represent Fundamental Physics](https://www.wolframphysics.org/technical-introduction/)
- [Kanerva — Hyperdimensional Computing: An Introduction to Computing in Distributed Representation with High-Dimensional Random Vectors](https://doi.org/10.1007/s12559-009-9009-8)
- [Meijer, Fokkinga, Paterson — Functional Programming with Bananas, Lenses, Envelopes and Barbed Wire (1991)](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.41.125)
- [nLab: catamorphism](https://ncatlab.org/nlab/show/catamorphism)
- [nLab: presheaf](https://ncatlab.org/nlab/show/presheaf)
- [nLab: double pushout rewriting](https://ncatlab.org/nlab/show/double+pushout+rewriting)
- [Johnstone — Sketches of an Elephant: A Topos Theory Compendium (2002)](https://doi.org/10.1093/acprof:oso/9780198524960.001.0001)
- [Spivak — Category Theory for the Sciences](https://math.mit.edu/~dspivak/CT4S.pdf) Ch. 4 on databases as categories
- [Goguen — A categorical manifesto](https://doi.org/10.1017/S0960129500001365)
