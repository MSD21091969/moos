# Next Session: Wave 0 Findings, Gaps, and Recommendations

**Session date:** 2026-03-09  
**Source:** Conversation from "can we fix this?" onward  
**Status:** Actionable — items below block Wave 1 correctness

---

## How to read this document

Each finding has:

- **What** — the concrete gap or flaw
- **Why** — the categorical reason it matters
- **Recommendation** — the minimum correct action
- **Wave** — earliest wave at which this should be resolved

Items are ordered by severity: correctness first, then structural, then strategic.

---

## F1 — `Kind=Kernel` and `Kind=Feature` are unregistered types

**What**  
Wave 0 seeds two Kinds — `Kernel` and `Feature` — that do not appear anywhere in `ontology.json` OBJ01–OBJ13. They were invented during implementation without consulting the existing object registry.

**Why**  
The SemanticRegistry loaded at boot is derived from `ontology.json`. When `EvaluateWithRegistry` checks whether a node's Kind is admissible, it looks up the Kind in that registry. If `Kernel` and `Feature` are not registered, the constraint system cannot enforce stratum rules, permitted ports, or inter-Kind wire constraints for those nodes. The graph is structurally valid (the fold runs) but semantically unconstrained for the two most important nodes it contains.

**Reference:** `internal/shell/registry_loader.go` → `LoadRegistry()`; `ontology.json` OBJ01–OBJ13

**Recommendation**  
Two options, pick one:

Option A (preferred) — Map to existing Kinds:

- `urn:moos:kernel:wave-0` → `Kind=NodeContainer` (OBJ05) or define a new OBJ14 `Kernel` in the ontology before seeding
- `urn:moos:feature:*` → examine each: pure-graph-core, append-only-log, program-composition, semantic-registry, hydration-materialize are genuine system capabilities → define OBJ14 `SystemCapability`; http-api belongs under F2 below

Option B — Register the new Kinds formally:

- Add `Kernel` as OBJ14 and `Feature` as OBJ15 to `ontology.json` with explicit broad_category, source_connections, target_connections, and allowed strata
- Re-run `seedKernel()` against the updated registry to verify no violations

**Wave:** 0 correction — before any external code depends on these Kind strings

---

## F2 — `urn:moos:feature:http-api` has the wrong Kind

**What**  
`urn:moos:feature:http-api` is seeded as `Kind=Feature`. The ontology already defines `OBJ11 ProtocolAdapter`: "WS channel, MCP session, gRPC stream, HTTP endpoint — routable communication container." The correct Kind is `ProtocolAdapter`, and the correct URN namespace is `adapter`, not `feature`.

**Why**  
Feature nodes (`Kind=Feature`) represent intrinsic kernel capabilities — things whose removal changes what the kernel _can do_ (e.g. program composition, semantic registry). A transport binding changes only how the kernel is _reached_. Conflating these two prevents the graph from answering "what transports are active?" independently from "what capabilities does the kernel have?" — which are distinct queries with distinct governance implications.

This is a concrete violation of Normalization Rule 4 (Semantics before transport): the transport binding has been given semantic status as a kernel capability when it is a deployment-surface concern.

**The correct graph representation:**

```
ADD  urn:moos:adapter:http    Kind=ProtocolAdapter  S2
LINK urn:moos:kernel:wave-0 [exposes] → urn:moos:adapter:http [binding]
```

Adding gRPC, WebSocket, or MCP/SSE later follows the same pattern — each becomes a ProtocolAdapter node with its own URN, linked to the kernel via the `exposes → binding` port pair. The query `GET /graph/nodes?kind=ProtocolAdapter&stratum=S2` answers "what transports are live?" without any env var or config file.

**Reference:** ontology.json OBJ11; `internal/core/types.go`; `cmd/kernel/main.go` seedKernel()  
**See also:** Category theory — subcategory separation; [Lawvere's functorial semantics](https://ncatlab.org/nlab/show/functorial+semantics) for the objects/observers distinction

**Recommendation**

1. In `ontology.json`: add morphism type `exposes / binding` (MOR17) between Kernel and ProtocolAdapter
2. In `seedKernel()`: replace the `http-api` Feature ADD+LINK with a ProtocolAdapter ADD+LINK using the new port names
3. Update CLAUDE.md Wave 0 facts table accordingly

**Wave:** 0 correction

---

## F3 — The morphism log store has no graph presence

**What**  
`platform/kernel/data/morphism-log.jsonl` — the JSONL file store — is the single source of truth per AX3. Yet it has no node in the graph. The store is an infrastructure dependency of the kernel, not an observable graph object.

**Why**  
OBJ12 `InfraService` is defined as: "Postgres instance, disk volume, network segment — persistable infrastructure container." The JSONL file store is precisely an InfraService. Without a node for it:

- The graph cannot express which store the kernel is using
- Switching to Postgres (via `MOOS_KERNEL_STORE=postgres`) is invisible in the graph
- Future governance over store migration has no anchor point

**Recommendation**

```
ADD  urn:moos:infra:log-store-file     Kind=InfraService  S2  { "type": "jsonl", "path": "data/morphism-log.jsonl" }
LINK urn:moos:kernel:wave-0 [persists] → urn:moos:infra:log-store-file [store]
```

Add `persists / store` as MOR18. When Postgres is active, seed `urn:moos:infra:log-store-postgres` instead.

**Wave:** 1

---

## F4 — `urn:moos:kernel:self` is an actor with no node

**What**  
Every envelope in the log carries an `actor` URN. `urn:moos:kernel:self` signs all 13 boot morphisms. It does not exist as a node in the graph — there is no `ADD` for it. This means:

- You cannot traverse "what did `urn:moos:kernel:self` issue?" as a graph query — only as a log scan
- AX5 ("governance is structural") cannot be applied to kernel-issued morphisms because the actor has no identity in the structure it governs
- The actor/morphism relationship is invisible to the graph's own projection mechanisms

**Why this is deeper than it looks**  
In the categorical model, an actor is an object in the identity subcategory (SUB01). Every OWNS morphism, every CAN_HYDRATE wire, every governance constraint is anchored to an identity node. An actor that signs morphisms but has no node is a morphism without a source object — categorically malformed.

**Reference:** ontology.json SUB01; AX5; `cmd/kernel/main.go` actor constant  
**See also:** [Lawvere theories](https://ncatlab.org/nlab/show/Lawvere+theory) — typed algebraic structure where every operation symbol has a source type

**Recommendation**

```
ADD  urn:moos:kernel:self   Kind=SystemCapability (or a new OBJ for Kernel identity)  S2
```

This should be the first morphism in `seedKernel()` — the actor must exist before it can sign anything. Actor governance wires (which actors may issue which morphism types against which target Kinds) are Wave 2+, but the node must exist now.

**Wave:** 0 correction

---

## F5 — Catamorphism is overstated in CLAUDE.md and README.md

**What**  
Both documents say "the kernel _is_ a catamorphism." This is imprecise.

**The precise statement:**  
`EvaluateWithRegistry(state, envelope) → (EvalResult, error)` is the **algebra map** — the step function.  
`foldl Apply ∅ log[0..t]` is the **catamorphism** — the unique morphism out of the initial algebra (the free monoid of envelopes) into the graph state algebra.  
The kernel _implements_ a catamorphism. It also contains IO, concurrency (RWMutex), store persistence, HTTP transport. Those are not folds. The full kernel container is not a pure catamorphism — it hosts one.

**Formal statement:**  
Let **Env** be the free monoid on the set of envelope types {ADD, LINK, MUTATE, UNLINK}.  
Let **State** be the carrier of the algebra `(GraphState, EvaluateWithRegistry)`.  
The catamorphism `cata : Env → State` is the unique monoid homomorphism such that `cata([e₁,...,eₙ]) = EvaluateWithRegistry(cata([e₁,...,eₙ₋₁]), eₙ)`.  
This homomorphism is what replay executes. It is unique (AX3 guarantee) because `State` is an `Env`-algebra and `Env` is initial among those.

**Reference:** [nLab: catamorphism](https://ncatlab.org/nlab/show/catamorphism); [Meijer, Fokkinga, Paterson — Functional Programming with Bananas, Lenses, Envelopes and Barbed Wire (1991)](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.41.125)  
**See also:** Initial algebra semantics; F-algebras; fold/unfold duality (anamorphism for log replay, catamorphism for state reconstruction)

**Recommendation**  
Replace "the kernel _is_ a catamorphism" with "the kernel _implements_ a catamorphism — `EvaluateWithRegistry` is the algebra map; replay over the morphism log is the fold" in both README.md and CLAUDE.md.

**Wave:** 0 doc correction

---

## F6 — Protocol is not a category; the term needs pinning

**What**  
CLAUDE.md states "Protocol = morphism-level routing — not a functor, not a category." This is correct but under-specified. The practical consequence — where protocol bindings live in the system — needs a canonical formulation that can be applied consistently when adding new transports.

**The precise picture:**

```
External world              Effect shell                    Pure core
────────────────            ──────────────────────────      ──────────────
HTTP POST /morphisms   →    decode([]byte) → Envelope  →   EvaluateWithRegistry
gRPC Unary call        →    decode([]byte) → Envelope  →   EvaluateWithRegistry
MCP/SSE frame          →    decode([]byte) → Envelope  →   EvaluateWithRegistry
WebRTC data channel    →    decode([]byte) → Envelope  →   EvaluateWithRegistry

EvalResult             ←    encode(result) → []byte    ←   graph state
```

A protocol binding is a **decode/encode pair on the IO boundary of the effect shell**. In the model it is:

- Not an object (no URN, no Kind, no Stratum)
- Not a morphism (does not change graph state)
- Not a functor (does not map between categories)
- Not a category (has no objects or composition law)

What IS an object is the ProtocolAdapter node (F2) that _represents the binding_ as a materialized fact. The protocol spec (RFC 7540, gRPC spec, WebRTC standard) never enters the graph. Only the implementation of it, as a named container with a URN and stratum, does.

**In strict categorical language:** a protocol binding is a mediating map from the external message monoid into the free `Env`-monoid. The model deliberately does not promote it to a named categorical structure — doing so would violate Rule 4.

**Reference:** Normalization Rule 4 (Semantics before transport); F2 above; ontology.json OBJ11  
**See also:** [MacLane — Categories for the Working Mathematician](https://link.springer.com/book/10.1007/978-1-4757-4721-8) Ch. 1 on morphisms as primary; [Goguen — A categorical manifesto](https://doi.org/10.1017/S0960129500001365)

**Wave:** doc/KB — no code change required

---

## F7 — The type system is not self-hosting (deep — future wave)

**What**  
OBJ01–OBJ13, CAT01–CAT22, MOR01–MOR16, and FUN01–FUN05 are defined in `ontology.json` (a file on disk) but do not exist as nodes in the graph. The type system defines what can be in the graph, but is not itself in the graph.

**Why this matters categorically**  
AX1 states: "Every entity is a container identified by URN. No metadata layer — only containers referencing containers via wires." If Kinds and Categories are entities with identity (they have IDs, descriptions, constraints), they are containers by AX1's own definition. Putting them outside the graph creates a metadata layer — a violation of the axiom they are supposed to uphold.

**The Gödelian boundary**  
The evaluation rule itself (`EvaluateWithRegistry`) cannot be a node — this is the precise analogue of Gödel's incompleteness: the proof rules of a system cannot be fully represented within the system they govern, for any system of sufficient power. But the _type declarations_ the evaluator reads (which Kinds exist, which ports they have) are data—not rules—and data can be graph nodes.

**What self-hosting would give:**

- `GET /graph/nodes?kind=Kind` → lists all registered Kinds
- Adding a new Kind is an `ADD` morphism — goes through the log, has an actor, is replayable
- Kind promotion from S0 (proposed) to S2 (operational) follows the stratum chain
- The ontology is no longer a file the kernel reads — it is part of the graph the kernel governs

**The practical boundary:**  
The evaluation rule still lives outside — in Go. Self-hosting the type declarations does not change this. The kernel code that reads Kind nodes and applies constraints is still external to the nodes it reads. This is not a flaw; it is the unavoidable fixed point.

**Reference:** F-algebra self-reference; [Hofstadter — Gödel, Escher, Bach](https://en.wikipedia.org/wiki/G%C3%B6del,_Escher,_Bach) Ch. on Strange Loops; [Lawvere — Diagonal arguments and cartesian closed categories](https://tac.mta.ca/tac/reprints/articles/15/tr15.pdf) for the formal version of the self-reference bound  
**See also:** [nLab: initial algebra](https://ncatlab.org/nlab/show/initial+algebra+of+an+endofunctor); Internal language of a topos as a model for self-describing type systems

**Wave:** 4+ — discuss during stratum-chain formalization

---

## F8 — Governance (AX5) is entirely absent in Wave 0

**What**  
The kernel currently accepts any actor URN issuing any morphism against any target. `urn:moos:kernel:self` and `urn:moos:user:alice` are categorically equal as requestors — no wire constraint separates what each is allowed to do.

**Why**  
AX5: "Governance is structural — access control is a graph morphism, not a middleware flag." The governance mechanism is defined axiomatically but has zero implementation. Any external caller can issue a `MUTATE` on any node, including kernel-owned nodes.

**The correct model when implemented:**  
An actor's permitted operations are determined by the graph: does a OWNS-chain wire exist between `actor_urn` and `target_urn`? If yes, the morphism is permitted for that actor on that target. This is a graph traversal, not a role table.

**Immediate mitigation needed:**  
The HTTP API should at minimum refuse morphisms targeting `urn:moos:kernel:*` nodes from actors other than `urn:moos:kernel:self`. This is structural (check graph: does the actor OWNS the target?) not role-based.

**Reference:** AX5; ontology.json SUB01 (identity subcategory); OWNS morphism (MOR01)  
**See also:** [Abadi et al. — Access control meets process calculi](https://doi.org/10.1145/3022719) for the morphism-as-permission model

**Wave:** 1 for kernel-node protection; 2 for full actor governance

---

## F9 — "Purpose" / tool description as lossy functor (strategic)

**What**  
Every major AI platform (OpenAI, Anthropic, Google) represents tools, skills, and agents as flat JSON blobs with a `description` string. The description is natural language that the LLM must parse at inference time to determine: ownership, scope, routing, composition constraints, stratum, history.

**What the graph gives for free that description does not:**

| Semantic fact          | In description (string)     | In graph (structural)                         |
| ---------------------- | --------------------------- | --------------------------------------------- |
| Who owns this tool     | "maintained by search team" | OWNS wire from identity node                  |
| What it connects to    | "can be used with models"   | CAN_ROUTE wire to AgnosticModel nodes         |
| Is it tested/validated | "production ready"          | Stratum = S2                                  |
| What called it last    | absent                      | morphism log (actor, timestamp)               |
| Can it chain with X    | absent                      | shared port traversal                         |
| What it costs          | absent                      | benchmarked_by wire to InfraService cost node |

The functor from the hypergraph to the tool-list format drops all of these. What re-enters through the description string is informal, unverifiable, and requires LLM inference to reconstruct — introducing exactly the ambiguity the graph would have resolved for free.

**This is not an academic concern.** When an agent selects a tool incorrectly because two tools have similar descriptions, the root cause is the dropped morphisms — ownership, routing constraints, stratum — that would have made the selection deterministic.

**The mo:os model's answer:**  
A tool's identity is its graph position. The XYflow projection (UI_Lens functor) of the relevant subgraph IS the purpose — made visible, not described in prose. The MCP tool list is a lossy S4 projection. The graph (S2/S3) is the truth.

**Reference:** AX2 ("Meaning is not projection"); Normalization Rule 5 ("Projection is not ontology"); ontology.json FUN01–FUN05 (functor definitions); CAT12 (Projected category)  
**See also:** [Goguen — Sheaf semantics for concurrent interacting objects](https://doi.org/10.1017/S0960129500001791) for structure-preserving vs lossy maps; [Spivak — Category Theory for the Sciences](https://math.mit.edu/~dspivak/CT4S.pdf) Ch. 4 on databases as categories (the tool list IS a database schema with missing foreign keys)

**Wave:** strategic framing — informs Wave 3+ provider/agent dispatch design

---

## F10 — MCP config had stale npx path and dead `collider-tools` entry

**What (already fixed — recorded for traceability)**  
`.vscode/mcp.json` had:

1. `npx.cmd` path pointing to a WinGet-versioned Node.js directory that no longer exists → caused `spawn EINVAL` on all three stdio MCP servers
2. `collider-tools` SSE server entry pointing to `http://localhost:8080/mcp/sse` — this was the FFS1 Collider Data Systems gRPC backend's MCP server; that implementation is removed from the repo
3. `.agent/knowledge` in `filesystem-workspace` args — that directory was deleted in the Wave 0 flatten commit

**Fix applied:**

- All `command` paths updated to `C:/Program Files/nodejs/npx.cmd`
- `.agent/knowledge` removed from args
- `collider-tools` entry retained (SSE type — only connects when server is running, no spawn error when absent)

**Recommendation for future:**  
When a new kernel MCP server is implemented, it will be a new `mcp.json` entry with a new name reflecting the kernel's URN namespace (e.g. `moos-kernel`) — not a resurrection of `collider-tools`. The `ProtocolAdapter` node for it should be seeded in the graph before the server is started.

**Wave:** done

---

## Summary table

| ID  | Severity  | Wave | Status  | One-line                                                               |
| --- | --------- | ---- | ------- | ---------------------------------------------------------------------- |
| F1  | Critical  | 0    | Open    | `Kind=Kernel` and `Kind=Feature` not in ontology OBJ list              |
| F2  | Critical  | 0    | Open    | `http-api` Feature → `ProtocolAdapter` (OBJ11); wrong kind, wrong port |
| F3  | Moderate  | 1    | Open    | Morphism log store (InfraService) has no graph node                    |
| F4  | Critical  | 0    | Open    | `urn:moos:kernel:self` actor has no ADD — categorically malformed      |
| F5  | Minor     | 0    | Open    | "kernel is a catamorphism" → "kernel implements a catamorphism" (docs) |
| F6  | Minor     | Doc  | Open    | Protocol not a category — canonical formulation pinned for consistency |
| F7  | Deep      | 4+   | Tracked | Type system not self-hosting — ontology.json is a metadata layer       |
| F8  | High      | 1    | Open    | AX5 governance has zero implementation — any actor does anything       |
| F9  | Strategic | 3+   | Tracked | Tool description = lossy functor; graph position = purpose             |
| F10 | Done      | 0    | Fixed   | MCP config stale paths and dead collider-tools entry                   |

---

## References

- [nLab: catamorphism](https://ncatlab.org/nlab/show/catamorphism)
- [nLab: initial algebra of an endofunctor](https://ncatlab.org/nlab/show/initial+algebra+of+an+endofunctor)
- [nLab: Lawvere theory](https://ncatlab.org/nlab/show/Lawvere+theory)
- [nLab: functorial semantics](https://ncatlab.org/nlab/show/functorial+semantics)
- Meijer, Fokkinga, Paterson — [Functional Programming with Bananas, Lenses, Envelopes and Barbed Wire (1991)](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.41.125)
- MacLane — [Categories for the Working Mathematician](https://link.springer.com/book/10.1007/978-1-4757-4721-8)
- Goguen — [A categorical manifesto (1989)](https://doi.org/10.1017/S0960129500001365)
- Goguen — [Sheaf semantics for concurrent interacting objects](https://doi.org/10.1017/S0960129500001791)
- Spivak — [Category Theory for the Sciences](https://math.mit.edu/~dspivak/CT4S.pdf)
- Lawvere — [Diagonal arguments and cartesian closed categories](https://tac.mta.ca/tac/reprints/articles/15/tr15.pdf)
- Hofstadter — [Gödel, Escher, Bach](https://en.wikipedia.org/wiki/G%C3%B6del,_Escher,_Bach) (Ch. on Strange Loops and self-reference)
- Abadi et al. — [Access control meets process calculi](https://doi.org/10.1145/3022719)
- Wolfram — [A New Kind of Science](https://www.wolframscience.com/nks/) Ch. 9 (causal invariance in hypergraph rewriting)
- `platform/kernel/cmd/kernel/main.go` — seedKernel(), actor constant
- `platform/kernel/internal/core/evaluate.go` — EvaluateWithRegistry (the algebra map)
- `platform/kernel/internal/shell/runtime.go` — Apply, SeedIfAbsent (the fold executor)
- `platform/kernel/internal/shell/registry_loader.go` — LoadRegistry (where Kind constraints are read)
- `.agent/knowledge_base/superset/ontology.json` — OBJ01–OBJ13, CAT01–CAT22, SUB01–SUB08
- `.agent/knowledge_base/01_foundations/01_axioms.md` — AX1–AX5
- `.agent/knowledge_base/CLAUDE.md` (root) — Normalization Rules 1–7
