# mo:os — 4-Week MVP Plan

**Author:** Sam Maassen + Claude
**Date:** 2026-03-12
**Goal:** Demonstrable MVP + arXiv paper + open-source release positioning
**Constraint:** Solo developer with full AI IDE assist

---

## Strategic Context

### What exists (Wave 0)
- Pure catamorphism kernel in Go — compiles, boots, self-seeds, serves HTTP
- 21-object ontology with operad validation, 22 categories, 5 functors (specified)
- 12 HTTP routes (9 read, 3 write), append-only morphism log, deterministic replay
- Curated industry layer (15 providers, 100+ tools, 11 protocols)
- Instance files for 11 of 21 kinds (52% coverage)
- System 3 AI synthesis document grounding the categorical approach

### What the landscape shows
- **No open-source categorical graph kernel exists** as runtime infrastructure (Catlab.jl is closest but targets scientific computing, not OS-layer)
- **Operads in software** is an emerging academic field with zero production implementations
- **MCP** is now the universal tool protocol (97M+ monthly SDK downloads, adopted by OpenAI/Google/Microsoft)
- **Local-first sovereign AI** is a $500B+ market narrative with no categorical foundation layer
- **"System 3"** is an open label — no one has rigorously defined it yet

### The positioning
mo:os is the first open-source categorical graph kernel that:
1. Reduces all state to 4 verified morphisms
2. Validates LLM tool proposals via operad constraints before execution
3. Provides complete causal audit via replay
4. Runs local-first with provider independence

---

## Week 1: Complete the Kernel Surface (Code)

**Theme:** Make `go run ./cmd/moos --kb .agent/knowledge_base` do everything.

### Day 1–2: Layer B — KB-Aware Boot

- [ ] Add `--kb <path>` flag to `cmd/moos/main.go`
- [ ] Auto-discover: `<kb>/superset/ontology.json` → registry
- [ ] Auto-discover: `<kb>/instances/distribution.json` → config
- [ ] Auto-resolve: morphism-log path from config or default
- [ ] Keep `--config` as override; `--kb` is the new default path
- [ ] Test: `go run ./cmd/moos --kb .agent/knowledge_base` boots cleanly

### Day 2–3: Layer D — Instance Hydration Flow

- [ ] Implement instance-file reader in `internal/hydration/`
  - Reads `instances/*.json`, extracts nodes and wires
  - Generates Programs per install.md spec (Programs 5–11)
  - Respects dependency order: providers → surfaces → tools → agents → benchmarks
- [ ] Wire `POST /hydration/materialize` handler to accept:
  - `{"source": "instances/providers.json"}` — file-based
  - Raw `MaterializeRequest` JSON — direct
- [ ] Add `--hydrate` boot flag: auto-apply Tier 2 Programs after seed
- [ ] Test: full de novo boot creates ~50–80 envelopes, all 21 kinds represented

### Day 4–5: Instance Gap Fill + Validation

- [ ] Create missing instance exemplars:
  - `OBJ02` ColliderAdmin in identities.json
  - `OBJ05` NodeContainer exemplar (generic container)
  - `OBJ10` ComputeResource (local GPU + cloud exemplar)
  - `OBJ12` InfraService (postgres, disk volume)
  - `OBJ13` MemoryStore (vector store stub)
- [ ] Add CAN_ROUTE morphism instances (MOR10) linking tools → surfaces
- [ ] Create `superset/schema.json` — JSON Schema v7 validating instances/*
- [ ] Run: boot with `--kb --hydrate`, verify all 21 kinds have ≥1 node in graph
- [ ] Run full test suite, ensure green

### Week 1 Deliverable
```
./moos --kb .agent/knowledge_base --hydrate
# Boots, loads registry, replays log, seeds Tier 1, hydrates Tier 2
# GET /state shows 50+ nodes, 80+ wires, all 21 kinds represented
# GET /log shows full morphism history
```

---

## Week 2: Differentiation Features (Code + Knowledge Base)

**Theme:** Build what nobody else has — operad-validated MCP bridge + scoped projections.

### Day 1–2: Layer C — Scoped Projections

- [ ] Implement `ScopedSubgraph(actor URN) GraphState` on `shell.Runtime`
  - BFS traversal following OWNS wires from actor
  - Returns filtered GraphState (only nodes/wires in actor's scope)
- [ ] Add `GET /state/scope/{actor}` endpoint
- [ ] Test: `GET /state/scope/urn:moos:user:demo-seeder` returns user's owned subgraph
- [ ] Test: `GET /state/scope/urn:moos:kernel:wave-0` returns kernel-owned subgraph

### Day 2–4: MCP Tool Surface (Layer F + new)

- [ ] Implement MCP server in `internal/mcp/` package
  - Transport: SSE on port 8080 (preset-compatible)
  - Expose kernel morphisms as MCP tools:
    - `moos_add` — ADD envelope via MCP
    - `moos_link` — LINK envelope via MCP
    - `moos_mutate` — MUTATE envelope via MCP
    - `moos_query` — read state/nodes/wires via MCP
    - `moos_hydrate` — materialize from instance file via MCP
  - Expose read operations as MCP resources:
    - `moos://state` — full graph
    - `moos://nodes/{urn}` — single node
    - `moos://scope/{actor}` — scoped subgraph
- [ ] **Operad validation on every MCP tool call** — this is the differentiator
  - LLM proposes a morphism → kernel validates via operad → accepts or rejects with structured error
  - Error includes: which constraint failed, what types were expected, what was received
- [ ] Test: connect Claude Code to kernel via `claude mcp add moos-kernel --transport sse http://localhost:8080/mcp/sse`
- [ ] Test: Claude proposes invalid morphism → kernel rejects with explanation

### Day 4–5: Benchmark Functor Scaffold (Layer H)

- [ ] Implement FUN05 scaffold in `internal/functor/benchmark.go`
  - Input: BenchmarkSuite + BenchmarkTask nodes
  - Output: BenchmarkScore nodes with SCORED_ON/EVALUATES_TASK/BENCHMARKED_BY wires
  - Compute: provider equivalence classes by score dimension
- [ ] Add `GET /functor/benchmark/{suite}` endpoint
  - Returns: provider rankings, equivalence classes, score distributions
- [ ] Populate `instances/benchmarks.json` with real published scores from industry data
  - Import Intelligence Index scores for top 5 providers
  - Import Arena Elo where available
- [ ] Test: `GET /functor/benchmark/industry-intelligence-v1` returns ranked provider list

### Week 2 Deliverable
```
# MCP bridge live — any AI agent can talk to kernel
claude mcp add moos-kernel --transport sse http://localhost:8080/mcp/sse

# Scoped projections work
curl localhost:8000/state/scope/urn:moos:user:demo-seeder

# Benchmark functor returns provider rankings
curl localhost:8000/functor/benchmark/industry-intelligence-v1

# Invalid morphism rejected with explanation
curl -X POST localhost:8080/mcp/sse -d '{"tool": "moos_add", "args": {"type_id": "invalid"}}'
# → Error: type_id "invalid" not in registry. Valid types: [User, Provider, ...]
```

---

## Week 3: Paper + Demo Polish

**Theme:** Write the paper, polish the demo, prepare the release.

### Day 1–3: arXiv Paper Draft

**Title (working):** "mo:os: A Categorical Graph Kernel for Verified Compositional Reasoning"

**Structure:**

1. **Abstract** (200 words)
   - Problem: LLM tool use lacks compositional verification
   - Approach: Categorical graph kernel with operad-validated morphisms
   - Result: 4 invariant operations, deterministic replay, provider independence
   - Claim: First open-source implementation of operadic composition for AI runtime

2. **Introduction** (1.5 pages)
   - LLMs compose tools without structural verification → hallucinated actions
   - Category theory provides composition guarantees (cite: Seven Sketches, Lawvere)
   - Hypergraph rewriting provides causal structure (cite: Wolfram)
   - Contribution: working kernel that reduces all state to 4 verified morphisms

3. **Background** (1 page)
   - Colored operads and algebras (cite: Royal Society operad paper)
   - Catamorphisms as universal folds
   - MCP as tool protocol (cite: Anthropic spec)
   - Neuro-symbolic verification (cite: LogicGraph)

4. **The mo:os Kernel** (3 pages)
   - 4.1 Categorical Model: objects, morphisms, natural transformations
   - 4.2 The Catamorphism: `state(t) = fold(log[0..t])`
   - 4.3 Operad Validation: constraint checking before execution
   - 4.4 Hydration Pipeline: S0 → S1 → S2 → S3 → S4
   - 4.5 Three-Layer Tower: Industry → Superset → Kernel

5. **Implementation** (2 pages)
   - Go package structure mirrors sub-operad algebra
   - Pure core / effect shell separation
   - MCP bridge with pre-execution validation
   - Benchmark functor for provider equivalence

6. **Evaluation** (1.5 pages)
   - Morphism validation: rejection rate on random vs structured inputs
   - Replay determinism: log replay produces identical state
   - Boot time: de novo install timing
   - Composition correctness: Programs 1–11 type-check
   - Comparison: what would this look like without operadic constraints?

7. **Related Work** (1 page)
   - Catlab.jl / AlgebraicJulia (scientific CT, not runtime)
   - Graph databases (Neo4j, etc. — no categorical semantics)
   - Neuro-symbolic systems (LogicGraph, DeepProbLog)
   - MCP ecosystem (no verification layer)

8. **Discussion & Future Work** (0.5 page)
   - Multiway branching (Wolfram-style)
   - GRPO training harness (System 3 reward signal)
   - Peer-to-peer morphism log federation
   - Template instantiation (subgraph patterns)

9. **Conclusion** (0.5 page)

**Figures (critical for credibility):**
- Fig 1: Three-layer tower diagram (Industry → Superset → Kernel)
- Fig 2: Catamorphism fold over morphism log → state reconstruction
- Fig 3: Operad validation: LLM proposes → kernel validates → accept/reject
- Fig 4: Hydration pipeline: S0 → S4 with example
- Fig 5: Benchmark functor: providers → equivalence classes
- Fig 6: Package dependency graph (pure core → shell → transport)

**LaTeX:** Use `acmart` or `llncs` template. Target: arXiv cs.AI + cs.PL cross-list.

### Day 3–4: Demo Script + README Rewrite

- [ ] Create `examples/demo.sh` — scripted walkthrough:
  1. Boot kernel from clean state
  2. Show self-seeding (GET /state shows kernel in its own graph)
  3. Hydrate providers + tools from instances
  4. Query scoped subgraph
  5. Submit morphism via MCP (valid — accepted)
  6. Submit morphism via MCP (invalid — rejected with explanation)
  7. Query benchmark functor
  8. Show morphism log (full audit trail)
- [ ] Record terminal session as asciinema or GIF
- [ ] Rewrite README.md for open-source audience:
  - Quick start (3 commands to running kernel)
  - What it does (1 paragraph)
  - Why it matters (sovereignty, verification, provider independence)
  - Architecture diagram
  - API reference (12 routes + MCP tools)
  - Link to paper

### Day 5: Explorer UI Polish

- [ ] Enhance `GET /explorer` (UI_Lens functor):
  - Graph visualization (nodes + wires, colored by Kind)
  - Click node → show payload, stratum, connections
  - Filter by Kind, Stratum, Category
  - Show morphism log as timeline
- [ ] Serve static HTML/JS from `internal/transport/static/`
- [ ] Test: open browser, see the typed graph, click around

### Week 3 Deliverable
- Paper draft complete (send to 1–2 reviewers for feedback)
- Demo script runs end-to-end
- README rewritten for public audience
- Explorer shows interactive graph

---

## Week 4: Release + Positioning

**Theme:** Ship it. Tag it. Tell people.

### Day 1–2: Release Engineering

- [ ] Clean up repo structure:
  - Ensure `.gitignore` covers: `data/morphism-log.jsonl`, `secrets/`, build artifacts
  - Add `CONTRIBUTING.md` (how to contribute, code conventions, PR process)
  - Add `CHANGELOG.md` (Wave 0 summary)
  - Verify LICENSE (MIT) is present ✓
  - Add `CODE_OF_CONDUCT.md` (standard Contributor Covenant)
- [ ] Add GitHub Actions CI:
  - `go test ./...` on push
  - `go vet ./...` + `golangci-lint`
  - Build binary for linux/darwin/windows
- [ ] Create `Makefile` or `justfile`:
  - `make build` — compile binary
  - `make test` — run all tests
  - `make run` — boot with default KB
  - `make demo` — run demo script
- [ ] Tag `v0.1.0` release on GitHub with:
  - Pre-built binaries (linux/darwin/windows)
  - Release notes summarizing Wave 0

### Day 2–3: Paper Finalize + Submit

- [ ] Incorporate reviewer feedback on paper draft
- [ ] Generate all figures (TikZ or draw.io → PDF)
- [ ] Write final abstract (this is what people read on arXiv listing)
- [ ] Submit to arXiv: primary cs.AI, cross-list cs.PL, cs.LO
- [ ] Upload preprint to GitHub releases as well

### Day 3–4: Documentation + Onboarding

- [ ] Write `docs/architecture.md` — the three-layer tower for developers
- [ ] Write `docs/ontology.md` — how to read and extend ontology.json
- [ ] Write `docs/mcp-bridge.md` — how to connect AI agents to kernel
- [ ] Write `docs/hydration.md` — how instance files become graph state
- [ ] Add inline Go doc comments to all exported functions
- [ ] Generate godoc and host (or just ensure `go doc` works cleanly)

### Day 4–5: Community Seeding

- [ ] Write launch blog post / announcement:
  - What mo:os is (1 paragraph)
  - The 4-morphism claim (with example)
  - The MCP bridge (with demo GIF)
  - Link to paper, repo, explorer
- [ ] Post to:
  - Hacker News (Show HN)
  - Reddit: r/golang, r/ProgrammingLanguages, r/MachineLearning
  - Lobsters
  - Category theory Discord/forums
  - MCP community channels
- [ ] Create GitHub Discussions (enable on repo)
- [ ] Create 2–3 "good first issue" tickets:
  - "Add Postgres store implementation"
  - "Implement FUN01 FileSystem functor"
  - "Add OpenAPI/Swagger spec for HTTP API"

### Week 4 Deliverable
- `v0.1.0` tagged and released with binaries
- Paper on arXiv
- Blog post / HN launch
- 3 good-first-issues for contributors
- Full documentation site

---

## Success Criteria (End of Week 4)

| Metric | Target |
|--------|--------|
| `go test ./...` | All green, ≥60 tests |
| De novo boot | Single command: `./moos --kb <path> --hydrate` |
| Graph state | 50+ nodes, 80+ wires, all 21 kinds |
| MCP bridge | Claude Code can read/write kernel via MCP |
| Operad rejection | Invalid morphisms rejected with structured errors |
| Benchmark query | Provider rankings from graph data |
| Explorer | Interactive graph visualization in browser |
| Paper | Submitted to arXiv |
| Release | v0.1.0 on GitHub with binaries |
| README | 3-command quickstart |

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| MCP implementation complexity | Start with SSE transport only; stdio later. Use existing Go MCP libraries if available. |
| Paper rejected / ignored | arXiv is preprint — no review gate. Quality of implementation IS the credibility. |
| Explorer UI scope creep | Keep it simple: D3.js force graph, click for details. No framework, no build step. |
| Instance gap fill takes too long | Prioritize OBJ10 (ComputeResource) and OBJ12 (InfraService) — others can be stubs. |
| Solo developer burnout | AI IDE assist handles boilerplate. Focus creative energy on paper figures and MCP bridge. |

---

## What This Plan Deliberately Defers

- **Postgres store** — file store is fine for MVP; Postgres is a "good first issue"
- **Multiway branching** — research-tier; paper mentions as future work
- **GRPO training harness** — needs benchmark functor first; Week 2 lays foundation
- **Standalone agent binary** — IDE copilot + MCP bridge covers the demo
- **Template instantiation (OBJ04)** — complex; AppTemplate is an extension point
- **Peer-to-peer federation** — paper mentions; implementation is post-MVP
- **Full functor implementations** — FUN05 (benchmark) is priority; others are paper future-work

---

## Daily Rhythm (Suggested)

```
Morning (2h):  Code — kernel features, tests
Midday  (1h):  Knowledge base — instance files, ontology fixes
Afternoon (2h): Code — MCP bridge, explorer, hydration
Evening (1h):  Paper — write one section, iterate figures
```

With AI IDE assist, the code portions compress significantly. The paper is the
bottleneck — figures and formal definitions require focused human thought.

---

## The Pitch (What You Tell People)

> mo:os is a categorical graph kernel. It reduces everything — tool calls,
> provider configs, agent state, governance — to 4 verified morphisms over
> a typed hypergraph. The kernel validates before executing. The log replays
> deterministically. Providers are interchangeable. Your machine is the
> authority, not the cloud.
>
> It's MIT licensed, it's written in Go, and it runs with one command.

---

*This plan lives at `.agent/knowledge_base/design/20260312-4week-mvp-plan.md`*
