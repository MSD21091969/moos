# Changelog

All notable changes to mo:os are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] — 2026-03-15

Wave 0 — categorical graph kernel, complete with typed operad, MCP bridge, and Explorer UI.

### Added

**Core kernel**

- Categorical graph kernel with 4 invariant morphisms: `ADD`, `LINK`, `MUTATE`, `UNLINK`
- Σ-catamorphism evaluator (`fold` package) — pure, zero IO, zero external deps
- 21-object typed operad with port-level validation (`operad` package)
- `allowed_strata` read from `ontology.json` — operad registry now fully driven by KB
- Deterministic morphism log replay — same graph state on every restart
- `SeedIfAbsent` — idempotent seeding on boot

**Boot & hydration**

- `--kb <path>` flag — KB-aware boot, reads ontology + instances from any directory
- `--hydrate` flag — batch materialization of all instance files on first boot
- Structured KB instance format: `glossary.json`, `categories.json`, `kinds.json`, `providers.json`, `agents.json`, …
- Schema validation for instance files (JSON Schema draft-07)

**HTTP API — 16 routes on `:8000`**

- `GET /healthz` — liveness + node/wire counts
- `GET /state` — full graph snapshot
- `GET /state/nodes`, `/state/wires` — typed subsets
- `GET /state/wires/outgoing/{urn}`, `/state/wires/incoming/{urn}` — coslice / slice
- `GET /state/scope/{urn}` — scoped subgraph (OWNS closure)
- `POST /morphisms` — apply single envelope
- `POST /programs` — apply atomic program (all-or-nothing)
- `GET /log` — append-only morphism log with `?after`, `?actor`, `?type`, `?limit` filters
- `GET /log/stream` — SSE live morphism stream
- `GET /semantics/registry` — loaded ontology registry
- `POST /hydration/materialize` — batch materialization
- `GET /functor/ui` — FUN02 UI_Lens projection
- `GET /functor/benchmark/{suite}` — FUN05 Benchmark functor projection
- `GET /explorer` — embedded Explorer UI

**MCP bridge — `:8080`**

- JSON-RPC 2.0 over SSE (MCP spec 2024-11-05)
- `initialize` handshake with server capabilities
- 5 tools: `graph_state`, `node_lookup`, `apply_morphism`, `scoped_subgraph`, `benchmark_project`
- Session management, non-blocking SSE

**Explorer UI**

- Dark-theme SVG canvas with category grid layout (broad_category × stratum axes)
- Sidebar with node cards, kind pills, stratum badges
- Real-time search — filters sidebar cards, dims non-matching SVG nodes
- Glossary toggle (`urn:moos:cat:*`) and kernel/feature node toggle
- Pan (drag) + zoom (scroll wheel, 0.15×–5×)
- Card click → pan SVG to node with highlight animation
- Live morphism feed via SSE (`/log/stream`)

**Functors**

- FUN02 `UI_Lens` — `F_ui: C → React` (category grid layout, deterministic)
- FUN05 `Benchmark` — `F_bench: Provider → Met` (rankings, distributions, equivalence classes)

**Observability**

- `GET /log/stream` SSE — live morphism stream per subscriber
- Non-blocking pub/sub in `shell.Runtime` (buffered 64, separate mutex)
- Actor-scoped audit: `?actor=` filter on `/log`

**Graph content — 118 nodes, 131 wires**

- 51 `urn:moos:cat:*` categorical ontology nodes at S1 (glossary, categories, kinds)
- Agent nodes: `urn:moos:agent:{claude-code,vscode-ai,antigraviti,copilot-interim}`
- Provider nodes: openai, anthropic, meta, google, ollama, local-cpu
- Benchmark suites: Industry Intelligence Index, Morphism Extraction Baseline

### Metrics

| Metric                | Value |
| --------------------- | ----- |
| Nodes                 | 118   |
| Wires                 | 131   |
| Log depth             | 249   |
| Test packages         | 8     |
| Lines of code         | ~4K   |
| External dependencies | 0     |

### Architecture

```
cmd/moos          Entrypoint — flag parsing, seeding, server init
internal/cat      Pure types: Node, Wire, URN, TypeID, Stratum, Port, Envelope
internal/fold     Σ-catamorphism — pure evaluation, zero IO
internal/operad   Typed operad — port validation, ontology-driven TypeSpecs
internal/shell    Effect boundary — RWMutex, Apply, Subscribe, Store
internal/hydration Batch materialization — KB JSON → morphism Programs
internal/functor  Read-path projections — FUN02 UI_Lens, FUN05 Benchmark
internal/mcp      MCP bridge — JSON-RPC 2.0 over SSE
internal/transport HTTP API — 16 routes, embedded Explorer UI
```

---

## [Unreleased]

- PostgreSQL store (`MOOS_KERNEL_STORE=postgres`)
- FUN03 Embedding functor (`F_embed: payload → ℝ^1536`)
- FUN04 Structure functor (`F_struct: subgraph → DAG`)
- Multi-kernel network topology
