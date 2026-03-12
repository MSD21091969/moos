# CLAUDE.md — moos Workspace

Workspace authority for mo:os at `D:\FFS0_Factory\moos`.

**Wave 0 — Go kernel is live.** Pure catamorphism core, effect shell, HTTP API,
semantic registry, hydration pipeline, self-seeding — all under `platform/kernel`.

**Strategy:** 4-week MVP → arXiv paper → open-source release (MIT).
Plan: `.agent/knowledge_base/design/20260312-4week-mvp-plan.md`

---

## Current Sprint

| Week | Theme | Status |
|------|-------|--------|
| **1** | Complete kernel surface | **In progress** |
| 2 | MCP bridge, scoped projections, benchmark functor | Pending |
| 3 | Paper draft, demo, explorer UI | Pending |
| 4 | v0.1.0 release, arXiv, community | Pending |

**Week 1 tasks:** 001 done, **002 pending p0**, 003 done, 004 pending p1, 005 pending p1.
Task 002 is critical path. Details in `.agent/configs/tasks/`.

---

## Context Read Order

1. This file
2. `.agent/knowledge_base/delegation-protocol.md`
3. `.agent/knowledge_base/handoff.md`
4. `.agent/configs/tasks/` (pending tasks)

---

## Active Scope

Edit targets: `platform/`, `.agent/knowledge_base/`, `.agent/configs/`, `.vscode/`, `secrets/`.
Everything else is legacy — do not edit unless task explicitly targets it.

**Key paths:**

| Path | What |
|------|------|
| `platform/kernel/cmd/kernel/main.go` | Entrypoint |
| `platform/kernel/internal/core/` | Pure catamorphism (no IO) |
| `platform/kernel/internal/shell/` | Effect shell (RWMutex, store, registry) |
| `platform/kernel/internal/httpapi/` | HTTP transport |
| `platform/kernel/internal/hydration/` | Batch materialization |
| `.agent/knowledge_base/superset/ontology.json` | Canonical ontology (21 kinds, 16 morphisms, 22 categories) |
| `.agent/knowledge_base/doctrine/` | Prose specs (strata, hydration, install) |
| `.agent/knowledge_base/instances/` | Runtime facts (schema-validated JSON) |
| `.agent/knowledge_base/industry/` | Curated landscape (providers, tools, compute) |

---

## Categorical Model (v3.0)

- **Connections = morphisms**, not functors
- **Fan-out = coslice**, Fan-in = slice category
- **Container OWNS** = full subcategory
- **Σ (collapse) = catamorphism** — the kernel _is_ a catamorphism
- **Protocol = morphism-level routing** — not a functor, not a category
- **Functor outputs are never ground truth** — projections (S4)
- **Four invariant NTs:** ADD, LINK, MUTATE, UNLINK — nothing else

---

## Implementation Facts

| Fact | Detail |
|------|--------|
| Go module | `moos/platform/kernel` (Go 1.22+) |
| Self-seeding | `seedKernel()` — 13 morphisms first boot, 0 on replay |
| Kernel actor | `urn:moos:kernel:self` |
| Kernel node | `urn:moos:kernel:wave-0` Kind=Kernel S2 |
| SeedIfAbsent | Absorbs ErrNodeExists/ErrWireExists |
| Default store | `platform/kernel/data/morphism-log.jsonl` (JSONL) |
| Postgres | `MOOS_KERNEL_STORE=postgres` + `MOOS_DATABASE_URL` |
| HTTP port | `8000` (kernel), `8080` (MCP/SSE future) |
| Test path depth | 4 `..` segments from test package to repo root |
| Tests | All green: `core`, `httpapi`, `shell` |

---

## Two-Agent Strategy + Task Delegation

**Claude Code** = strategic (plans, reviews, KB, paper).
**VS Code AI** = execution (implements, tests, commits).

**Comm surfaces:**
- `.agent/knowledge_base/delegation-protocol.md` — workflow spec
- `.agent/knowledge_base/handoff.md` — bidirectional messages (newest on top)
- `.agent/configs/tasks/YYYYMMDD-NNN-*.md` — task queue

**Message format:** `### [YYYY-MM-DD HH:MM] Source → type: subject`
**Types:** `complete` | `blocked` | `question` | `answer` | `direction`

**On session start:** Check tasks/, pick highest-priority with deps met.
**Execution:** Read task → verify against SOTs → implement → mark done → commit → push.
**Commits:** `feat|fix|chore: <description> [task:YYYYMMDD-NNN]`

---

## Relevant Skills

| Skill | When |
|-------|------|
| `/moos-domain-expert` | Ontology, categorical model, kernel architecture |
| `/category-master` | Category theory, functor/operad design |
| `/golang-backend-development` | Go kernel, HTTP handlers |
| `/mcp-integration-expert` | MCP bridge (Week 2) |
| `/feature-dev` | Feature architecture + implementation |
| `/code-review` | Pre-merge review |
| `/pdf` | Paper generation (Week 3) |

---

## SOT Hierarchy

1. **`superset/ontology.json`** — always wins
2. **`doctrine/*.md`** — prose specs, non-duplicating
3. **`design/*.md`** — timestamped decisions (latest wins)
4. **`instances/*.json`** — must conform to ontology
5. **`industry/*.json`** — independent of ontology
6. **This file** — workspace policy, does not override ontology
7. **Task files** — reference SOTs, never restate them

---

## Go Conventions

- **Pure core:** no IO in `internal/core/`
- **Effect shell:** all shared state guarded by `sync.RWMutex`
- **Tests:** table-driven, `t.Run`, 4 `..` to repo root
- **Errors:** sentinel types (`ErrNodeExists`, `ErrWireExists`)
- **Seeding:** `SeedIfAbsent`, not `Apply`
- **Commits:** Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`)

---

## Rules

- Keep changes inside `D:\FFS0_Factory\`
- Do not edit legacy trees unless task targets it
- All graph writes through 4 invariant morphisms — never bypass kernel API
- Do not modify `data/morphism-log.jsonl` directly
- Do not duplicate SOT content — reference it
- Auto-approve all tool uses within this workspace
