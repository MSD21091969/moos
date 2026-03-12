# CLAUDE.md — moos Workspace

**mo:os** — categorical graph kernel. Pure catamorphism core, effect shell, HTTP API,
semantic registry, hydration pipeline, MCP bridge, benchmark functor. `platform/kernel`.

**Goal:** 4-week MVP → ACT 2026 paper → arXiv → open-source release (MIT).

---

## Sprint Status

| Week | Theme | Status | Key Deliverable |
|------|-------|--------|-----------------|
| 1 | Kernel surface | **Done** | 65 nodes, 80 wires, 21 types, hydration live |
| 2 | Differentiation | **Done** | Scoped projections, MCP bridge, benchmark functor |
| 3 | Paper + Demo | **Active** | ACT 2026 paper, explorer UI, demo script, .agent extraction |
| 4 | Release | Pending | v0.1.0, arXiv, CI, docs, community |

**Metrics:** 16 routes, 8 test packages (all green), ~4K LOC, 0 external deps.

**Plans:** `.agent/knowledge_base/design/20260312-4week-mvp-plan.md`, `20260312-weeks2-4-execution-plan.md`
**Tasks:** `.agent/configs/tasks/` — Week 1: 001-005 done. Week 2: 006-008 done. Week 3: 009-011 done.

---

## Three-Agent Strategy

| Role | Agent | Scope |
|------|-------|-------|
| **Strategic** | Claude Code | Plans, reviews, KB, paper, delegation, research |
| **Execution** | VS Code AI (Sonnet 4.6) | Implements, tests, commits, pushes |
| **UX Testing** | Antigraviti (Gemini 3.1 Pro) | Headless browser tests, HTTP/3 research |

**Comm channel** (read on every session start):
1. This file
2. `.agent/knowledge_base/delegation-protocol.md` — workflow rules
3. `.agent/knowledge_base/handoff.md` — bidirectional messages (newest on top)
4. `.agent/configs/tasks/` — pick highest-priority, deps met

**Message format:** `### [YYYY-MM-DD HH:MM] Source → type: subject`
**Types:** `complete` | `blocked` | `question` | `answer` | `direction`
**Commits:** `feat|fix|chore: <description> [task:YYYYMMDD-NNN]`

---

## Skills Map

| Phase | Skill | Purpose |
|-------|-------|---------|
| Week 2 | `/golang-backend-development` | Scoped projections, functor package |
| Week 2 | `/mcp-integration-expert` | MCP bridge (SSE, JSON-RPC, 5 tools) |
| Week 2 | `/category-master` | Benchmark functor design (FUN05), pipeline complexity |
| **Week 3** | **`/pdf`** | **ACT 2026 paper — evolve with pipeline/transport/LLM theory** |
| Week 3 | `/moos-domain-expert` | Ontology, kernel architecture docs |
| Week 4 | `/golang-backend-development` | Release engineering, CI |
| Any | `/feature-dev` | Feature architecture + implementation |
| Any | `/code-review` | Pre-merge review |

**Research resources:**
- `.agent/knowledge_base/reference/` — manifesto, manuscript, paper digests
- `.agent/knowledge_base/http3.pdf` — Gemini HTTP/3 transport research (18pp)
- `.agent/knowledge_base/reference/papers/` — HyperGraphRAG, LogicGraph, Fong/Spivak, Wolfram HDC
- `.papers/act2026/` — paper draft, references, figures, easychair abstract

---

## SOT Hierarchy

1. **`superset/ontology.json`** — always wins (21 kinds, 16 morphisms, 4 NTs)
2. **`doctrine/*.md`** — prose specs
3. **`design/*.md`** — timestamped decisions (latest wins)
4. **`instances/*.json`** — must conform to ontology
5. **`industry/*.json`** — independent landscape data
6. **This file** — workspace policy
7. **Task files** — reference SOTs, never restate them

---

## Key Paths

| Path | What |
|------|------|
| `platform/kernel/cmd/moos/main.go` | Entrypoint (`--kb`, `--hydrate`) |
| `platform/kernel/internal/cat/` | Pure types: Node, Wire, GraphState, Envelope |
| `platform/kernel/internal/fold/` | Pure catamorphism: Evaluate, Replay (no IO) |
| `platform/kernel/internal/operad/` | Semantic registry: 21 TypeSpecs, port validation |
| `platform/kernel/internal/shell/` | Effect shell (RWMutex, Apply, ScopedSubgraph) |
| `platform/kernel/internal/transport/` | HTTP on :8000 (16 routes) |
| `platform/kernel/internal/hydration/` | Batch materialization from KB |
| `platform/kernel/internal/mcp/` | MCP bridge on :8080 (5 tools, SSE, JSON-RPC) |
| `platform/kernel/internal/functor/` | Benchmark functor (FUN05: Provider → Met) |
| `platform/kernel/transport/static/` | Explorer UI (embedded, `go:embed`) |
| `D:\FFS0_Factory\.agent\.papers\act2026\main.tex` | ACT 2026 paper draft (EPTCS, 12pp limit) — external, not in repo |
| `D:\FFS0_Factory\.agent\knowledge_base\` | KB root — external, not in repo; ontology, doctrine, instances, design, refs |
| `platform/kernel/examples/kb-starter/` | Minimal KB scaffold for new cloners |

---

## Categorical Model

- **4 invariant NTs:** ADD, LINK, MUTATE, UNLINK — nothing else
- **Connections = morphisms**, not functors
- **Σ (collapse) = catamorphism** — `state(t) = fold(log[0..t])`
- **Functor outputs = S4 projections**, never ground truth
- **Container OWNS** = full subcategory (BFS scoping)
- **Protocol = morphism-level routing** (CAN_ROUTE: adapter → any)
- **LLM = FPU inside the graph** — agnostic_model object, CAN_ROUTE interface, FUN05 benchmarks
- **MCP = natural transformation** η: Kernel ⇒ LLM tool-use category
- **Causal invariance** — independent morphisms on disjoint subgraphs commute

**Pipeline complexity:**
- Knowledge discovery cost ∝ |E| (edges in subgraph)
- Knowledge retrieval cost ∝ |N| (nodes in subgraph)
- Subgraph complexity = edge values / node count ratio
- HTTP/3: independent QUIC streams map to independent morphisms (causal invariance)
- Stratum transport: S0-S3 reliable streams, S4 unreliable datagrams

---

## Go Conventions

- Pure core: no IO in `internal/cat/`, `internal/fold/`
- Effect shell: `sync.RWMutex` guards all shared state
- Tests: table-driven, `t.Run`, 4 `..` to repo root
- Errors: sentinel types (`ErrNodeExists`, `ErrWireExists`)
- Seeding: `SeedIfAbsent`, not `Apply`
- Zero external dependencies (stdlib only)

---

## Rules

- Keep changes inside `D:\FFS0_Factory\`
- Do not edit legacy trees unless task targets it
- All graph writes through 4 invariant morphisms
- Do not modify `data/morphism-log.jsonl` directly
- Do not duplicate SOT content — reference it
- Auto-approve all tool uses within this workspace
