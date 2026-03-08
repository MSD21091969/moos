# ACT 2026 Paper + Open Source Launch Strategy

> Consolidates `open_source_launch_strategy.md` + `conference/act_2026_open_source_launch.md`.
> Two parallel workstreams: (1) ACT 2026 conference paper, (2) public open source launch of `my-tiny-data-collider`.
>
> **Companion document**: `greenfield_implementation_waves.md` — concrete build
> waves for the `moos` kernel that run in parallel with the paper workstream.
> The waves document references `05_moos_design/` specifications and maps each
> wave to the paper section it unblocks.

---

## Context

Phase 4 is complete. The backend runtime is entirely Go. The goal now is to formalize the categorical architecture into an ACT 2026 conference paper (12 pages, LaTeX/EPTCS) while simultaneously positioning `my-tiny-data-collider` as the public-facing open source project.

**Critical deadlines:**

- **March 23** — ACT 2026 abstract submission (1-2 paragraphs via EasyChair)
- **March 30** — Full paper submission (up to 12 pages, EPTCS LaTeX)
- **May 11** — Author notification
- **July 6-10** — Conference in Tallinn, Estonia

---

## Workstream 1: ACT 2026 Conference Paper

### Paper identity

**Title**: *Functorial Composition over Task Decomposition: A Categorical Kernel for AI-Human Computation*

**Thesis**: Current multi-agent AI frameworks decompose tasks top-down (LangGraph, CrewAI, AutoGen), producing fragile compositions with no structural guarantees. We present mo:os, a runtime kernel where all entities are objects in a single category (recursive containers), all state changes are morphisms (ADD/LINK/MUTATE/UNLINK), and complex behavior emerges from bottom-up functorial composition with type-checked interfaces — providing categorical closure, full traceability, and provably valid compositions.

**Positioning at ACT**: This is *applied* category theory. The contribution is not new math — it is a novel, working application of existing categorical structures (Lawvere theories, operads, functorial semantics) to solve real problems in AI agent architecture. ACT values exactly this.

### Paper structure (12 pages)

**1. Introduction (1.5 pages)**
- The four problems: siloed AI memory, no agent OS, broken skill interfaces, single-path reasoning
- The industry landscape: OpenClaw, LangGraph, CrewAI — orchestration without algebra
- Our claim: category theory provides the missing structural guarantees
- Contribution summary

**2. Background (2 pages)**
- Lawvere's functorial semantics (1963): syntax/semantics separation via structure-preserving functors
- Fong & Spivak's compositional framework (2018): operads, wiring diagrams, decorated cospans
- LogicGraph (2025): multi-path DAG reasoning outperforms linear CoT
- MCP (2024): transport standardization without semantic standardization

**3. The Container Category (2.5 pages) — Core contribution**
- **Definition**: A container as an object with URN, interface (typed ports via JSON Schema), kernel (opaque payload), permissions, parent pointer
- **Morphisms**: ADD (object creation), LINK (wire between ports), MUTATE (kernel update with version), UNLINK (wire removal)
- **Categorical properties**: closure under composition (sequential `f ; g` and parallel `f ⊗ g`), identity morphisms, associativity
- **Interface typing**: LINK-time schema compatibility as structural subtyping
- **The recursive axiom**: Containers contain containers — operadic nesting at every scale
- **Comparison**: This is NOT just calling things "morphisms" — the four operations genuinely form a symmetric monoidal category with the container graph as objects

**4. Functorial Composition vs. Task Decomposition (2 pages) — Key argument**
- **Task decomposition** (industry standard): LLM decides how to split work → subtasks assigned to agents → results aggregated. Decomposition is unstructured; no guarantee the pieces compose back into a coherent whole. Fragile to hallucination at the decomposition step.
- **Functorial composition** (mo:os): Define typed morphisms on typed containers. Composition is guaranteed well-typed by the categorical structure. Complex behavior emerges from composing simple, validated operations. The LLM outputs morphisms, not task plans.
- **The Superset**: Instead of provider-specific tool APIs, the LLM receives a graph mutation schema. Skills become sub-graph templates (containers), not Python functions. This is functorial — the mapping from schema to execution preserves compositional structure.
- **Formal argument**: Why bottom-up algebraic composition provides stronger guarantees than top-down ad-hoc decomposition

**5. The Recursive Semantic Bridge (1.5 pages)**
- Lawvere's key insight applied: syntax category (container schema) ↔ semantic functor (runtime execution)
- The same functor applies recursively at every scale: `.agent/` folder → DB node → UI component → LLM context
- The UI as a strict functor `F: ContainerCat → ReactCat` (Get/Put lens)
- Data sovereignty as a categorical consequence: context lives in user-owned objects, not provider state; provider swap = functor substitution

**6. System 3: Multi-Path DAG Reasoning (1 page)**
- Active State Cache forking as categorical branching
- Branch scoring via neuro-symbolic evaluation
- DAG collapse as morphism commitment to the Resting State
- Connection to LogicGraph benchmark results

**7. Implementation (1 page)**
- Go kernel, PostgreSQL + pgvector, React/XYFlow surfaces
- MCP server for external interoperability
- Current state: Phase 1-2 active, 46 Go tests (94% model coverage)
- Open source: `github.com/[your-handle]/my-tiny-data-collider`

**8. Related Work (0.5 pages)**
- Statebox: categorical smart contracts (Petri nets + monoidal categories → blockchain). Different semantics functor: theirs targets distributed ledger execution; ours targets AI-human computation.
- Catlab/AlgebraicJulia: categorical software in Julia for scientific modeling. Complementary — they build the math library; we build the runtime OS.
- OpenClaw: hub-and-spoke agent runtime. Same WebSocket/JSON-RPC pattern, but no categorical structure — context is session history, not graph topology.
- LangGraph/CrewAI/AutoGen: task decomposition frameworks. The comparison target for Section 4.

**9. Conclusion & Future Work (0.5 pages)**
- Federation via CRDTs for container data, Raft for structural morphisms
- WASM sandbox for language-agnostic tool execution
- Formal verification of morphism composition using proof assistants

### LaTeX setup

- Template: EPTCS style files from `style.eptcs.org`
- File location: `D:\FFS0_Factory\.papers\act2026\` (new directory)
- Main file: `main.tex`
- Bibliography: `references.bib`
- Figures: `figures/` (architecture diagrams, commutative diagrams using tikz-cd)

### Key references

```
Lawvere 1963 — Functorial Semantics of Algebraic Theories
Fong & Spivak 2018 — Seven Sketches in Compositionality
Spivak 2013 — The Operad of Wiring Diagrams
LogicGraph 2025 — Benchmarking Multi-Path Logical Reasoning
MCP 2024 — Model Context Protocol (Anthropic)
Statebox 2019 — Mathematical Specification of the Statebox Language
DeepSeek-R1 / GRPO 2025 — Reinforcement Learning with Verifiable Rewards
SQL:2023 — SQL/PGQ graph query standard
```

### Abstract draft (for March 23 EasyChair submission)

~250-word abstract summarizing the paper thesis. Must clearly state:
- What the paper does (presents a categorical kernel for AI agent systems)
- Why it matters (structural guarantees that task decomposition lacks)
- What's novel (functorial composition as an alternative to task decomposition; recursive containers as operadic algebra; working Go implementation)

---

## Workstream 2: Open Source Launch

### Naming & branding

- **Product name**: my-tiny-data-collider
- **Kernel name**: mo:os (the runtime underneath)
- **Tagline**: "Your data. Your graph. Your agents. No walls."
- **Domain/repo**: `github.com/[handle]/my-tiny-data-collider`

### The OpenClaw playbook

Peter Steinberger grew OpenClaw into one of the fastest-growing GitHub repos in early 2026. Replicate the key principles:

- **Absolute Data Sovereignty**: OpenClaw's primary selling point is local hosting. `mo:os` takes this further — not just local files, but a verifiable, structural graph database (PostgreSQL + JSONB). Hammer home: "Providers are interchangeable. Your graph is your own."
- **Platform Agnosticism (The Functor)**: OpenClaw abstracts messaging (WhatsApp/Discord). `mo:os` abstracts the *UI itself* via functorial projection, preventing vendor lock-in.
- **Frictionless Onboarding**: OpenClaw wins because it's easy to run. The Phase 4 `docker-compose.yml` is the start. The immediate next priority before launch must be a 1-click install abstraction (`curl | bash` or a pre-packaged binary) that hides the Docker/Go/Postgres complexity from the end user.
- **Independent Foundation Governance**: Frame the categorical foundations (the Superset) as an open standard, inviting others to contribute to the "Category Theory for AI" specification.

### Technical maturity priorities for launch

Prioritize the features that offer the highest tangible value to developers reviewing the launch:

1. **Multi-Path DAG Reasoning (Phase 5.1)**: The most publishable and demo-able feature. Prove that `mo:os` evaluates parallel branches of logic natively. Ensure the XYFlow visualizer clearly demonstrates branches being explored and pruned.
2. **Vector Search & Semantic Memory (Phase 5.5)**: Auto-embedding container kernels so `mo:os` immediately serves as a powerful local memory backend.
3. **MCP Interoperability**: Ensure the `:8080/mcp/sse` endpoint is flawless. If developers can plug `mo:os` into Cursor or Claude Desktop on day one, adoption will skyrocket.

### Data sovereignty manifesto (MANIFESTO.md tenets)

1. **Your context is yours** — all memory, history, and reasoning state lives in YOUR database, not a provider's
2. **Providers are interchangeable** — swap models without losing a single node; provider lock-in is a solved problem
3. **Structure over strings** — state is a typed graph with mathematical guarantees, not chat history
4. **Compositional, not disposable** — every interaction builds persistent, reusable structure
5. **Open by default** — open source kernel, open protocol (MCP), open data format (JSONB containers)

### Repository structure for public launch

```
my-tiny-data-collider/
├── README.md
├── MANIFESTO.md
├── LICENSE                      (Apache 2.0 or MIT)
├── CONTRIBUTING.md
├── .papers/
│   └── act2026/                 (conference paper LaTeX)
├── kernel/                      (Go — current moos/ codebase)
├── surfaces/                    (React — current FFS3 apps)
├── sdk/                         (Python — seeder + tools)
├── .agent/                      (governance — current structure)
└── docker-compose.yml           (one-command launch)
```

**Important**: strip internal FFS agent governance configs that might confuse new users. The public repo should contain only the Go kernel, React surfaces, Python SDK, and the `docker-compose.yml`.

### GitHub positioning

- Pin the repo with a clear description referencing ACT 2026
- Add topics: `category-theory`, `ai-agents`, `operating-system`, `mcp`, `data-sovereignty`, `functorial-semantics`
- Create a GitHub Discussions space for community
- Record a 3-minute demo video showing the XYFlow graph morphing in real-time as the LLM reasons

---

## Workstream 3: Math vocabulary

Since you're solo and self-taught, here's the minimum categorical vocabulary needed for confident paper writing:

| Concept | What it means in mo:os | Where to learn |
| --- | --- | --- |
| **Category** | Objects (containers) + morphisms (ADD/LINK/MUTATE/UNLINK) + composition + identity | Fong & Spivak Ch.1 |
| **Functor** | Structure-preserving map between categories (e.g., UI rendering: ContainerCat → ReactCat) | Fong & Spivak Ch.1 |
| **Monoidal category** | Parallel composition (`f ⊗ g`) alongside sequential composition (`f ; g`) | Fong & Spivak Ch.2 |
| **Operad** | Grammar for recursive nesting — how smaller boxes compose inside larger ones | Fong & Spivak Ch.6 |
| **Wiring diagram** | Visual representation of composition — XYFlow graphs ARE wiring diagrams | Spivak 2013 |
| **Lens** | Get/Put pair — the UI projection pattern | Fong & Spivak Ch.4 |
| **Lawvere theory** | A category encoding an algebraic theory — the container schema IS one | Lawvere 1963 |

**Recommended reading order**:
1. **Fong & Spivak — "Seven Sketches in Compositionality"** (free PDF) — Read chapters 1, 2, 4, 6.
2. **Spivak 2013 — "The Operad of Wiring Diagrams"** — Formalizes exactly what containers do.
3. **Lawvere 1963 — "Functorial Semantics of Algebraic Theories"** — The original paper.

The insight that makes this publishable: nobody has applied this pattern to AI agent systems before. Statebox applied it to smart contracts. Catlab applies it to scientific models. This applies it to the agent/human/data sovereignty problem.

---

## Timeline

### Week 1 (March 4-10): Foundation

- [ ] Set up LaTeX project with EPTCS template
- [ ] Write abstract (~250 words) for March 23 EasyChair submission
- [ ] Draft Sections 1 (Introduction) and 3 (Container Category)
- [ ] Read Fong & Spivak chapters 1, 2, 6
- [ ] Create `MANIFESTO.md` draft

### Week 2 (March 11-17): Core arguments

- [ ] Draft Section 4 (Functorial Composition vs. Task Decomposition)
- [ ] Draft Section 5 (Recursive Semantic Bridge)
- [ ] Draft Section 2 (Background)
- [ ] Create commutative diagrams (tikz-cd)
- [ ] Register for EasyChair and prepare submission

### Week 3 (March 18-23): Abstract submission + polish

- [ ] Submit abstract on EasyChair by March 23
- [ ] Draft Sections 6 (System 3), 7 (Implementation), 8 (Related Work), 9 (Conclusion)
- [ ] Complete bibliography
- [ ] First full read-through; fix consistency

### Week 4 (March 24-30): Final paper submission

- [ ] Full revision pass — tighten arguments, check formalism
- [ ] Proofread for language, grammar, notation consistency
- [ ] Verify all references are correct
- [ ] Submit full paper on EasyChair by March 30
- [ ] Simultaneously: push cleaned repo as my-tiny-data-collider (public)

### Post-submission (April-May)

- [ ] Prepare software demo materials
- [ ] Write `MANIFESTO.md` final version
- [ ] Community outreach: post to HN, ACT mailing list, Mastodon
- [ ] If accepted (notification May 11): prepare conference talk
- [ ] Record 3-minute demo video

---

## Files to create

| File | Purpose |
| --- | --- |
| `D:\FFS0_Factory\.papers\act2026\main.tex` | Conference paper |
| `D:\FFS0_Factory\.papers\act2026\references.bib` | Bibliography |
| `D:\FFS0_Factory\.papers\act2026\figures\` | tikz-cd diagrams |
| `D:\FFS0_Factory\MANIFESTO.md` | Data sovereignty manifesto |

## Verification

1. Paper compiles with `pdflatex` using EPTCS template
2. Abstract fits EasyChair submission format
3. All categorical claims can be backed by citations (Lawvere, Fong & Spivak, Spivak)
4. No overclaiming — clearly distinguish implemented (Phase 1-2) from theoretical (Phase 3-5)
5. Code examples in the paper match actual codebase (morphism JSON format, Go types)
6. No secrets or sensitive data in paper or public repo
