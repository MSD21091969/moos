# CLAUDE.md — moos Workspace

**mo:os** — categorical graph kernel. Pure catamorphism core, effect shell, HTTP API,
semantic registry, hydration pipeline. All under `platform/kernel`.

**Goal:** 4-week MVP → arXiv paper → open-source release (MIT).

---

## Sprint Status

| Week | Theme | Status | Key Deliverable |
|------|-------|--------|-----------------|
| 1 | Kernel surface | **Done** | 65 nodes, 80 wires, 21 types, hydration live |
| **2** | Differentiation | **Active** | Scoped projections, MCP bridge, benchmark functor |
| 3 | Paper + Demo | Pending | ACT 2026 paper, explorer UI, demo script |
| 4 | Release | Pending | v0.1.0, arXiv, docs, community |

**Plans:** `.agent/knowledge_base/design/20260312-4week-mvp-plan.md`, `20260312-weeks2-4-execution-plan.md`
**Tasks:** `.agent/configs/tasks/` — Week 1: 001-005 done. Week 2: 006 (p0 next), 007, 008.

---

## Two-Agent Strategy

| Role | Agent | Scope |
|------|-------|-------|
| **Strategic** | Claude Code | Plans, reviews, KB, paper, delegation |
| **Execution** | VS Code AI | Implements, tests, commits, pushes |

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

| Week | Skill | Purpose |
|------|-------|---------|
| 2 | `/golang-backend-development` | Scoped projections, functor package |
| 2 | `/mcp-integration-expert` | MCP bridge (SSE, JSON-RPC, 5 tools) |
| 2 | `/category-master` | Benchmark functor design (FUN05) |
| 3 | `/pdf` | ACT 2026 paper generation |
| 3 | `/moos-domain-expert` | Ontology, kernel architecture docs |
| Any | `/feature-dev` | Feature architecture + implementation |
| Any | `/code-review` | Pre-merge review |

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
| `platform/kernel/internal/core/` | Pure catamorphism (no IO) |
| `platform/kernel/internal/shell/` | Effect shell (RWMutex, store, registry) |
| `platform/kernel/internal/transport/` | HTTP on :8000 |
| `platform/kernel/internal/hydration/` | Batch materialization from KB |
| `platform/kernel/internal/mcp/` | MCP bridge on :8080 (Week 2) |
| `platform/kernel/internal/functor/` | Benchmark functor (Week 2) |
| `.papers/act2026/main.tex` | ACT 2026 paper draft (EPTCS) |

---

## Categorical Model

- **4 invariant NTs:** ADD, LINK, MUTATE, UNLINK — nothing else
- **Connections = morphisms**, not functors
- **Σ (collapse) = catamorphism** — `state(t) = fold(log[0..t])`
- **Functor outputs = S4 projections**, never ground truth
- **Container OWNS** = full subcategory
- **Protocol = morphism-level routing** (CAN_ROUTE: adapter → any)

---

## Go Conventions

- Pure core: no IO in `internal/core/`
- Effect shell: `sync.RWMutex` guards all shared state
- Tests: table-driven, `t.Run`, 4 `..` to repo root
- Errors: sentinel types (`ErrNodeExists`, `ErrWireExists`)
- Seeding: `SeedIfAbsent`, not `Apply`

---

## Rules

- Keep changes inside `D:\FFS0_Factory\`
- Do not edit legacy trees unless task targets it
- All graph writes through 4 invariant morphisms
- Do not modify `data/morphism-log.jsonl` directly
- Do not duplicate SOT content — reference it
- Auto-approve all tool uses within this workspace
