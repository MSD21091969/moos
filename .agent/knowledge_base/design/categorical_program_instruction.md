# Instruction: Write a Kernel Program — Categorical Dependencies Only

**Date:** 2026-03-09  
**Status:** Abstract specification — no implementation decisions  
**Depends on:** ../doctrine/hypergraph.md, 20260309-hypergraph-approach.md

---

## Rule

Every dependency is a categorical construct. If it doesn't appear in the toolkit below, it doesn't exist. No libraries, no frameworks, no packages — only objects, morphisms, and the structures they compose into.

---

## CT Toolkit

| CT Construct                                                                               | What it does                                                                    | Kernel analog                                                                                                       |
| ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **Object**                                                                                 | A thing with identity                                                           | Kind — the type of a node                                                                                           |
| **Morphism**                                                                               | An arrow between objects                                                        | The four NTs (ADD/LINK/MUTATE/UNLINK)                                                                               |
| **Category**                                                                               | Objects + morphisms + composition + identity law                                | A named scope where specific Kinds and morphism types are valid                                                     |
| **Functor**                                                                                | Structure-preserving map between categories                                     | Projections (UI lens, embedding, benchmark)                                                                         |
| **Natural Transformation**                                                                 | Morphism between functors                                                       | The four NTs themselves — they transform state functors                                                             |
| **Operad**                                                                                 | Multi-input typed operation signatures                                          | The ontology — colors are Kinds, operations are morphism types, arities are port counts                             |
| **Algebra**                                                                                | An implementation over a signature                                              | Any process that consumes envelopes and produces state                                                              |
| **Initial Algebra**                                                                        | The free structure — no equations, just syntax                                  | The morphism log (free monoid of envelopes)                                                                         |
| **Carrier**                                                                                | The set an algebra operates on                                                  | GraphState                                                                                                          |
| **Catamorphism**                                                                           | The unique fold from initial algebra to any algebra                             | Replay: $\text{fold}(\text{Evaluate}, \emptyset, \text{log})$                                                       |
| **Product** $A \times B$                                                                   | Both A and B together                                                           | A node that participates in two relations simultaneously                                                            |
| **Coproduct** $A + B$                                                                      | Either A or B                                                                   | Kind union — "this port accepts User OR Group"                                                                      |
| **Terminal object** $1$                                                                    | The unique thing everything maps to                                             | The empty graph ∅ (initial state)                                                                                   |
| **Initial object** $0$                                                                     | The thing that maps to everything                                               | The empty envelope list (trivial log)                                                                               |
| **Hom-set** $\text{Hom}(A,B)$                                                              | All morphisms from A to B                                                       | All legal wires from Kind A to Kind B (port-constrained)                                                            |
| **Slice** $\mathcal{C}/X$                                                                  | Everything over X                                                               | The subcategory reachable via OWNS from node X (scope)                                                              |
| **Subobject classifier** $\Omega$                                                          | Truth values for "is this in the sub-thing?"                                    | Queries — a filter predicate on the graph                                                                           |
| **Adjunction** $F \dashv G$                                                                | A free/forgetful pair                                                           | Free construction (build from log) ⊣ Forgetful (extract state)                                                      |
| **Monad** $T = G \circ F$                                                                  | Composed adjunction — wraps effects                                             | The apply-and-return cycle: read state → evaluate → write state                                                     |
| **Concrete category**                                                                      | A category with a faithful functor to **Set**                                   | An implementation language — it grounds abstract objects into machine-representable sets                            |
| **Topos**                                                                                  | A category with limits, exponentials, and $\Omega$                              | The execution environment — it provides the "universe" in which objects can be constructed, stored, queried         |
| **Enriched category**                                                                      | Hom-sets carry extra structure (not just sets, but objects in another category) | A type system — hom-sets become typed function signatures, not raw sets of arrows                                   |
| **Presheaf** $[\mathcal{C}^{\text{op}}, \mathbf{Set}]$                                     | A functor from the opposite category to Set                                     | A file tree — contravariant: deeper paths restrict, parent paths include                                            |
| **Yoneda embedding** $\mathcal{C} \hookrightarrow [\mathcal{C}^{\text{op}}, \mathbf{Set}]$ | Every object is fully determined by its relationships                           | A module/package system — an object is known by what maps into it (its imports) and what it maps to (its exports)   |
| **Monoidal category**                                                                      | A category with a tensor product $\otimes$ and unit $I$                         | A build pipeline — $\otimes$ is sequential composition of transforms, $I$ is source (identity build = no transform) |
| **String diagram**                                                                         | A 2D notation for morphisms in monoidal categories                              | A wire protocol — boxes are endpoints, strings are channels, composition is message flow                            |

---

## Step 0 — Choose the concrete category (language)

A **concrete category** is a category $\mathcal{C}$ equipped with a faithful functor $U: \mathcal{C} \to \mathbf{Set}$. "Faithful" means: for every pair of objects $A, B$, the map $U: \text{Hom}(A,B) \to \text{Hom}(UA, UB)$ is injective — no two distinct morphisms in $\mathcal{C}$ become the same function on sets.

A programming language IS a concrete category:

- Objects = types
- Morphisms = functions between types
- $U$ = the mapping from types to their underlying value sets (e.g., `int` → ℤ ∩ [−2³¹, 2³¹))
- Faithful = type-safe: different typed functions remain different at the set level

**Why this matters:** The language choice determines which hom-sets are expressible. A language with sum types (coproducts) can express $A + B$ directly. One without them must encode it (e.g., interface + type switch). The choice of concrete category constrains which categorical constructs are **native** vs. **encoded**.

**Specify:** One concrete category. Justify by which constructs it makes native.

---

## Step 1 — Choose the topos (runtime environment)

A **topos** is a category with:

- Finite limits (you can construct products, equalizers — i.e., you can match patterns and combine data)
- Exponentials $B^A$ (you can treat morphisms as objects — first-class functions)
- A subobject classifier $\Omega$ (you can ask "is this element in this subset?" — predicates, queries, filters)

A runtime environment IS a topos:

- Limits = memory allocation, data structure construction
- Exponentials = closures, callbacks, function pointers
- $\Omega$ = boolean predicates on runtime state

**Why this matters:** The topos determines what questions the running program can answer about itself. A topos with rich $\Omega$ (e.g., a runtime with reflection) can classify subobjects dynamically. A minimal topos (bare metal, no reflection) limits queries to compile-time decisions.

**Specify:** One topos. Justify by what limits, exponentials, and $\Omega$ it provides.

---

## Step 2 — Choose the presheaf (directory structure)

A **presheaf** on a category $\mathcal{C}$ is a functor $F: \mathcal{C}^{\text{op}} \to \mathbf{Set}$. Contravariance means: a morphism $A \to B$ in $\mathcal{C}$ induces a restriction $F(B) \to F(A)$ — going deeper narrows scope.

A directory tree IS a presheaf:

- Objects in $\mathcal{C}$ = directories (nodes in the tree)
- Morphisms = inclusion (parent → child)
- $F(\text{dir})$ = the set of source files in that directory
- Contravariance = a file deeper in the tree is more specialized (narrower scope)

**Why this matters:** The directory structure determines the **restriction maps** — what is visible from where. A file in `internal/core/` cannot see `internal/shell/` — the restriction map from `internal/` to `core/` forgets everything outside `core/`. This IS the purity boundary. It's not a convention — it's a categorical constraint.

**Specify:** One presheaf. Justify by which restriction maps enforce which visibility boundaries.

---

## Step 3 — Choose the Yoneda embedding (module/package system)

The **Yoneda lemma** says: $\text{Nat}(\text{Hom}(-, A), F) \cong F(A)$. An object is completely determined by the natural transformations from its representable functor to any other functor. In practice: **a module is known entirely by its imports (what maps into it) and its exports (what it maps to).**

A package manager IS a Yoneda embedding:

- $\text{Hom}(-, A)$ = the set of all modules that import module $A$ (dependents)
- $F(A)$ = the content of module $A$
- The embedding says: if you know all the ways $A$ is used (all dependents) and all the things $A$ provides (exports), you know $A$ completely

**Why this matters:** Dependencies are morphisms in the module category. Adding a dependency = adding a morphism. The Yoneda perspective forces you to ask: "what does this import reveal about my module's identity?" Every dependency reshapes what your module IS — not just what it uses.

**Specify:** One embedding. Justify by which morphisms (imports) are admitted and which are forbidden.

---

## Step 4 — Choose the monoidal category (build pipeline)

A **monoidal category** $(\mathcal{C}, \otimes, I)$ has:

- A tensor product $\otimes$ — a bifunctor $\mathcal{C} \times \mathcal{C} \to \mathcal{C}$ (combines two objects into one)
- A unit $I$ — the identity for $\otimes$ ($A \otimes I \cong A$)
- Associativity and unit coherence (up to natural isomorphism)

A build pipeline IS a monoidal category:

- Objects = artifact states (source, compiled, linked, bundled, deployable)
- $\otimes$ = sequential composition of build steps
- $I$ = the source artifact (the identity transform — no build = source)
- Associativity = $(A \otimes B) \otimes C \cong A \otimes (B \otimes C)$ — rearranging build steps within an equivalence class doesn't change the output

**Why this matters:** The build tool defines the tensor product. Different tools give different $\otimes$: a compiler composes source → object, a linker composes objects → binary, a bundler composes modules → bundle. Each is a morphism in the monoidal category. The unit $I$ tells you what "no build" means — if $I$ = source and the program runs without building, you have an interpreted language (the identity morphism IS execution).

**Specify:** One monoidal category. Justify by what $\otimes$ is, what $I$ is, and what coherence constraints the build steps satisfy.

---

## Step 5 — Choose the string diagram (wire protocol)

A **string diagram** is the graphical notation for morphisms in a monoidal category. Boxes are morphisms (processes), strings are objects (channels), and composition is spatial adjacency:

- Horizontal composition = parallel ($\otimes$)
- Vertical composition = sequential ($\circ$)
- Crossings = symmetry (the braiding, if the category is symmetric monoidal)

A wire protocol IS a string diagram:

- Boxes = endpoints (processes that send/receive)
- Strings = channels (typed message flows between endpoints)
- $\otimes$ = multiplexing (parallel channels on the same connection)
- $\circ$ = message sequencing (response follows request)
- Braiding = routing (messages can cross between channels without interference)

**Why this matters:** The protocol defines the morphisms between distributed algebras. Two processes running the same operad (same ontology) communicate by exchanging elements of the free monoid (envelopes). The string diagram specifies HOW those elements flow — serialization format, transport, multiplexing, ordering guarantees. It does NOT specify WHAT flows — that's the operad's job.

**Specify:** One string diagram. Justify by what the boxes are, what the strings carry, and what the braiding guarantees.

---

## Step 6 — Declare the operad

Define every **color** (Kind) the program will touch. For each color, declare:

- Its **identity** — what makes two instances distinct (the URN)
- Its **ports** — named, typed slots. Each port has a **color constraint** (which Kinds may connect there) and an **arity** (how many connections that slot admits)
- Its **stratum** — which layer it lives on (S0–S4)

This is the **signature**. Nothing else exists until this is written.

---

## Step 7 — Declare the hom-sets

For every pair of colors $(A, B)$, enumerate the **morphisms** between them — the legal wires, typed by port. Each morphism specifies:

- **Source port** on $A$
- **Target port** on $B$
- **NT** it decomposes into (which sequence of ADD/LINK/MUTATE/UNLINK)

If $\text{Hom}(A, B) = \emptyset$ for a pair, those Kinds cannot relate. This IS the access control.

---

## Step 8 — Define the initial algebra

The **carrier** is the state type — a presheaf $G: \mathcal{O}^{\text{op}} \to \mathbf{Set}$ where $\mathcal{O}$ is the operad from step 6.

The **initial algebra** is the free monoid on the four NTs. A program is an element of this monoid — a finite list of typed rewrites.

The **algebra map** is the evaluator: given current state $G$ and one envelope $e$, produce $G'$. This map must:

- Respect the operad (reject envelopes that violate port constraints)
- Be deterministic ($G + e = G'$ always)
- Be total on valid inputs

---

## Step 9 — Define the functors

Each **consumer** of the state is a functor $F: \mathcal{C} \to \mathcal{D}$ where:

- $\mathcal{C}$ is the graph category
- $\mathcal{D}$ is the target category

The functor must be structure-preserving and read-only. S4 outputs are never ground truth.

---

## Step 10 — Define the algebras (clients)

Every process that writes to the graph is an algebra over the operad:

$$\alpha: \text{State} \to [\text{Envelope}]$$

This includes the UI, the agent, a test harness, a migration script. They are all the same type. They differ only in which function body produces the envelopes. The operad constrains what they may emit — not what they are.

A mock is the trivial algebra: $\alpha(\text{any}) = []$

---

## Step 11 — Compose via catamorphism

$$\text{cata}: \text{Free}(\text{NT}) \to \text{State}$$

The only execution model. Every state change passes through this fold.

---

## Step 12 — Validate via subobject classifier

Queries are characteristic morphisms $\chi: G \to \Omega$. A test is a query that asserts a subgraph exists (or doesn't). Testing = applying $\chi$ to the carrier after folding.

---

## The Complete Dependency Table

| Decision         | CT Construct              | What you declare                                                    |
| ---------------- | ------------------------- | ------------------------------------------------------------------- |
| Language         | Concrete category         | Objects (types), morphisms (functions), faithful functor to **Set** |
| Runtime          | Topos                     | Limits, exponentials, subobject classifier                          |
| Directory layout | Presheaf                  | Restriction maps (visibility boundaries)                            |
| Package system   | Yoneda embedding          | Admitted morphisms (imports/exports)                                |
| Build tool       | Monoidal category         | Tensor product (build steps), unit (source), coherence              |
| Wire protocol    | String diagram            | Boxes (endpoints), strings (channels), braiding (routing)           |
| Type system      | Operad                    | Colors (Kinds), operations (morphisms), arities (ports)             |
| State model      | Initial algebra + carrier | Free monoid (log) + presheaf (graph)                                |
| Execution model  | Catamorphism              | Unique fold from initial algebra to carrier                         |
| Read path        | Functors                  | Structure-preserving projections                                    |
| Write path       | Algebras                  | $\text{State} \to [\text{Envelope}]$                                |
| Test/query       | Subobject classifier      | Characteristic morphisms $G \to \Omega$                             |

Nothing else. If it's not in this table, it's not a dependency — it's an accident.
