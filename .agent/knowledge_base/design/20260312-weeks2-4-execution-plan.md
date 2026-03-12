# Execution Plan: Weeks 2–4 MVP

TL;DR: 9 tasks across 3 weeks. Week 2 adds scoped projections, MCP bridge, and benchmark functor. Week 3 ports explorer UI, evolves ACT 2026 paper, polishes demo. Week 4 ships v0.1.0 with CI, docs, and community seeding. All pure Go, zero external deps.

**Baseline (end of Week 1):** nodes=65, wires=80, log_depth=145, 21 type_ids, 6 test packages green.

---

## Phase A — Week 2: Differentiation

### Task 006: Scoped Projections (p0, blocks 007)

Add actor-scoped subgraph extraction via BFS on OWNS wires.

- Add `ScopedSubgraph(actor URN) GraphState` to shell.Runtime (BFS, RLock)
- Add `GET /state/scope/{actor}` route in transport/server.go
- Table-driven tests in shell + transport
- **Files:** shell/runtime.go, transport/server.go, +tests

### Task 007: MCP Bridge (p0, depends 006)

SSE transport on port 8080, 5 tools + 3 resources, operad pre-validation.

- New `internal/mcp/` package (server.go, tools.go, resources.go, validation.go)
- Wire into cmd/kernel/main.go
- SSE via net/http (text/event-stream), JSON-RPC, no external deps
- Structured rejection errors (constraint name, expected vs received)
- **Files:** internal/mcp/\*, cmd/kernel/main.go

### Task 008: Benchmark Functor (p1, parallel with 006-007)

FUN05: classifying functor mapping providers to metric space.

- New `internal/functor/` package (benchmark.go, types.go)
- `GET /functor/benchmark/{suite}` endpoint
- Score distributions, provider rankings, equivalence classes
- **Files:** internal/functor/\*, transport/server.go

---

## Phase B — Week 3: Paper + Demo

### Task 009: Explorer UI (p1)

Port archive explorer.go + explorer.html to current kernel.

- embed.FS static HTML, expand kindColor 13→21
- Generate UI JSON directly from GraphState (no uiLens)
- `GET /explorer` route
- **Files:** transport/static/explorer.html, transport/explorer.go, server.go

### Task 010: ACT 2026 Paper (p0)

**Existing draft:** `.papers/act2026/main.tex` (EPTCS class, 9 sections, 8 refs).
Evolve from conceptual draft to implementation-backed paper with:

- Actual kernel metrics (node/wire counts, morphism throughput)
- TikZ figures in figures/ (currently empty)
- Update Section 7 (Implementation) with Wave 0 specifics
- Add benchmark data from instances/benchmarks.json
- Fill in author details, institution
- **Files:** .papers/act2026/main.tex, references.bib, figures/\*.tex

### Task 011: Demo Script + README (p1, depends 007-009)

8-step walkthrough + README rewrite for open-source audience.

- examples/demo.sh (.ps1), README.md rewrite

---

## Phase C — Week 4: Release

### Task 012: Release Engineering (p0)

GH Actions CI, Makefile, v0.1.0 tag, multi-platform binaries.

### Task 013: Paper Submission (p0, depends 010)

Final figures, abstract polish, submit to ACT 2026 / arXiv (cs.AI+cs.PL).

### Task 014: Documentation + Community (p1, depends 012-013)

5 docs, godoc comments, community seeding.

---

## Dependency Graph

```
006 → 007 → 011
008 (parallel with 006-007)
009 (parallel, after Week 1)
010 (parallel, after 007+008) → 013
012 (parallel with 010-011) → 014
```

**Critical path:** 006 → 007 → 011 → 014

---

## Key Decisions

| Decision        | Choice                | Rationale                           |
| --------------- | --------------------- | ----------------------------------- |
| MCP transport   | SSE (net/http)        | Zero deps, browser-compatible       |
| Paper template  | EPTCS (existing)      | ACT 2026 submission already started |
| Functor package | New internal/functor/ | Clean separation from core          |
| Explorer embed  | embed.FS              | Single binary, no external assets   |
| Release CI      | GitHub Actions        | Standard Go CI pattern              |

---

## Discovery: Existing ACT 2026 Paper

`.papers/act2026/` contains a partial submission:

- **Template:** EPTCS class (eptcs.cls), not acmart
- **Sections:** Introduction, Background, Container Category, Semantic Bottleneck, Recursive Semantic Bridge, System 3 DAG Reasoning, Implementation (stub), Related Work, Conclusion
- **References:** 8 entries (Lawvere, Fong/Spivak, Spivak operads×2, MCP, LogicGraph, Statebox, Bonchi, Gu)
- **Figures:** empty directory (needs TikZ diagrams)
- **Status:** Conceptual — Implementation section is a one-liner, needs Wave 0 specifics
- **Abstract:** Also saved as easychair_abstract.md (EasyChair submission)
- **Helpers:** arxiv_search.py (literature search), read_pdf\*.py (reference extraction)
