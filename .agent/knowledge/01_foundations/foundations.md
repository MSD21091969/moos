# mo:os — Categorical Foundations

> Consolidated from `_legacy/01_foundations/` — see `_legacy/` for historical versions.
> Version: 3.0 | Date: 2026-07-03 | Locked Agreements: 9

---

## §1 — The One Axiom

Everything in mo:os reduces to one primitive:

$$\forall\, x \in \text{System},\quad x = (\text{urn},\; \Sigma(\text{morphisms}))$$

where $\Sigma : \text{Log} \to \text{State}$ folds the append-only morphism log into the current state.

**Consequences:**

- **Node = opaque identifier.** A URN is a key into `containers`. It has no intrinsic type, no class, no schema beyond what morphisms have written into it. The `state_payload` JSONB is a materialized view of the morphism history — not a source of truth.

  > **Why state_payload is NOT truth.** If `state_payload` were the source of truth, every consumer would have to parse, diff, and reconcile a mutable JSONB blob — there would be no canonical history, no replay, no time-travel, no reconstruction after corruption. The append-only `morphism_log` IS truth because: (a) it is append-only and therefore tamper-evident, (b) any container's current state can be reconstructed by folding $\Sigma : \text{Log} \to \text{State}$, (c) the `containers` and `wires` tables are caches derivable from the log — if they corrupt, replay rebuilds them. Treating `state_payload` as truth would collapse the distinction between *derived state* and *causal history*, making audit, rollback, and federation impossible.

- **User = label on a blind box.** An `AuthUser` is a container whose morphisms grant edges. The user has no special ontological status — it is a label *inside* the container, like all other labels. The difference is *visibility*: user identity labels are projected to admins and share-app users through the UI_Lens functor and connection morphisms, while other labels remain internal. But ontologically, user identity is a MUTATE on `state_payload`, not a privileged category.

- **Code is separated from metadata — and code is ALSO syntax.** Code lives in external stores (git, filesystem). The graph stores only URNs + wires + morphism history. Binding code to state_payload creates structural coupling — a failure mode we call *structural binding loss*.

  This separation exhibits a **symmetry**: just as data in `state_payload` is syntax (structured JSONB parsed by the kernel), code referenced by URNs is *also* syntax — it is a structured representation that becomes semantics only when *evaluated*. Neither code nor metadata carries meaning intrinsically; meaning arises through the evaluation functor (the Go kernel executing morphisms). This is Lawvere's functorial semantics applied: **Syntax** = container schema + code-as-text, **Semantics** = kernel execution, **Bridge** = the structure-preserving functor mapping one to the other.

  **Hydration on evaluation.** Code — including atomic tools at the leaf level — is hydrated (loaded, bound, made executable) only when evaluated. This happens:
  - On each **use** (an agent or user invokes a tool → kernel traverses wires → tool container's code reference is resolved and executed)
  - On each **performance test** in the classification system with conventions (benchmark functor §9 evaluates tool quality → code is hydrated for measurement)

  **Topological use-case context.** Each evaluation must document its *topological state* — the subgraph context in which the code was hydrated. A tool evaluated in workspace A with wires {W₁, W₂, W₃} is a different evaluation than the same tool in workspace B with wires {W₁, W₄}. Only when the evaluation records its position in the hypergraph can nested semantic layering (§8 sub-categories) produce meaningful D/R metrics. Without topological context, benchmark results are context-free and therefore uninterpretable.

  **Reference:** See `papers/Functorial Semantics as a Unifying Perspective.pdf` for the categorical approach to bridging syntax and semantics through decomposition and composition; `papers/HyperGraphRAG.pdf` for hypergraph-aware retrieval that respects topological context.

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

- **Semi-discrete with recursion.** Adjacency is sparse (most node-pairs are unwired). Containers can represent subgraphs (a workspace IS a container that OWNS other containers). This gives fractal nesting without leaving the category.
- **Cycles permitted.** Unlike classical DAGs, $\mathcal{C}$ allows $A \to B \to A$. Cycle detection is a query concern, not a structural prohibition.
- **Finite and enumerable.** Unlike Set, $\mathcal{C}$ has finitely many objects and morphisms at any instant — all stored in Postgres.
- **NOT classical.** $\mathcal{C}$ is not a subcategory of Set. Objects have no internal structure visible to the category — they are opaque identifiers. All structure lives in the morphisms.

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

**What is NOT a functor:** Connections / transport surfaces (HTTP, WebSocket, MCP/SSE) are **morphisms** (wires) in $\mathcal{C}$ — arrows within the category, not structure-preserving maps between categories. A new transport protocol is a new wire implementation, not a new functor. See §5 for how the fan-out pattern from a service to multiple endpoints is correctly modeled as a coslice category.

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

**Completeness:** There is no fifth invariant morphism. DELETE for containers is deliberately absent — you can only UNLINK a container's edges, making it an orphan (invisible to traversal but still in the log).

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

**Query collapses superposition.** Selecting `WHERE source_port = 'owns'` projects the ownership tree from the full hypergraph. Different queries project different subgraphs from the same underlying data.

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

**Why this matters:** One service endpoint that fans out to multiple downstream consumers is not a functor — it is a coslice category. The MOOS kernel dispatching messages to HTTP (:8000), WebSocket (:18789), and MCP/SSE (:8080) simultaneously is the coslice from the kernel node.

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

This functor is what allows the kernel to "zoom out" from a specific fan-out context to the full graph: you drop the information about which wire led you there and work directly with the targets.

### Practical Example: Task Decomposition as Coslice

When an agent decomposes a task into subtasks:
```
AgentWorkspace → subtask_1, subtask_2, subtask_3
```
This is the coslice category `AgentWorkspace/C`. The forgetful functor $U$ maps each subtask wire to its target container, enabling traversal of subtask results independently of how they were assigned. The commuting triangles capture subtask dependencies (if subtask_2 depends on subtask_1, there's a morphism between them in the coslice).

---

## §6 — Containers as Categories: Full Subcategories via OWNS

A container $W$ with OWNS children is **simultaneously** an object in $\mathcal{C}$ **and** a category in its own right.

### Full Subcategory $\mathcal{C}_W \hookrightarrow \mathcal{C}$

Given container $W$ that OWNS $\{c_1, c_2, \ldots, c_m\}$:

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

This gives the fractal structure mentioned in §2. A workspace contains projects, which contain files, which contain functions — each level is a full subcategory of the one above.

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

The rules that filter potential edges into actual edges ARE the system's intelligence. Every business rule, permission check, schema constraint, and ontological decision is a filter that reduces $10^8$ potential edges to the $k$ that actually exist.

### Discovery Cost

$$\text{Cost}_{\text{discovery}} = O(|E_{\text{scope}}| \times c_{\text{index}})$$

where:
- $|E_{\text{scope}}|$ = candidate edges in the evaluated scope
- $c_{\text{index}}$ = per-node metadata density (schema JSONB size + state_payload complexity)

Discovery builds the index BY scanning. More metadata per node = slower scan, richer result. This is not a bug — it's a fundamental tradeoff.

### Retrieval Cost

$$\text{Cost}_{\text{retrieval}} = O(k + 1)$$

where $k$ = batch of node payloads, $1$ = pre-computed tree index (the collapsed superposition from §4). Retrieval is asymptotically free because the structure was pre-solved during discovery.

### D/R Ratio: Per-Sub-Category Optimization Metric

$$\frac{D}{R} = \frac{\text{Cost}_{\text{discovery}}}{\text{Cost}_{\text{retrieval}}}$$

The D/R ratio is computed per sub-category (§8):

| D/R Ratio    | Meaning                                      | Optimization Strategy                        |
| ------------ | -------------------------------------------- | -------------------------------------------- |
| High D (≫ R) | Schema is evolving, edges change frequently  | Pre-compute + cache subgraph structure       |
| High R (≫ D) | Schema is stable, mostly fetching known data | Optimize batch fetching, payload compression |
| D ≈ R        | Balanced                                     | Monitor for drift                            |

**Edge-defined relevance:** Edges define node RELEVANCE, not existence. An orphan node (zero edges) exists in `containers` but is invisible to every traversal. Relevance is structural, not intrinsic.

---

## §8 — Sub-Categories: Typed Port Signatures

Port preferences partition $\text{Hom}(A,B)$ into named channels, inducing sub-categories of $\mathcal{C}$.

**Formal definition:** A sub-category $\mathcal{C}_\sigma$ is a full subcategory of $\mathcal{C}$ induced by the set of objects sharing a port signature vocabulary $\sigma$.

**Relationship to §6:** Port-signature sub-categories ($\mathcal{C}_\sigma$) and OWNS-based subcategories ($\mathcal{C}_W$) are orthogonal partitions of $\mathcal{C}$. A container can belong to both an OWNS subcategory (structural containment) and a port-signature subcategory (behavioral role). Their intersection $\mathcal{C}_W \cap \mathcal{C}_\sigma$ gives "containers owned by $W$ that participate in the $\sigma$ vocabulary" — the scoped behavioral slice.

**Properties:**

- Each user's port preferences = their personal projection of the hypergraph.
- Union of all users' port preferences = the active schema vocabulary.
- Zero-use edge types (ports never queried by any user) = candidates for UNLINK — graph hygiene.
- Per-schema D/R ratio (§7) = optimization signal for data pipelines.

**Example:** If agents use ports `{can_execute, data_flow}` and humans use ports `{owns, can_hydrate}`, these are distinct sub-categories with different D/R profiles and different optimization strategies.

---

## §9 — Benchmarks as Functors

A benchmark $B$ defines a structure-preserving map:

$$B: \mathcal{C}_{\text{provider}} \to \mathcal{C}_{\text{standard}}$$

**Structure preservation:**
- Objects in the provider category (e.g., model containers from different LLM vendors) map to objects in a standard evaluation category
- Morphisms (wires between provider objects) map to standard morphisms, preserving composition
- Cross-provider comparison = comparing functor images in $\mathcal{C}_{\text{standard}}$

**Key insight (LogicGraph reference):** Benchmarks don't test models in isolation — they test the quality of the projected graph structure that models traverse. Multi-path logical reasoning benchmarks specifically measure hypergraph traversal quality.

### Functoriality = Why Process-Verified Evaluation Works

The benchmark functor $B$ must preserve composition:

$$B(g \circ f) = B(g) \circ B(f)$$

**This is the categorical reason why process-verified evaluation outperforms outcome-only evaluation.** When evaluating a composed pipeline (e.g., agent decomposes task → subtasks execute → results compose), the benchmark MUST evaluate each step and verify that composed step-evaluations equal the evaluation of the composed result. If you only evaluate the final outcome, you violate functoriality — you lose the compositional structure that makes the evaluation meaningful.

**Concretely:** Given a coslice decomposition (§5) where agent $A$ fans out to subtasks $\{f_1, f_2, f_3\}$, the benchmark must score each $f_i$ independently AND verify that $B(f_3 \circ f_2 \circ f_1) = B(f_3) \circ B(f_2) \circ B(f_1)$. Outcome-only evaluation checks the left side. Process-verified evaluation checks the right side AND the equation.

**Benchmark suites** = families of functors parameterized by task type:

$$\{B_t : \mathcal{C}_{\text{provider}} \to \mathcal{C}_{\text{standard}}\}_{t \in \text{Tasks}}$$

This replaces ad-hoc "accuracy on dataset X" with a categorical framework where the comparison itself preserves compositional structure.

---

## §10 — GPU Structure Functor

$$F_{\text{struct}}: \text{subgraph} \to \text{compressed DAG}$$

**Traditional pipeline:**
```
raw content → LLM prompt → LLM discovers structure → answer
```

**Proposed pipeline:**
```
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

**Benefit:** Reduces LLM token cost by providing pre-analyzed structure. Forces structural awareness before the LLM call, preventing the model from wasting tokens rediscovering graph topology.

---

## §11 — Two Access Domains

**Locked Agreement #3.** Access is split into two orthogonal domains:

| Domain          | Controls                 | Mechanism                                         |
| --------------- | ------------------------ | ------------------------------------------------- |
| **Node access** | Identity — who you ARE   | Auth user has a key (URN) for containers they own |
| **Edge access** | Policy — what you CAN DO | Any rule: global, local, temporal, env-based      |

**Why two domains?** If access were node-only, you couldn't have shared resources. If access were edge-only, you couldn't have identity. The split allows: "User A owns node X" (node domain) AND "Users with role Y can hydrate node X" (edge domain) simultaneously.

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

**Relationship to §6:** OWNS transitivity is the mechanism that defines subcategory membership. The recursive CTE computes $\text{Ob}(\mathcal{C}_W)$ by following transitive OWNS chains.

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

**Separation principle:** Embeddings are **functor output**, not graph metadata. They are stored separately (`container_embeddings`, not `state_payload`) and regenerated on every MUTATE. This prevents functor-as-metadata pollution.

**Discovery complement:** Vector search finds semantically similar containers that may not be wired. This complements graph traversal (which finds structurally connected containers). The two discovery modes are orthogonal.

---

## §14 — The Syntax/Semantics Bridge: Functorial Decomposition and Composition

mo:os instantiates Lawvere's functorial semantics (1963) as an operational architecture, not just a theoretical model. The key insight: **syntax and semantics are separate categories connected by a structure-preserving functor**.

### The Bridge

| Layer                                                                 | Role                                                                 | In mo:os                                                               |
| --------------------------------------------------------------------- | -------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| **Syntax category** $\mathcal{S}$                                     | Structure of the language — types, ports, wiring rules, code-as-text | Container schema, `wires` topology, code references in `state_payload` |
| **Semantics category** $\mathcal{M}$                                  | Meaning of the language — what happens when evaluated                | Go kernel morphism execution, LLM outputs, tool results                |
| **Evaluation functor** $F_{\text{eval}}: \mathcal{S} \to \mathcal{M}$ | Structure-preserving map from syntax to semantics                    | Kernel pipeline $\Sigma$ — the reducer (§1)                            |

**Structure preservation** means: if two syntactic elements compose in $\mathcal{S}$ (e.g., two wired containers), their semantic evaluations compose identically in $\mathcal{M}$. This is the naturality condition for the four invariant morphisms (§3).

**The evaluation functor IS the reducer $\Sigma$.** The kernel pipeline (Connection → Route → Dispatch → Transform → Commit) is a concrete implementation of the functor $F_{\text{eval}}: \mathcal{S} \to \mathcal{M}$ — it takes syntactic structure (containers, wires, morphism requests) and produces semantic results (state changes, committed to the log). The catamorphism $\Sigma: \text{Log} \to \text{State}$ is $F_{\text{eval}}$ applied iteratively over the full morphism history.

### Decomposition and Composition Are Categorical Duals

**Decomposition** (analysis): Given a complex container subgraph, decompose into atomic morphisms (ADD, LINK, MUTATE, UNLINK). Every subgraph operation has a unique decomposition into these four invariants. This is guaranteed by §3's completeness.

**Composition** (synthesis): Given a sequence of atomic morphisms, compose into a coherent subgraph transformation. The semicolon operator `;` composes morphism programs. The result is verifiable: replay the log and check.

The critical property: **decomposition followed by composition is identity** (up to ordering of independent morphisms). This is NOT true for LLM-based task decomposition, where:
- Decomposition is LLM-generated (can hallucinate)
- Recomposition has no formal guarantees
- Subtasks can be incompatible

mo:os avoids this by decomposing into *mathematically invariant* operations, not natural-language task descriptions.

### The Neuro-Symbolic Implication (System 3 Reasoning)

The System 3 transcript (`transcripts/system 3.txt`) and `papers/LogicGraph  Benchmarking Multi-Path Logical Reasoning.pdf` establish that:

1. **LLMs prioritize semantic fluency over logical entailment.** They build linguistically plausible but logically invalid bridges between known start and end states (result-oriented hallucination).
2. **Neuro-symbolic pipelines** escape this by anchoring language models to symbolic engines (Prover9, Lean 4, Python verification).
3. **Process-verified rewards** (per-step verification) outperform outcome-verified rewards (final-answer-only) for complex reasoning. **This is functoriality** — see §9 for why preserving composition at each step is categorically required.

**How mo:os already implements this:**
- The kernel IS the symbolic engine — it speaks containers, wires, and the four invariant morphisms (pure logic, zero hallucination)
- LLMs are **Fuzzy Processing Units** — sandboxed coprocessors that propose morphisms, which the kernel validates against the graph structure before committing
- Every morphism step is logged and verifiable (process-level audit, not just outcome)
- Multi-path reasoning = hypergraph traversal through multiple port types simultaneously (§4 superposition)
- Task decomposition by agents produces coslice categories (§5) — the forgetful functor $U$ recovers the target containers from the decomposition structure

**What this means for evaluation:**
- Benchmarks (§9) should be structured as neuro-symbolic verification: LLM proposes → kernel decomposes → each step verified against graph constraints → process reward computed
- The LogicGraph error taxonomy (semantic misinterpretation, information omission, fact hallucination, invalid deduction, rule misapplication, insufficient premise) maps to specific failure modes in morphism decomposition
- Functoriality of the benchmark (§9) ensures that step-by-step evaluation is categorically consistent with end-to-end evaluation

### Paper References

| Paper                                                     | Key Contribution to mo:os                                                                                                |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **Functorial Semantics as a Unifying Perspective**        | Categorical decomposition/composition guarantees; syntax/semantics bridge formalization                                  |
| **HyperGraphRAG**                                         | Hypergraph-aware retrieval that preserves topological context during RAG operations                                      |
| **LogicGraph: Benchmarking Multi-Path Logical Reasoning** | Error taxonomy for LLM reasoning failures; neuro-symbolic verification pipeline; multi-path graph traversal as benchmark |
| **Seven Sketches in Compositionality** (Fong & Spivak)    | Monoidal categories, operads, wiring diagrams — the mathematical vocabulary of mo:os                                     |

---

## §15 — Morphism Log as Ground Truth

The append-only `morphism_log` table is the single source of truth:

```sql
SELECT new_state FROM morphism_log
WHERE target_urn = :x
ORDER BY id DESC LIMIT 1
```

This reconstructs the current state of any container.

**Implications:**
- `containers.state_payload` is a **cache** — a materialized view of the latest morphism.
- `wires` table is a **cache** — the current set of active edges derived from LINK/UNLINK history.
- Time-travel: replay morphisms up to any timestamp to reconstruct historical state.
- Audit: every state change has an author, timestamp, and previous state.
- Reconstruction: if `containers` and `wires` tables are corrupted, they can be rebuilt from `morphism_log` alone.

**Σ as replay.** The reducer $\Sigma: \text{Log} \to \text{State}$ (§1) is precisely this reconstruction operation. Folding the morphism log produces the current state. The log IS the category's morphism history; the state IS the colimit.

---

## §16 — Field Research Placeholder

Empirical observation categories for future validation:

| Metric                          | What It Measures                                    | Source                           |
| ------------------------------- | --------------------------------------------------- | -------------------------------- |
| Morphism frequency distribution | Which of the 4 morphisms dominate in real usage     | `morphism_log`                   |
| Edge density $k/(n^2 \cdot      | P_s                                                 | \cdot                            | P_t | )$ | How sparse the actual graph is vs multi-port theoretical max (§7) | `wires` + `containers` count + port type cardinality |
| Traversal depth                 | Average/max path length in ownership trees          | Recursive CTE on `wires`         |
| Replay cost                     | Time to reconstruct state from morphism_log         | Benchmark on `morphism_log` size |
| Hypergraph fanout               | Average number of distinct port types per node-pair | `wires` GROUP BY source/target   |
| Coslice cardinality             | Average fan-out degree per node                     | `wires` GROUP BY source_urn      |
| Subcategory depth               | Max nesting level of OWNS chains                    | Recursive CTE depth counter      |

**Method:** Prometheus metrics at `/metrics` endpoint + direct SQL queries on `morphism_log`. These observations will validate or falsify the cost model (§7) and sub-category analysis (§8) once production data exists.

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
