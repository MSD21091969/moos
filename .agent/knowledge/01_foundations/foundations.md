# mo:os — Categorical Foundations

> Consolidated from `_legacy/01_foundations/` — see `_legacy/` for historical versions.
> Version: 3.0 | Date: 2026-07-03 | Locked Agreements: 9
>
> **Wolfram/HDC integration**: §4 (Wolfram correspondence + HDC encoding),
> §14 (paper references), §20 (computation triangle).
> **Cross-provider mapping**: §9 (benchmark functors, provider categories, Dispatcher as colimit).
> **Category Registry**: §21 (syn/sem classification of all named categories).
> Sources: `papers/wolfram_hdc_digest.md`, `papers/hypergraphrag_digest.md`, `papers/logicgraph_digest.md`.

---

## §1 — The One Axiom

Everything in mo:os reduces to one primitive:

$$\forall\, x \in \text{System},\quad x = (\text{urn},\; \Sigma(\text{morphisms}))$$

where $\Sigma : \text{Log} \to \text{State}$ folds the append-only morphism log into the current state.

**Consequences:**

- **Node/object = opaque identifier.** A URN is a key into the object
  store (historically the `containers` table). `container` is a
  compatibility/storage word, not the public semantic primitive. A
  node/object may wrap or point to whatever syntax a user needs to
  describe a scoped slice of the hypergraph — tree fragments, pipeline
  JSON, code references, policy fragments, or projected subgraph
  descriptors. The `state_payload` JSONB is still only a materialized
  view of morphism history — never the source of truth.

- **Purpose is the top program.** The root semantic anchor is purpose,
  and the kernel executes category-bearing syntax in service of that
  purpose. Kernel code is semantic machinery because it performs the
  evaluation; code outside the kernel remains syntax until hydrated and
  evaluated in topological context.

  > **Why state_payload is NOT truth.** If `state_payload` were the
  > source of truth, every consumer would have to parse, diff, and
  > reconcile a mutable JSONB blob. There would be no canonical history,
  > no replay, no time-travel, and no reconstruction after corruption.
  > The append-only `morphism_log` IS truth because: (a) it is
  > append-only and therefore tamper-evident, (b) any object's current
  > state can be reconstructed by folding
  > $\Sigma : \text{Log} \to \text{State}$, and (c) the `containers`
  > and `wires` tables are caches derivable from the log — if they
  > corrupt, replay rebuilds them. Treating `state_payload` as truth
  > would collapse the distinction between _derived state_ and _causal
  > history_, making audit, rollback, and federation impossible.

- **User = label on a blind box.** A `User` is an object whose
  morphisms grant edges. The user has no special ontological status — it
  is a label _inside_ the object, like all other labels. The difference
  is _visibility_: user identity labels are projected to admins and
  share-app users through the UI_Lens functor and connection morphisms,
  while other labels remain internal. Ontologically, user identity is a
  MUTATE on `state_payload`, not a privileged category.

- **Code is separated from metadata — and code is ALSO syntax.** Code
  lives in external stores (git, filesystem). The graph stores only
  URNs, wires, and morphism history. Binding code to state*payload creates
  structural coupling — a failure mode we call \_structural binding
  loss*.

  This separation exhibits a **symmetry**: just as data in
  `state_payload` is syntax (structured JSONB parsed by the kernel),
  code referenced by URNs is _also_ syntax — it is a structured
  representation that becomes semantics only when _evaluated_. Neither
  code nor metadata carries meaning intrinsically; meaning arises
  through the evaluation functor (the Go kernel executing morphisms).
  This is Lawvere's functorial semantics applied: **Syntax** = container
  schema + code-as-text, **Semantics** = kernel execution, **Bridge** =
  the structure-preserving functor mapping one to the other.

  **Hydration on evaluation.** Code — including atomic tools at the leaf level — is hydrated (loaded, bound, made executable) only when evaluated. This happens:
  - On each **use** (an agent or user invokes a tool → kernel traverses
    wires → tool container's code reference is resolved and executed)
  - On each **performance test** in the classification system with
    conventions (benchmark functor §9 evaluates tool quality → code is
    hydrated for measurement)

  **Topological use-case context.** Each evaluation must document its
  _topological state_ — the subgraph context in which the code was
  hydrated. A tool evaluated in workspace A with wires {W₁, W₂, W₃} is
  a different evaluation than the same tool in workspace B with wires
  {W₁, W₄}. Only when the evaluation records its position in the
  hypergraph can nested semantic layering (§8 sub-categories) produce
  meaningful D/R metrics. Without topological context, benchmark results
  are context-free and therefore uninterpretable.

  **Reference:** See `papers/Functorial Semantics as a Unifying
Perspective.pdf` for the categorical approach to bridging syntax and
  semantics through decomposition and composition; see
  `papers/HyperGraphRAG.pdf` for hypergraph-aware retrieval that
  respects topological context.

- **Semantic folders start empty.** A workspace container has no children until morphisms (ADD + LINK) create them. There is no implicit "contents" relation.
- **Only morphisms can change state.** Direct SQL writes to `containers` or `wires` tables violate the axiom. Every state change must be recorded in `morphism_log`.

---

## §2 — Category $\mathcal{C}$

mo:os defines a concrete category $\mathcal{C}$:

| Component              | Definition                                                                | Storage                                                                      |
| ---------------------- | ------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| **Objects**            | URNs — rows in `containers`                                               | `containers(urn UUID PK, type_id, state_payload JSONB, ...)`                 |
| **Morphisms** Hom(A,B) | Wires — rows in `wires`                                                   | `wires(source_urn, source_port, target_urn, target_port, wire_config JSONB)` |
| **Composition**        | Traversal — $f: A \to B$ and $g: B \to C$ compose to $g \circ f: A \to C$ | Join on `target_urn = source_urn`                                            |
| **Identity**           | Self-state — `id_A: A \to A$ is the node's current state_payload          | Virtual (no explicit self-wire stored)                                       |

**Properties of $\mathcal{C}$:**

- **Semi-discrete with recursion.** Adjacency is sparse (most node-pairs
  are unwired). Objects recorded in the historical `containers` store
  can represent scoped subgraphs (for example, a workspace scope that
  OWNS other objects). This gives fractal nesting without leaving the
  category.
- **Cycles permitted.** Unlike classical DAGs, $\mathcal{C}$ allows
  $A \to B \to A$. Cycle detection is a query concern, not a structural
  prohibition.
- **Finite and enumerable.** Unlike Set, $\mathcal{C}$ has finitely
  many objects and morphisms at any instant — all stored in Postgres.
- **NOT classical.** $\mathcal{C}$ is not a subcategory of Set. Objects
  have no internal structure visible to the category — they are opaque
  identifiers. All structure lives in the morphisms.

**Associativity:** For wires $f: A \to B$, $g: B \to C$, $h: C \to D$:

$$h \circ (g \circ f) = (h \circ g) \circ f$$

This holds because composition is SQL join, which is associative.

### Categorical Inventory

This table is the authoritative reference for every categorical concept used in mo:os.

| Concept                       | Categorical Identity                                                                   | Storage / Realization                                               |
| ----------------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| Containers                    | Objects in $\mathcal{C}$                                                               | `containers` table                                                  |
| Wires (including connections) | Morphisms in $\mathcal{C}$                                                             | `wires` table                                                       |
| Fan-out from node $A$         | Coslice category $A/\mathcal{C}$ (§5)                                                  | `SELECT * FROM wires WHERE source_urn = :A`                         |
| Fan-in to node $A$            | Slice category $\mathcal{C}/A$ (§5)                                                    | `SELECT * FROM wires WHERE target_urn = :A`                         |
| Translation (fan-out ↔ graph) | Forgetful functor $U: A/\mathcal{C} \to \mathcal{C}$ (§5)                              | Implicit in traversal (drops source context, keeps targets)         |
| Container with OWNS children  | Full subcategory $\mathcal{C}_W \hookrightarrow \mathcal{C}$ (§6)                      | Recursive CTE on `wires WHERE source_port = 'owns'`                 |
| $\Sigma$ (reducer)            | Colimit of morphism chain — catamorphism (§1)                                          | Kernel pipeline: Connection → Route → Dispatch → Transform → Commit |
| FileSystem                    | Functor $F_{\text{fs}}: \text{Manifest} \to \mathcal{C}$                               | Reads `manifest.yaml`, produces LINK morphisms                      |
| UI_Lens                       | Functor $F_{\text{ui}}: \mathcal{C} \to \text{React}$                                  | Renders containers + wires to XYFlow component tree                 |
| Embedding                     | Functor $F_{\text{embed}}: \text{state\_payload} \to \mathbb{R}^{1536}$                | pgvector in `container_embeddings`                                  |
| Structure                     | Functor $F_{\text{struct}}: \text{subgraph} \to \text{DAG}$ (planned)                  | GPU-accelerated topological compression                             |
| Benchmark                     | Functor $B: \mathcal{C}_{\text{provider}} \to \mathcal{C}_{\text{standard}}$ (planned) | Maps provider coslices to standard evaluation category              |

**What is NOT a functor:** Connections / transport surfaces (HTTP,
WebSocket, MCP/SSE) are **morphisms** (wires) in $\mathcal{C}$ — arrows
within the category, not structure-preserving maps between categories.
A new transport protocol is a new wire implementation, not a new
functor. See §5 for how the fan-out pattern from a service to multiple
endpoints is correctly modeled as a coslice category.

---

## §3 — The Four Invariant Natural Transformations

Every state change in mo:os decomposes into exactly four operations. These are the **only** invariant natural transformations of $\mathcal{C}$:

| Morphism   | Signature          | Effect                                                 |
| ---------- | ------------------ | ------------------------------------------------------ |
| **ADD**    | $\emptyset \to C$  | Create a new container (URN enters Objects)            |
| **LINK**   | $C \times C \to W$ | Create a wire between two containers (edge enters Hom) |
| **MUTATE** | $C \to C$          | Update a container's state_payload (endomorphism)      |
| **UNLINK** | $W \to \emptyset$  | Remove a wire (edge leaves Hom)                        |

**Why natural transformations?** For any functor $F: \mathcal{C} \to \mathcal{D}$ (e.g., $F_{\text{ui}}$ rendering the graph to React), the diagram commutes:

$$F(\text{ADD}(x)) = \text{ADD}_{F}(F(x))$$

The four morphisms have the same structural effect regardless of which functor surface observes them. This is the naturality condition.

**Completeness:** There is no fifth invariant morphism. DELETE for
containers is deliberately absent — you can only UNLINK an object's
edges, making it an orphan (invisible to traversal but still in the
log).

**Atomicity:** Each morphism is atomic:

- No cascading side effects (LINK doesn't MUTATE source/target)
- No split edges (one wire = one LINK)
- No implicit operations (ADD doesn't auto-LINK to parent)

**Composition:** Morphisms compose sequentially via `;`:

$$\text{ADD}(c) \;;\; \text{LINK}(parent, c) \;;\; \text{MUTATE}(c, \text{payload})$$

This is a morphism program. The semicolon is explicit — no implicit ordering.

---

## §4 — Hypergraph Superposition

The database stores **the** graph — a superposition of all possible projected graphs:

- **Multiple wires** between the same pair $(A, B)$ via different ports is the **general case**, not an edge case.
- Uniqueness constraint: `UNIQUE(source_urn, source_port, target_urn, target_port)` — the 4-tuple.
- A single pair can simultaneously have: an OWNS wire, a CAN_HYDRATE wire, a data-flow wire, and a template-binding wire.

**Superposition model:**

$$G_{\text{stored}} = \bigcup_{p \in \text{Ports}} G_p$$

where each $G_p$ is a projected subgraph filtered by port type.

**Query collapses superposition.** Selecting
`WHERE source_port = 'owns'` projects the ownership tree from the full
hypergraph. Different queries project different subgraphs from the same
underlying data.

**Traversal modes:**

- **Breadth** = enumerate all wires from a node → discovers the superposition
- **Depth** = follow one port type to leaves → resolves one projected graph

**What the single graph simultaneously encodes:**

- Ownership trees (port: `owns`)
- Permission graphs (port: `can_hydrate`)
- Data flow DAGs (port: `data_flow`)
- Template hierarchies (port: `template`)
- Agent capability graphs (port: `can_execute`)

No separate tables. No separate databases. One graph, many projections.

### Bipartite Storage Bijection

The `wires` table is a **bipartite incidence graph** representation of
the hypergraph (Wikipedia: "A hypergraph H may be represented by a
bipartite graph BG"). Port-pairs act as implicit relation nodes:
grouping wires by port type recovers the n-ary hyperedge.

HyperGraphRAG Proposition 2 proves the encoding
$\Phi: G_H \to G_B$ is a **bijection** — lossless. Proposition 1 proves
that binary decomposition (dropping ports) is **provably lossy**:
$H(X \mid \phi_B(X)) > 0$ while $H(X \mid \phi_H(X)) = 0$.
This validates the 4-tuple design over simpler (source, target) edges.

The dual hypergraph $H^*$ is obtainable by transposing the wires table
(swap source/target columns). The container hierarchy's `parent_urn`
tree provides $\alpha$-acyclicity for the ownership projection
(Beeri, Fagin, Maier, Yannakakis 1983).

### Wolfram Correspondence

This superposition model is the mo:os realization of Wolfram's
hypergraph universe. In the Wolfram Physics Project, space, time, and
content all emerge from a single hypergraph under rewriting rules —
exactly as ownership, permissions, data flow, and capabilities all
emerge from the single mo:os graph under the four invariant morphisms.

The four morphisms (ADD/LINK/MUTATE/UNLINK) are **rewriting rules** in
Wolfram's sense: each application matches a local pattern in the current
hypergraph and replaces it with a new local structure. The morphism log
is the complete history of rewriting steps.

**Effective dimension.** At any node $v$, the effective dimension of
the local graph neighborhood measures connectivity density:

$$d_{\text{eff}}(v) = \frac{\log |\text{Ball}(v, r)|}{\log r}$$

where $\text{Ball}(v, r)$ counts all containers reachable within $r$ wire
hops across all port types. This is the _"interface port diameter"_ from
the founder's manuscript — directly measuring the Wolfram graph-ball
growth rate in the mo:os domain. Dense hub nodes have high $d_{\text{eff}}$;
linear pipelines have $d_{\text{eff}} \approx 1$.

### HDC Encoding of Superposition

Hyperdimensional Computing gives the algebraic structure for encoding the
superposition as distributed representations:

$$\phi_{\text{ctx}}(v) = \bigoplus_{w \in \text{wires}(v)} \left( \mathbf{ROLE}_w \otimes \phi(\text{peer}(w)) \right)$$

where $\otimes$ = binding (creates relational structure), $\oplus$ =
bundling (creates superposition), and $\phi$ maps URNs to random
base hypervectors in $\{-1, +1\}^d$. The result is one hypervector
that encodes the full relational context of a node — the _"hypergraph
hypervector"_ — enabling similarity search without graph traversal.

See `papers/wolfram_hdc_digest.md` for full analysis.

### Three Pillars

The hypergraph model rests on three pillars integrated at the storage level:

| Pillar                                      | Provides                                                        | mo:os Surface                       |
| ------------------------------------------- | --------------------------------------------------------------- | ----------------------------------- |
| **Category Theory**                         | Formal structure (objects, morphisms, functors)                 | §21 registry, wires, NTs            |
| **Hypergraph Rewriting** (Wolfram)          | Computation model (rules, causal graph, confluence)             | morphism_log, 4 invariant morphisms |
| **Vector Symbolic Architectures** (Kanerva) | Representation ($\otimes$ bind, $\oplus$ bundle, $\pi$ permute) | embeddings table, pgvector HNSW     |

**Implementation status (2026-03-07):** Pillars 1 and 2 are deeply
formalized and implemented in the Go kernel. Pillar 3 (VSA/HDC) has
complete theory in `architecture.md` §11 and schema in
`0001_phase0_core.sql` (embeddings table) but **zero Go runtime code**
for algebraic HDC operations (bind/bundle/permute). The LLM embedding
path exists via provider adapters but no compositional HDC encoding.

---

## §5 — Coslice and Slice Categories: Fan-Out and Fan-In

When a single node $A$ has multiple outgoing wires to distinct targets, the set of those wires forms a **coslice category** $A/\mathcal{C}$.

### Coslice Category $A/\mathcal{C}$ (Fan-Out)

Given node $A$ in $\mathcal{C}$ with outgoing wires $f_1: A \to B_1, \; f_2: A \to B_2, \; \ldots, \; f_n: A \to B_n$:

| Component       | Definition                                                                                            |
| --------------- | ----------------------------------------------------------------------------------------------------- |
| **Objects**     | Outgoing morphisms from $A$: each $f_i: A \to B_i$ is an object                                       |
| **Morphisms**   | Commuting triangles: $h: B_i \to B_j$ such that $h \circ f_i = f_j$                                   |
| **Composition** | Inherited from $\mathcal{C}$: if $h: f_i \to f_j$ and $k: f_j \to f_k$, then $k \circ h: f_i \to f_k$ |
| **Identity**    | $\text{id}_{f_i} = \text{id}_{B_i}$ (the identity on the target)                                      |

**SQL realization:** `SELECT * FROM wires WHERE source_urn = :A` returns all objects of the coslice category $A/\mathcal{C}$.

**Why this matters:** One service endpoint that fans out to multiple
downstream consumers is not a functor — it is a coslice category. The
MOOS kernel dispatching messages to HTTP (:8000), WebSocket (:18789),
and MCP/SSE (:8080) simultaneously is the coslice from the kernel node.

### Slice Category $\mathcal{C}/A$ (Fan-In)

Dually, when multiple nodes wire into a single target $A$:

| Component     | Definition                                                          |
| ------------- | ------------------------------------------------------------------- |
| **Objects**   | Incoming morphisms to $A$: each $g_i: B_i \to A$                    |
| **Morphisms** | Commuting triangles: $h: B_i \to B_j$ such that $g_j \circ h = g_i$ |

**SQL realization:** `SELECT * FROM wires WHERE target_urn = :A`.

### The Forgetful Functor $U: A/\mathcal{C} \to \mathcal{C}$

The **translation** between a coslice category and the ambient graph is the forgetful functor:

$$U: A/\mathcal{C} \to \mathcal{C}$$

- On objects: $U(f_i: A \to B_i) = B_i$ (forgets the wire, keeps the target)
- On morphisms: $U(h: f_i \to f_j) = h: B_i \to B_j$ (forgets the commuting condition)

**Verification (functoriality):**

1. **Identity preservation:** $U(\text{id}_{f_i}) = U(\text{id}_{B_i}) = \text{id}_{B_i} = \text{id}_{U(f_i)}$ ✓
2. **Composition preservation:** $U(k \circ h) = k \circ h = U(k) \circ U(h)$ ✓

This functor is what allows the kernel to "zoom out" from a specific
fan-out context to the full graph: you drop the information about which
wire led you there and work directly with the targets.

### Practical Example: Task Decomposition as Coslice

When an agent decomposes a task into subtasks:

```text
AgentWorkspace → subtask_1, subtask_2, subtask_3
```

This is the coslice category `AgentWorkspace/C`. The forgetful functor
$U$ maps each subtask wire to its target container, enabling traversal
of subtask results independently of how they were assigned. The
commuting triangles capture subtask dependencies (if subtask_2 depends
on subtask_1, there's a morphism between them in the coslice).

---

## §6 — Scoped Objects as Full Subcategories via OWNS

A scoped object $W$ (historically called a `container`) with OWNS
children is **simultaneously** an object in $\mathcal{C}$ **and** a full
subcategory in its own right. The important semantic fact is the scoped
subcategory, not the storage-era noun. If a user wants a tree, that tree
is one projection of the hypergraph induced by OWNS — not the whole
ontology.

### Full Subcategory $\mathcal{C}_W \hookrightarrow \mathcal{C}$

Given a scoped object $W$ that OWNS $\{c_1, c_2, \ldots, c_m\}$:

$$\text{Ob}(\mathcal{C}_W) = \{W, c_1, c_2, \ldots, c_m\}$$

$$\text{Hom}_{\mathcal{C}_W}(x, y) = \text{Hom}_{\mathcal{C}}(x, y) \quad \forall\, x, y \in \text{Ob}(\mathcal{C}_W)$$

This is a **full subcategory** — it inherits ALL morphisms between its objects from $\mathcal{C}$.

**Inclusion functor** $\iota: \mathcal{C}_W \hookrightarrow \mathcal{C}$:

- On objects: $\iota(x) = x$ (identity embedding)
- On morphisms: $\iota(f) = f$ (identity on wires)

**Verification (functoriality):**

1. **Identity:** $\iota(\text{id}_x) = \text{id}_x = \text{id}_{\iota(x)}$ ✓
2. **Composition:** $\iota(g \circ f) = g \circ f = \iota(g) \circ \iota(f)$ ✓

### Recursive Nesting

Since $c_i$ can itself OWN children, subcategories nest:

$$\mathcal{C}_{c_i} \hookrightarrow \mathcal{C}_W \hookrightarrow \mathcal{C}$$

This gives the fractal structure mentioned in §2. A purpose-scoped
workspace can project projects, files, functions, tools, or policy
objects as nested full subcategories — each level is a scoped slice of
the same hypergraph, not a separate ontological regime.

### 2-Categorical View

Viewing containers-as-categories at the macro level:

| Level       | Category Theory                          | In mo:os                                                                                   |
| ----------- | ---------------------------------------- | ------------------------------------------------------------------------------------------ |
| **0-cells** | Categories                               | Containers-as-categories ($\mathcal{C}_W$, $\mathcal{C}_V$, …)                             |
| **1-cells** | Functors between categories              | Structure-preserving maps between container scopes (wires crossing subcategory boundaries) |
| **2-cells** | Natural transformations between functors | Morphism-level coherence (the four invariants commute across subcategory boundaries)       |

**SQL realization:** The recursive CTE for OWNS transitivity (architecture.md §5) is precisely the algorithm that computes $\text{Ob}(\mathcal{C}_W)$.

---

## §7 — Linear vs Non-Linear Growth: The Formalized Cost Model

**Locked Agreement #7.** This section formalizes what was discussed as "linear vs non-linear growth."

### Node Growth: O(n) — Boring

Nodes grow linearly. Each ADD creates one row in `containers`. Storage cost = $O(n)$. No combinatorial explosion. Nodes are independent identifiers.

### Edge Growth: The Interesting Part

For a directed multi-port graph with $n$ nodes, where each node has $|P_s|$ possible source ports and $|P_t|$ possible target ports:

$$|E_{\max}| = n^2 \times |P_s| \times |P_t|$$

This is NOT the simple $\frac{n(n-1)}{2}$ of undirected graphs. For 1000 nodes with 10 port types each: $1000^2 \times 10 \times 10 = 10^8$ potential edges.

Actual edges $k$ satisfy $k \ll n^2 \times |P_s| \times |P_t|$.

### The Gap IS the Knowledge

$$\text{Knowledge} = n^2 \times |P_s| \times |P_t| - k$$

The rules that filter potential edges into actual edges ARE the
system's intelligence. Every business rule, permission check, schema
constraint, and ontological decision is a filter that reduces $10^8$
potential edges to the $k$ that actually exist.

### Discovery Cost

$$\text{Cost}_{\text{discovery}} = O(|E_{\text{scope}}| \times c_{\text{index}})$$

where:

- $|E_{\text{scope}}|$ = candidate edges in the evaluated scope
- $c_{\text{index}}$ = per-node metadata density (schema JSONB size + state_payload complexity)

Discovery builds the index BY scanning. More metadata per node = slower scan, richer result. This is not a bug — it's a fundamental tradeoff.

### Retrieval Cost

$$\text{Cost}_{\text{retrieval}} = O(k + 1)$$

where $k$ = batch of node payloads, $1$ = pre-computed tree index (the
collapsed superposition from §4). Retrieval is asymptotically free
because the structure was pre-solved during discovery.

### D/R Ratio: Per-Sub-Category Optimization Metric

$$\frac{D}{R} = \frac{\text{Cost}_{\text{discovery}}}{\text{Cost}_{\text{retrieval}}}$$

The D/R ratio is computed per sub-category (§8):

| D/R Ratio    | Meaning                                      | Optimization Strategy                        |
| ------------ | -------------------------------------------- | -------------------------------------------- |
| High D (≫ R) | Schema is evolving, edges change frequently  | Pre-compute + cache subgraph structure       |
| High R (≫ D) | Schema is stable, mostly fetching known data | Optimize batch fetching, payload compression |
| D ≈ R        | Balanced                                     | Monitor for drift                            |

**Edge-defined relevance:** Edges define node RELEVANCE, not existence.
An orphan node (zero edges) exists in `containers` but is invisible to
every traversal. Relevance is structural, not intrinsic.

---

## §8 — Sub-Categories: Typed Port Signatures

Port preferences partition $\text{Hom}(A,B)$ into named channels, inducing sub-categories of $\mathcal{C}$.

**Formal definition:** A sub-category $\mathcal{C}_\sigma$ is a full
subcategory of $\mathcal{C}$ induced by the set of objects sharing a
port signature vocabulary $\sigma$.

**Relationship to §6:** Port-signature sub-categories
($\mathcal{C}_\sigma$) and OWNS-based subcategories ($\mathcal{C}_W$)
are orthogonal partitions of $\mathcal{C}$. An object can belong to
both an OWNS subcategory (structural containment) and a port-signature
subcategory (behavioral role). Their intersection
$\mathcal{C}_W \cap \mathcal{C}_\sigma$ gives "objects owned by $W$
that participate in the $\sigma$ vocabulary" — the scoped behavioral
slice.

**Properties:**

- Each user's port preferences = their personal projection of the hypergraph.
- Union of all users' port preferences = the active schema vocabulary.
- Zero-use edge types (ports never queried by any user) = candidates for UNLINK — graph hygiene.
- Per-schema D/R ratio (§7) = optimization signal for data pipelines.

**Example:** If agents use ports `{can_execute, data_flow}` and humans
use ports `{owns, can_hydrate}`, these are distinct sub-categories with
different D/R profiles and different optimization strategies.

---

## §9 — Benchmarks as Functors: Cross-Provider Category Mapping

A benchmark $B$ defines a structure-preserving map:

$$B: \mathcal{C}_{\text{provider}} \to \mathcal{C}_{\text{standard}}$$

**Structure preservation:**

- Objects in the provider category (e.g., model containers from different LLM vendors) map to objects in a standard evaluation category
- Morphisms (wires between provider objects) map to standard morphisms, preserving composition
- Cross-provider comparison = comparing functor images in $\mathcal{C}_{\text{standard}}$

**Key insight (LogicGraph reference):** Benchmarks don't test models in
isolation — they test the quality of the projected graph structure that
models traverse. Multi-path logical reasoning benchmarks specifically
measure hypergraph traversal quality.

### Functoriality = Why Process-Verified Evaluation Works

The benchmark functor $B$ must preserve composition:

$$B(g \circ f) = B(g) \circ B(f)$$

**This is the categorical reason why process-verified evaluation
outperforms outcome-only evaluation.** When evaluating a composed
pipeline (e.g., agent decomposes task → subtasks execute → results
compose), the benchmark MUST evaluate each step and verify that
composed step-evaluations equal the evaluation of the composed result.
If you only evaluate the final outcome, you violate functoriality — you
lose the compositional structure that makes the evaluation meaningful.

**Concretely:** Given a coslice decomposition (§5) where agent $A$ fans
out to subtasks $\{f_1, f_2, f_3\}$, the benchmark must score each
$f_i$ independently AND verify that
$B(f_3 \circ f_2 \circ f_1) = B(f_3) \circ B(f_2) \circ B(f_1)$. Outcome-only
evaluation checks the left side. Process-verified evaluation checks the
right side AND the equation.

**Benchmark suites** = families of functors parameterized by task type:

$$\{B_t : \mathcal{C}_{\text{provider}} \to \mathcal{C}_{\text{standard}}\}_{t \in \text{Tasks}}$$

This replaces ad-hoc "accuracy on dataset X" with a categorical framework where the comparison itself preserves compositional structure.

### Cross-Provider Category Mapping

Each LLM provider defines its own category:

$$\mathcal{P}_{\text{anthropic}}, \quad \mathcal{P}_{\text{gemini}}, \quad \mathcal{P}_{\text{openai}}$$

**Objects** in each provider category are the provider's models (e.g.,
`claude-3-7-sonnet`, `gemini-2.0-flash`, `gpt-4o`), each with a
capability profile: context window, tool-use support, streaming
protocol, token pricing, latency characteristics.

**Morphisms** in each provider category are the operations the provider
supports: `Complete`, `Stream`, tool invocations, and any
provider-specific operations (Anthropic's prompt caching, Gemini's
grounding, OpenAI's function calling). These morphisms compose — a
`Complete` followed by tool-call parsing followed by morphism extraction
is a composed morphism.

The benchmark functor is **per-provider**:

$$B_{\text{anthropic}}: \mathcal{P}_{\text{anthropic}} \to \mathcal{C}_{\text{standard}}$$
$$B_{\text{gemini}}: \mathcal{P}_{\text{gemini}} \to \mathcal{C}_{\text{standard}}$$
$$B_{\text{openai}}: \mathcal{P}_{\text{openai}} \to \mathcal{C}_{\text{standard}}$$

All three land in the **same target category** $\mathcal{C}_{\text{standard}}$.
Cross-provider comparison is comparison of images:

$$B_{\text{anthropic}}(\text{claude-3-7-sonnet}) \quad \text{vs} \quad B_{\text{gemini}}(\text{gemini-2.0-flash})$$

Both are objects in $\mathcal{C}_{\text{standard}}$, so they are
directly comparable via the standard category's hom-sets.

### The Standard Evaluation Category

$\mathcal{C}_{\text{standard}}$ has:

| Objects                                                          | Morphisms                                                   |
| ---------------------------------------------------------------- | ----------------------------------------------------------- |
| Scored task results: `(task, score, morphism_trace, latency)`    | Score composition: subtask scores compose to pipeline score |
| Capability profiles: `(context_length, tool_support, streaming)` | Profile ordering: partial order by capability coverage      |
| Cost metrics: `(tokens_in, tokens_out, price, p50_latency)`      | Cost composition: pipeline cost = sum of stage costs        |

**Key property:** $\mathcal{C}_{\text{standard}}$ must be **provider-agnostic**.
Its structure is defined by the _task domain_, not by any provider's API
surface. This is why the four invariant morphisms (§3) define the only
operations: any provider output must be expressible as a sequence of
ADD/LINK/MUTATE/UNLINK. A model that produces outputs incompatible with
the four morphisms is outside the category.

### Natural Transformations Between Benchmark Functors

A **natural transformation** $\eta: B_t \Rightarrow B_{t'}$ between two
benchmark functors (for task types $t$ and $t'$) maps every provider
model's score on task $t$ to its score on task $t'$, coherently:

$$\eta_{\text{model}} : B_t(\text{model}) \to B_{t'}(\text{model})$$

**Naturality condition:** For any provider morphism $f: M_1 \to M_2$
(e.g., fine-tuning, or model version upgrade):

$$\eta_{M_2} \circ B_t(f) = B_{t'}(f) \circ \eta_{M_1}$$

This says: the relationship between task performance is preserved across
model upgrades. If a natural transformation exists between
$B_{\text{reasoning}}$ and $B_{\text{code\_gen}}$, then a model that
improves on reasoning will predictably improve on code generation, and
the improvement factor is coherent across models.

**When naturality FAILS:** The absence of a natural transformation
between two benchmark functors is informative — it means the two task
types measure genuinely independent capabilities. A model can improve on
one without improving on the other. This is where per-task evaluation is
irreducible (no shortcut from one benchmark to predict another).

### The Dispatcher as a Colimit

The `Dispatcher` (Go: `model.NewDispatcher(primary, adapters...)`)
implements a **colimit** over the provider categories:

$$\text{Dispatch}: \coprod_{p \in \text{Providers}} \mathcal{P}_p \to \mathcal{C}_{\text{kernel}}$$

The provider order (primary → secondary alphabetical → error) defines a
cocone from the coproduct of provider categories into the kernel's
morphism category. Each adapter is an inclusion map
$\iota_p : \mathcal{P}_p \to \coprod \mathcal{P}_p$, and the
Dispatcher's `Complete`/`Stream` methods form the universal map from
the coproduct into the kernel.

**Fallback as coproduct**: The fallback chain
(`primary || secondary₁ || secondary₂ || error`) is the colimit
construction: try the first diagram leg, if it fails try the next —
the first success IS the colimit morphism. This is why the kernel's
pure core sees no provider-specific types: it receives
`CompletionResult` (= an object in $\mathcal{C}_{\text{kernel}}$)
regardless of which provider produced it.

### The Adapter Interface as a Forgetful Functor

Each adapter implements the same `Adapter` interface:

```go
type Adapter interface {
    Name() string
    Complete(ctx context.Context, request CompletionRequest) (CompletionResult, error)
    Stream(ctx context.Context, request CompletionRequest) (<-chan Chunk, error)
}
```

This interface acts as a **forgetful functor** $U: \mathcal{P}_p \to
\mathcal{C}_{\text{adapter}}$ — it forgets provider-specific structure
(API keys, headers, SSE parsing, model names) and retains only the
morphism-relevant operations (`Complete`, `Stream`). All provider
categories have the same image under $U$: the two-method adapter
contract.

The compile-time verification `var _ provider.LLM = (*AnthropicAdapter)(nil)`
is the Go expression of this forgetful functor: it asserts that the
concrete type satisfies the abstract interface — that the inclusion into
the adapter category is well-defined.

### Cross-Provider Benchmark Workflow

```text
Task(t) ──→ B_anthropic(claude-3-7) ──→ Standard score S₁
         ├→ B_gemini(gemini-2.0)    ──→ Standard score S₂
         └→ B_openai(gpt-4o)       ──→ Standard score S₃
                                         │
                                         ▼
                              Compare S₁, S₂, S₃ in C_standard
                              Natural transformations detect
                              cross-task capability correlations
```

**What the benchmark measures per provider:**

| Dimension            | What It Captures                             | Morphism-Level Measurement                            |
| -------------------- | -------------------------------------------- | ----------------------------------------------------- |
| **Accuracy**         | Correct morphism extraction from LLM output  | % of valid envelopes in `CompletionResult.Morphisms`  |
| **Compositionality** | Step-wise vs end-to-end consistency          | $B(g \circ f) \stackrel{?}{=} B(g) \circ B(f)$        |
| **Latency**          | Time-to-first-morphism, total pipeline time  | Prometheus `moos_cost_execution_seconds` per provider |
| **Cost**             | Token consumption per morphism produced      | Input/output token ratio from provider billing        |
| **Robustness**       | Graceful degradation under ambiguous prompts | Error rate classification per LogicGraph taxonomy     |
| **Tool fidelity**    | Correct tool invocation from graph context   | `CompletionResult.ToolCalls` validity rate            |

---

## §10 — GPU Structure Functor

$$F_{\text{struct}}: \text{subgraph} \to \text{compressed DAG}$$

**Traditional pipeline:**

```text
raw content → LLM prompt → LLM discovers structure → answer
```

**Proposed pipeline:**

```text
raw content → GPU graph analysis → structured subgraph → LLM prompt → answer
```

**What $F_{\text{struct}}$ does:**

- Adjacency matrix operations (connected components, strongly connected components)
- Spectral analysis (importance scoring via eigenvector centrality)
- DAG compression (transitive reduction, redundant edge removal)
- Subgraph extraction for bounded-context LLM prompts

**Hardware context:** GPU handles $O(n^2 \times |rules|)$ filtering massively in parallel. The Z440's 12GB VRAM can process ~50K-node subgraphs in real time.

**Composition with other functors:**

- $F_{\text{struct}} \circ F_{\text{embed}}$: first embed content, then analyze structure of the embedding space
- $F_{\text{struct}}$ standalone: pure topological analysis without semantic embedding

**Benefit:** Reduces LLM token cost by providing pre-analyzed
structure. Forces structural awareness before the LLM call, preventing
the model from wasting tokens rediscovering graph topology.

---

## §11 — Two Access Domains

**Locked Agreement #3.** Access is split into two orthogonal domains:

| Domain          | Controls                 | Mechanism                                         |
| --------------- | ------------------------ | ------------------------------------------------- |
| **Node access** | Identity — who you ARE   | Auth user has a key (URN) for containers they own |
| **Edge access** | Policy — what you CAN DO | Any rule: global, local, temporal, env-based      |

**Why two domains?** If access were node-only, you couldn't have shared
resources. If access were edge-only, you couldn't have identity. The
split allows: "User A owns node X" (node domain) AND "Users with role Y
can hydrate node X" (edge domain) simultaneously.

Edge access is stored as wires. Permission check = wire existence check:

```sql
SELECT 1 FROM wires
WHERE source_urn = :actor AND target_urn = :resource
  AND source_port = 'can_hydrate'
```

If the wire exists, permission is granted. No separate ACL table.

---

## §12 — Transitivity

**Locked Agreements #4, #8.**

Two transitivity modes co-exist in $\mathcal{C}$:

| Wire Type       | Transitivity      | Rule                                                                                                                           |
| --------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| **OWNS**        | Automatic         | If $A \xrightarrow{\text{owns}} B$ and $B \xrightarrow{\text{owns}} C$, then $A$ transitively owns $C$. No declaration needed. |
| **CAN_HYDRATE** | Declared per-edge | Each wire's `wire_config` controls whether the edge propagates. Manifest declares propagation rules.                           |

**Manifest = transitivity controller** (Locked Agreement #8):

- Currently lives as a YAML/JSON config file
- Controls which CAN_HYDRATE edges propagate transitively
- Will dissolve into the `wires` table when graph sync (§7 in architecture.md) is implemented
- At that point, transitivity rules become wires themselves — self-describing graph

**Relationship to §6:** OWNS transitivity is the mechanism that defines
subcategory membership. The recursive CTE computes
$\text{Ob}(\mathcal{C}_W)$ by following transitive OWNS chains.

---

## §13 — RAG as Functor

Retrieval-Augmented Generation integrates as a functor:

$$F_{\text{embed}}: \text{state\_payload} \to \mathbb{R}^{1536}$$

stored in `container_embeddings` via `pgvector`.

**Graph vs Vector — complementary, not competing:**

| Dimension        | Graph (wires)           | Vector (embeddings)     |
| ---------------- | ----------------------- | ----------------------- |
| Precision        | Exact match             | Approximate             |
| Composability    | $g \circ f$ works       | Non-composable          |
| Schema-awareness | Port-typed edges        | Flat feature space      |
| Explainability   | Wire path = audit trail | Opaque similarity score |

**Separation principle:** Embeddings are **functor output**, not graph
metadata. They are stored separately (`container_embeddings`, not
`state_payload`) and regenerated on every MUTATE. This prevents
functor-as-metadata pollution.

**Discovery complement:** Vector search finds semantically similar
objects that may not be wired. This complements graph traversal (which
finds structurally connected objects). The two discovery modes are
orthogonal.

---

## §14 — The Syntax/Semantics Bridge: Functorial Decomposition and Composition

mo:os instantiates Lawvere's functorial semantics (1963) as an
operational architecture, not just a theoretical model. The key insight
is that **syntax and semantics are separate categories connected by a
structure-preserving functor**.

### The Bridge

| Layer                                                                 | Role                                                                 | In mo:os                                                               |
| --------------------------------------------------------------------- | -------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| **Syntax category** $\mathcal{S}$                                     | Structure of the language — types, ports, wiring rules, code-as-text | Container schema, `wires` topology, code references in `state_payload` |
| **Semantics category** $\mathcal{M}$                                  | Meaning of the language — what happens when evaluated                | Go kernel morphism execution, LLM outputs, tool results                |
| **Evaluation functor** $F_{\text{eval}}: \mathcal{S} \to \mathcal{M}$ | Structure-preserving map from syntax to semantics                    | Kernel pipeline $\Sigma$ — the reducer (§1)                            |

**Structure preservation** means that if two syntactic elements compose
in $\mathcal{S}$ (e.g., two wired objects), their semantic evaluations
compose identically in $\mathcal{M}$. This is the naturality condition
for the four invariant morphisms (§3).

**The evaluation functor IS the reducer $\Sigma$.** The kernel pipeline
(Connection → Route → Dispatch → Transform → Commit) is a concrete
implementation of the functor $F_{\text{eval}}: \mathcal{S} \to \mathcal{M}$.
It takes syntactic structure (objects, wires, morphism requests) and
produces semantic results (state changes, committed to the log). The
catamorphism $\Sigma: \text{Log} \to \text{State}$ is
$F_{\text{eval}}$ applied iteratively over the full morphism history.

### Decomposition and Composition Are Categorical Duals

**Decomposition** (analysis): Given a complex subgraph, decompose into
atomic morphisms (ADD, LINK, MUTATE, UNLINK). Every subgraph operation
has a unique decomposition into these four invariants. This is
guaranteed by §3's completeness.

**Composition** (synthesis): Given a sequence of atomic morphisms,
compose them into a coherent subgraph transformation. The semicolon
operator `;` composes morphism programs. The result is verifiable:
replay the log and check.

The critical property is **decomposition followed by composition is
identity** (up to ordering of independent morphisms). This is NOT true
for LLM-based task decomposition, where:

- Decomposition is LLM-generated (can hallucinate)
- Recomposition has no formal guarantees
- Subtasks can be incompatible

mo:os avoids this by decomposing into _mathematically invariant_ operations, not natural-language task descriptions.

### The Neuro-Symbolic Implication (System 3 Reasoning)

The System 3 transcript (`transcripts/system 3.txt`) and
`papers/LogicGraph  Benchmarking Multi-Path Logical Reasoning.pdf`
establish that:

1. **LLMs prioritize semantic fluency over logical entailment.** They
   build linguistically plausible but logically invalid bridges between
   known start and end states (result-oriented hallucination).
2. **Neuro-symbolic pipelines** escape this by anchoring language models to symbolic engines (Prover9, Lean 4, Python verification).
3. **Process-verified rewards** (per-step verification) outperform
   outcome-verified rewards (final-answer-only) for complex reasoning.
   **This is functoriality** — see §9 for why preserving composition at
   each step is categorically required.

**How mo:os already implements this:**

- The kernel IS the symbolic engine — it speaks objects, wires, and the
  four invariant morphisms (pure logic, zero hallucination).
- LLMs are **Fuzzy Processing Units** — sandboxed coprocessors that
  propose morphisms, which the kernel validates against the graph
  structure before committing.
- Every morphism step is logged and verifiable (process-level audit, not
  just outcome).
- Multi-path reasoning = hypergraph traversal through multiple port
  types simultaneously (§4 superposition).
- Task decomposition by agents produces coslice categories (§5) — the
  forgetful functor $U$ recovers the target containers from the
  decomposition structure.

**What this means for evaluation:**

- Benchmarks (§9) should be structured as neuro-symbolic verification:
  LLM proposes → kernel decomposes → each step verified against graph
  constraints → process reward computed.
- The LogicGraph error taxonomy (semantic misinterpretation,
  information omission, fact hallucination, invalid deduction, rule
  misapplication, insufficient premise) maps to specific failure modes
  in morphism decomposition.
- Functoriality of the benchmark (§9) ensures that step-by-step
  evaluation is categorically consistent with end-to-end evaluation.

### Paper References

| Paper                                                     | Key Contribution to mo:os                                                                                                                            |
| --------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Functorial Semantics as a Unifying Perspective**        | Categorical decomposition/composition guarantees; syntax/semantics bridge formalization                                                              |
| **HyperGraphRAG**                                         | Hypergraph-aware retrieval that preserves topological context during RAG operations                                                                  |
| **LogicGraph: Benchmarking Multi-Path Logical Reasoning** | Error taxonomy for LLM reasoning failures; neuro-symbolic verification pipeline; multi-path graph traversal as benchmark                             |
| **Seven Sketches in Compositionality** (Fong & Spivak)    | Monoidal categories, operads, wiring diagrams — the mathematical vocabulary of mo:os                                                                 |
| **Wolfram Physics Project** (Wolfram 2020)                | Hypergraph rewriting as computational primitive; multiway systems; causal invariance = replay consistency; effective dimension via graph-ball growth |
| **Hyperdimensional Computing** (Kanerva 2009)             | Distributed representation algebra (bind/bundle/permute) for compositional graph encoding; GPU-parallel vector operations on graph structure         |

---

## §15 — Morphism Log as Ground Truth

The append-only `morphism_log` table is the single source of truth:

```sql
SELECT new_state FROM morphism_log
WHERE target_urn = :x
ORDER BY id DESC LIMIT 1
```

This reconstructs the current state of any object.

**Implications:**

- `containers.state_payload` is a **cache** — a materialized view of the latest morphism.
- `wires` table is a **cache** — the current set of active edges derived from LINK/UNLINK history.
- Time-travel: replay morphisms up to any timestamp to reconstruct historical state.
- Audit: every state change has an author, timestamp, and previous state.
- Reconstruction: if `containers` and `wires` tables are corrupted, they can be rebuilt from `morphism_log` alone.

**Σ as replay.** The reducer $\Sigma: \text{Log} \to \text{State}$
(§1) is precisely this reconstruction operation. Folding the morphism
log produces the current state. The log IS the category's morphism
history; the state IS the colimit.

---

## §16 — Field Research Placeholder

Empirical observation categories for future validation:

- **Morphism frequency distribution**
  - measures: which of the 4 morphisms dominate in real usage
  - source: `morphism_log`
- **Edge density ratio**
  - measures: sparsity of the actual graph relative to
    $k / (n^2 \cdot \|P_s\| \cdot \|P_t\|)$
  - source: `wires` + `containers` count + port types
- **Traversal depth**
  - measures: average/max path length in ownership trees
  - source: recursive CTE on `wires`
- **Replay cost**
  - measures: time to reconstruct state from morphism log
  - source: benchmark on `morphism_log` size
- **Hypergraph fanout**
  - measures: average number of distinct port types per node-pair
  - source: `wires` grouped by source/target
- **Coslice cardinality**
  - measures: average fan-out degree per node
  - source: `wires` grouped by `source_urn`
- **Subcategory depth**
  - measures: max nesting level of OWNS chains
  - source: recursive CTE depth counter

**Method:** Prometheus metrics at `/metrics` endpoint plus direct SQL
queries on `morphism_log`. These observations will validate or falsify
the cost model (§7) and sub-category analysis (§8) once production data
exists.

---

## §17 — The Stratum Model

The graph is not flat. Objects and wires occupy distinct **strata**
that reflect their role in the system's self-description hierarchy.
This is a formal categorical construction, not merely a naming
convention.

### Four Strata as a Filtration

Define a filtration of $\mathcal{C}$:

$$\mathcal{C}_0 \hookrightarrow \mathcal{C}_1 \hookrightarrow \mathcal{C}_2$$

where each $\mathcal{C}_i$ is a full subcategory of $\mathcal{C}$ and
$\hookrightarrow$ is the inclusion functor (§6). Stratum 3
($\mathcal{L}$) is NOT a subcategory of $\mathcal{C}$ — it is a
separate target category reached only by projection functors.

| Stratum | Category        | Contains                                                                                                                         | Mutability                                                           |
| ------- | --------------- | -------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| **S0**  | $\mathcal{C}_0$ | Bootstrap substrate — invariant algebra, log contract, evaluator reference, identity/version primitives                          | Immutable after seed. Protected from user morphisms.                 |
| **S1**  | $\mathcal{C}_1$ | Authoring syntax — category declarations, functor declarations, schema/port vocabularies, governance policies, bootstrap presets | Mutable by authoring pipeline only. Syntax about the semantic world. |
| **S2**  | $\mathcal{C}_2$ | Operational graph — workspaces, documents, tools, agents, sessions, providers, users, groups                                     | Mutable by user/agent morphisms. Where runtime state lives.          |
| **S3**  | $\mathcal{L}$   | Projection surfaces — UI renders, embeddings, compressed DAGs, API responses                                                     | Never stored in `containers`. Always computed from S2 by functors.   |

### Inclusion Maps as Functors

The inclusions $\iota_i : \mathcal{C}_i \hookrightarrow \mathcal{C}_{i+1}$
are exact — they preserve all objects and all morphisms between those
objects. This means:

- S0 rules **constrain** all valid S2 transitions (the invariant
  morphism algebra declared in S0 governs what morphisms S2 can use)
- S1 declarations **define** the vocabulary for S2 objects (a `kind`
  used in S2 should trace to an S1 `_S1_CATEGORY` declaration)
- S2 state is **projected** into S3 by lens/functor surfaces (never the
  reverse — S3 cannot modify S2)

### Stratum as Discriminator

Each object and wire carries a `stratum` attribute. This is an
integer (0, 1, 2) stored in the database. Stratum 3 objects are
never stored — they exist only as functor output in memory or
external systems.

**Stratum promotion:** An S1 declaration can be "promoted" into S2
by the materialization step of the hydration lifecycle (see
`05_moos_design/hydration_lifecycle.md`). Promotion means: the S1
syntax object generates a sequence of ADD/LINK morphisms that create
corresponding S2 objects. The S1 object persists as the authoring
source; the S2 objects are the operational instances.

**Stratum demotion:** Not permitted. An S2 operational object cannot
become an S1 declaration. If an S2 pattern needs to become reusable
authoring syntax, a NEW S1 declaration is authored that captures the
pattern.

---

## §18 — Mock Categories as Formal Scaffolds

Mock categories are temporary objects created to test topology,
execution, governance, or schema hypotheses. They follow a formal
lifecycle to prevent prototype concepts from silently hardening into
permanent ontology.

### Lifecycle State Machine

A mock category is an S1 or S2 object with `lifecycle = "mock"`. It
transitions through exactly one of four terminal states:

$$\text{MOCK} \xrightarrow{\text{validate}} \begin{cases} \text{PROMOTED} & \text{(becomes permanent S2 object)} \\ \text{DELETED} & \text{(orphaned, invisible to traversal)} \\ \text{SPLIT} & \text{(decomposes into finer categories)} \\ \text{RECLASSIFIED} & \text{(changes categorical classification)} \end{cases}$$

**MOCK → INVALID** is also possible if validation (hydration Stage 2)
fails. Invalid mocks can be corrected and re-validated.

### Mandatory Mock Metadata

Every mock object in $\mathcal{C}$ must carry:

- `mock_purpose`: Why this category exists as a hypothesis
- `mock_review_by`: Deadline for lifecycle decision (temporal
  `wire_config` rule from §5 of architecture can auto-expire)
- `mock_metrics`: Placeholder for D/R and THC measurements once
  the mock is evaluated

**Enforcement:** The kernel validation (pure core) rejects ADD
morphisms that create mock objects without these fields. This is a
Stratum 0 rule — it is part of the invariant algebra.

### Why Mocks Matter

Without formal mock lifecycle, every prototype category eventually
becomes load-bearing. Engineers treat temporary names as permanent
ontology. The normalization sheet (05_moos_design) warns against
this: `container`, `NodeContainer`, `RootContainer`, `hasContainer`
are all examples of mock-era concepts that hardened into the codebase
without lifecycle review.

---

## §19 — The Hydration Bridge: From Syntax to Semantics to Projection

The syntax/semantics bridge (§14) is one link in a longer chain. The
full hydration lifecycle connects **five** categories through
structure-preserving functors:

$$\mathcal{A} \xrightarrow{V} \mathcal{V} \xrightarrow{M} \mathcal{P} \xrightarrow{E} \mathcal{C} \xrightarrow{P_i} \mathcal{L}_i$$

| Functor | Name               | From → To                                           |
| ------- | ------------------ | --------------------------------------------------- |
| $V$     | Validate           | Authored artifacts → Validated artifacts            |
| $M$     | Materialize        | Validated artifacts → Morphism programs             |
| $E$     | Evaluate           | Morphism programs → Operational graph $\mathcal{C}$ |
| $P_i$   | Project (multiple) | Operational graph → Lens surfaces $\mathcal{L}_i$   |

The evaluation functor $E$ is the reducer $\Sigma$ from §1. The
projection functors $P_i$ are the five functors from §2 (FileSystem,
UI_Lens, Embedding, Structure, Benchmark).

**The full pipeline** $P_i \circ E \circ M \circ V$ is the complete
hydration functor from authored intent to visible projection. Its
composition is guaranteed by functoriality at each stage.

**Decomposition/composition duality (§14) still holds:** Each stage
decomposes complex structures into atomic operations, and the
composition of those operations is verified at each functor boundary.
The pipeline as a whole satisfies:

$$P(E(M(V(a_1 ; a_2)))) = P(E(M(V(a_1)))) ; P(E(M(V(a_2))))$$

for independent authored artifacts $a_1, a_2$. This is the
categorical guarantee that hydrating two declarations separately
produces the same result as hydrating their composition.

**Reference:** Full operational specification in
`05_moos_design/hydration_lifecycle.md`.

---

## §20 — Rewriting Semantics and the Computation Triangle

_References: Wolfram Physics Project (2020), Kanerva's HDC (2009),
founder's manuscript, papers/wolfram_hdc_digest.md._

The Collider's founding vision rests on three pillars that form a
**computation triangle** — each pillar addressing a distinct aspect
of the system:

### The Three Pillars

| Pillar                    | Provides                                                     | Formal Basis                         |
| ------------------------- | ------------------------------------------------------------ | ------------------------------------ |
| **Category Theory**       | Structural framework (objects, morphisms, functors)          | Lawvere's functorial semantics (§14) |
| **Hypergraph Rewriting**  | Computational model (the graph IS the computation)           | Wolfram's multiway systems           |
| **Hypervector Computing** | Representation layer (distributed encoding for parallel ops) | Kanerva's VSA algebra                |

### Rewriting Formalization

The four invariant morphisms (§3) are graph rewriting rules. Each
application is a local transformation: match a precondition in the
current graph, replace with new structure, append to the log.

The morphism log is a **causal graph**: entries that reference each
other's versions are causally related; entries on disjoint subgraphs
are causally independent. Causal invariance holds for independent
morphisms — a property testable by applying them in both orderings.

The set of all reachable states (via finite morphism sequences) is the
mo:os **state space** — a finite projection of Wolfram's ruliad.

### HDC Formalization

The Embedding functor (FUN03) uses HDC algebra internally:

- **Bind** $\otimes$: encodes port-typed relationships (wire = bound pair of role + URN)
- **Bundle** $\oplus$: encodes node context (superposition of all incident wires)
- **Permute** $\pi$: encodes temporal position in morphism history

This gives structure-preserving compositionality to the embedding space:
the embedding of a composed structure equals the composition of
embeddings, because HDC operations distribute over each other.

### Founder's Manuscript Grounding

The manuscript explicitly states this trinity:

> _"category theory and then hypervector and functional programming to
> process the rigid logic of the numerous graphs in the hypergraph
> instead of just 1 topological one then gpu"_

> _"hypergraph solves that. By placing the diff states in the same nide
> instad of topologically"_ — this IS Wolfram's multiway system: multiple
> states coexist at the same node rather than being split into separate
> topological copies.

> _"Its a hyoergraph whatvuser buils and at any end of morf choice to pick
> avail aother based on rules"_ — rule application creating branching
> histories in the multiway graph.

---

## §21 — Category Registry: Theory vs Model

_Reference: §14 (Lawvere's functorial semantics), §18 (mock
categories), §19 (hydration bridge). Waves: `06_planning/greenfield_implementation_waves.md`._

A named category is a **theory** (syntax) until its objects and
morphisms are explicitly defined. The definition is its **model**
(semantics). The structure-preserving map from theory to model is the
evaluation functor — the same bridge formalized in §14, now applied
reflexively to the knowledge base itself.

$$\text{Theory} \xrightarrow{F_{\text{eval}}} \text{Model}$$

A category stuck at theory-only status has the same failure mode as a
mock object (§18) that never gets lifecycle review: it silently
becomes load-bearing despite carrying no formal content.

### Formalization Levels

| Level  | Name              | Definition                                                     | Risk                                                             |
| ------ | ----------------- | -------------------------------------------------------------- | ---------------------------------------------------------------- |
| **L3** | Fully modeled     | Objects, morphisms, composition, identity all explicit         | None — this is the target                                        |
| **L2** | Partially modeled | Objects named, some morphisms described, composition implicit  | Misuse — people compose in it without checking associativity     |
| **L1** | Named only        | Appears in functor signatures or prose, no internal structure  | Label on a blind box — §1's warning about nodes applies here too |
| **L0** | External          | Standard mathematical category (e.g. $\mathbb{R}^{1536}$, Set) | None — inherited from mathematics                                |

### The Registry

Every named category in mo:os, its formalization level, where it is
defined, and when it becomes modeled.

#### Core Categories

| Category                      | Level  | Objects                                       | Morphisms                    | Defined In          | Realized By |
| ----------------------------- | ------ | --------------------------------------------- | ---------------------------- | ------------------- | ----------- |
| $\mathcal{C}$ (main)          | **L3** | URNs (`containers` rows)                      | Wires (`wires` rows)         | §2                  | Wave 0      |
| $A/\mathcal{C}$ (coslice)     | **L3** | Outgoing morphisms from $A$                   | Commuting triangles          | §5                  | Wave 0      |
| $\mathcal{C}/A$ (slice)       | **L3** | Incoming morphisms to $A$                     | Commuting triangles          | §5                  | Wave 0      |
| $\mathcal{C}_W$ (scoped)      | **L3** | $W$ + OWNS children (recursive)               | Inherited from $\mathcal{C}$ | §6                  | Wave 0      |
| $\mathcal{C}_{\text{kernel}}$ | **L3** | = $\mathcal{C}$ (same objects, post-dispatch) | = $\mathcal{C}$ morphisms    | §9, kernel_spec §14 | Wave 0      |

#### Stratum Chain

| Category                      | Level  | Objects                      | Morphisms                     | Defined In    | Realized By |
| ----------------------------- | ------ | ---------------------------- | ----------------------------- | ------------- | ----------- |
| $\mathcal{C}_0$ (bootstrap)   | **L2** | Objects where `stratum = 0`  | Wires between S0 objects      | strata Part 2 | Wave 0      |
| $\mathcal{C}_1$ (authoring)   | **L2** | $\mathcal{C}_0$ ∪ S1 objects | Wires between S0∪S1 objects   | strata Part 2 | Wave 4      |
| $\mathcal{C}_2$ (operational) | **L2** | $\mathcal{C}_1$ ∪ S2 objects | All wires (the working graph) | strata Part 2 | Wave 4      |

**Gap**: Inclusion functors $\iota_k: \mathcal{C}_k \hookrightarrow \mathcal{C}_{k+1}$ are stated but composition verification is not shown. Promote to L3 by proving $\iota_1 \circ \iota_0 = \iota_{01}$ and that each $\iota_k$ is full and faithful.

#### Hydration Pipeline Categories (§19)

| Category                        | Level  | Objects                                       | Morphisms | Defined In         | Realized By |
| ------------------------------- | ------ | --------------------------------------------- | --------- | ------------------ | ----------- |
| $\mathcal{A}$ (authored)        | **L1** | Manifest declarations, code references        | ?         | hydration §3       | Wave 4      |
| $\mathcal{V}$ (validated)       | **L1** | Validated artifacts (post-schema check)       | ?         | hydration §3       | Wave 4      |
| $\mathcal{P}$ (programs)        | **L1** | Morphism programs (ADD;LINK;MUTATE sequences) | ?         | hydration §3       | Wave 2      |
| $\mathcal{L}_i$ (lens surfaces) | **L1** | UI projections, embeddings, metrics           | ?         | §19, strata Part 2 | Wave 5–6    |

**Gap**: These four categories carry the entire §19 pipeline but have
no defined objects or morphisms. They are §1's "blind boxes" — labels
without content. The functors $V$, $M$, $E$, $P_i$ connecting them
are more precisely defined than the categories they connect.
**Promotion**: Define objects and at least one morphism for each.

#### Functor Codomains (External / Planned)

| Category            | Level  | Objects                | Morphisms   | Defined In    | Realized By      |
| ------------------- | ------ | ---------------------- | ----------- | ------------- | ---------------- |
| $\mathbb{R}^{1536}$ | **L0** | Vectors                | Linear maps | Standard math | Wave 5           |
| $\text{Manifest}$   | **L1** | `manifest.yaml` files  | ?           | §2, arch §3   | Wave 1           |
| $\text{React}$      | **L1** | XYFlow component trees | ?           | §2, arch §3   | FFS3 (external)  |
| $\text{DAG}$        | **L1** | Topological orderings  | ?           | arch §3       | Wave 6 (planned) |

#### Cross-Provider Categories (§9)

| Category                        | Level  | Objects                                           | Morphisms                             | Defined In          | Realized By     |
| ------------------------------- | ------ | ------------------------------------------------- | ------------------------------------- | ------------------- | --------------- |
| $\mathcal{P}_p$ (per-provider)  | **L2** | Model containers owned by provider                | `can_execute` wires, tool invocations | §9, kernel_spec §14 | Wave 6          |
| $\mathcal{C}_{\text{standard}}$ | **L1** | Scored results, capability profiles, cost metrics | Score composition, profile ordering   | §9                  | Wave 6          |
| $\mathcal{C}_{\text{adapter}}$  | **L2** | CompletionRequest, CompletionResult               | Complete(), Stream()                  | kernel_spec §14     | Wave 1 (exists) |

**Gap**: $\mathcal{C}_{\text{standard}}$ is the benchmark target
category — every provider functor lands here — but its morphisms
(score composition, profile ordering) have no formal definition.
Without them, cross-provider comparison has no guaranteed structure
preservation.

#### Paper-Derived Structures

| Structure                          | Level  | Type                                 | Defined In              | Status                                   |
| ---------------------------------- | ------ | ------------------------------------ | ----------------------- | ---------------------------------------- |
| $\mathcal{H}$ (hypervector space)  | **L3** | Algebraic (ring/field, not category) | wolfram_hdc_digest §B   | Reference — realized in Wave 5 embedding |
| $G_H$ (knowledge hypergraph)       | **L2** | Hypergraph $(V, E_H)$                | hypergraphrag_digest §1 | Reference — informs §4 superposition     |
| $\mathcal{P}, \mathcal{G}$ (logic) | **L1** | Propositional sets                   | logicgraph_digest §1    | Reference — informs §14 neuro-symbolic   |

### Summary

```
L3 (fully modeled):    5 categories  — the operational core
L2 (partially modeled): 7 categories  — structure sketched, gaps identified
L1 (named only):        9 categories  — blind boxes carrying functor signatures
L0 (external):          1 category    — inherited from mathematics
Paper structures:       3 structures  — reference, not mo:os-native
```

**The uncomfortable truth**: 9 out of 22 mo:os-native categories are
L1 — named in functor signatures but structurally empty. The hydration
pipeline (§19) chains four functors through three of these blind boxes.
The pipeline is formally defined but its intermediate categories are
not. This is the syn/sem gap applied to the knowledge base itself.

**Promotion protocol** (extends §18 mock lifecycle):

1. For each L1 category, define at least: one non-trivial object, one
   non-identity morphism, composition rule.
2. Verify functoriality of each functor whose domain or codomain
   becomes L2+.
3. Record in the wave that realizes it (greenfield_implementation_waves.md).
4. Update this registry.

**Machine-readable companion**: `../knowledge_base/superset/ontology.json` (+ `.csv`)
contains the canonical registry in structured form. `datasets/` contains
value-layer instances (benchmarks, providers, preferences, workstation).

---

## Locked Agreements Reference

These 9 agreements were reached through multi-session categorical reasoning and are foundational constraints:

1. **Nodes = opaque IDs**, payload = morphism history
2. **Schema = node** (type_id on container), not external constraint
3. **Two access domains**: node (identity) vs edge (policy)
4. **Transitivity**: OWNS = automatic, CAN_HYDRATE = declared
5. **Runtime switching** via wire_config JSONB (temporal + environmental rules)
6. **User graph syncable** — portable edges with diverge/merge model
7. **Linear vs non-linear growth** — formalized cost model (§7)
8. **Manifest = transitivity controller** → dissolves into wires table
9. **Four morphisms are the ONLY invariant** natural transformations of $\mathcal{C}$
