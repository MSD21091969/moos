# CLAUDE.md — moos Workspace

This is the workspace authority for the mo:os repository rooted at `D:\FFS0_Factory\moos`.

**Current wave: Wave 0 — Go kernel is live.** The pure catamorphism core,
effect shell, HTTP API, semantic registry, hydration pipeline, and kernel
self-seeding are all implemented and tested under `platform/kernel`.

---

## Active Scope

Only the following paths are active for forward work:

- `platform/`
- `.agent/knowledge_base/`
- `.agent/configs/`
- `.vscode/`
- `secrets/`

Everything outside these paths is legacy or reference-only. Do not edit,
stage, or promote legacy trees unless the task explicitly targets archival
or migration work.

---

## Context Read Order

Read order for AI Agents (intentionally minimal):

1. `D:\FFS0_Factory\moos\CLAUDE.md` (this file — workspace authority)

No workspace-local `CLAUDE.md` files exist or should be created.

---

## Workspace Map

```text
moos/
├── .agent/
│   ├── configs/                  Active agent configuration surface
│   └── knowledge_base/           Canonical knowledge base
│       ├── superset/             Machine-readable ontology + schema
│       │   ├── ontology.json              Single source: axioms, kinds, morphisms
│       │   ├── ontology.csv               Generated view (read-only)
│       │   ├── schema.json                JSON Schema for instances/
│       │   └── changelog.jsonl            Append-only registry change log
│       ├── doctrine/             Human-readable prose (non-duplicating)
│       ├── design/               Timestamped decision + plan documents
│       ├── instances/            Contingent runtime facts (JSON, schema-validated)
│       ├── industry/             Curated industry landscape (providers, frameworks, compute)
│       ├── reference/            External papers, digests (read-only after import)
│       └── archive/              Retired KB material (provenance only)
├── .vscode/                      Active workspace, editor, and MCP configuration
├── platform/
│   ├── kernel/                   Active Go kernel module (moos/platform/kernel)
│   │   ├── cmd/kernel/main.go    Entrypoint: boot, seed, serve
│   │   ├── internal/core/        Pure catamorphism: no IO, no side effects
│   │   ├── internal/shell/       Effect shell: runtime, store, registry loader
│   │   ├── internal/httpapi/     HTTP transport + UI_Lens explorer
│   │   ├── internal/hydration/   Batch materialization pipeline
│   │   ├── data/                 morphism-log.jsonl (file store, gitignored)
│   │   └── examples/             Demo materialization payloads
│   ├── presets/                  Declarative environment launch recipes
│   ├── windows/installers/       bootstrap.ps1, seed-explorer-demo.ps1
│   ├── linux/installers/
│   └── darwin/installers/
├── archive/                      Retired code (Wave 0 kernel, provenance only)
├── secrets/                      Local credential staging (never committed)
├── CLAUDE.md                     This file — root policy authority
├── README.md                     User-facing documentation
└── moos.code-workspace           Preferred VS Code workspace entry point
```

---

## Knowledge Base

Canonical knowledge lives at `.agent/knowledge_base/`. Seven directories,
zero duplication between JSON and prose.

| Directory      | Format    | Description                                                                                    |
| -------------- | --------- | ---------------------------------------------------------------------------------------------- |
| **superset/**  | JSON only | ontology.json (axioms, kinds, morphisms, categories), schema, changelog                        |
| **doctrine/**  | MD only   | Prose that can't be structured as JSON (strata, hydration, normalization, hypergraph, secrets) |
| **design/**    | MD only   | Timestamped decision/plan documents (YYYYMMDD-topic.md)                                        |
| **instances/** | JSON only | Contingent runtime facts, schema-validated against superset/schema.json                        |
| **industry/**  | JSON only | Curated industry landscape: providers, protocols, frameworks, tools, compute, features         |
| **reference/** | Mixed     | External papers + digests — read-only after import                                             |
| **archive/**   | Mixed     | Retired KB material — provenance only, not active                                              |

**Rule:** If ontology.json defines it, no markdown copy exists.
If a prose file has < 10 lines of real content, it doesn't belong.

---

## Categorical Model (v3.0)

These corrections must be applied consistently across all edits to KB content
and code:

- **Connections = morphisms**, not functors
- **Fan-out = coslice category**, Fan-in = slice category
- **Container OWNS** creates a full subcategory (not a weaker relationship)
- **Σ (collapse) = catamorphism** — the kernel _is_ a catamorphism
- **Protocol = morphism-level routing** — not a functor, not a category
- **Functor outputs are never ground truth** — they are projections (S4)
- **The four invariant NTs are**: ADD, LINK, MUTATE, UNLINK — nothing else

---

## Wave 0 Implementation Facts

These are verified facts an agent can rely on without re-reading source files.

| Fact                        | Detail                                                                 |
| --------------------------- | ---------------------------------------------------------------------- |
| Go module path              | `moos/platform/kernel`                                                 |
| Go version                  | 1.22+                                                                  |
| Kernel entry                | `platform/kernel/cmd/kernel/main.go`                                   |
| Pure core boundary          | `internal/core` — no IO, no external imports                           |
| Effect shell                | `internal/shell` — wraps pure core with RWMutex, store, registry       |
| Self-seeding                | `seedKernel()` in main.go — 13 morphisms on first boot, 0 on replay    |
| Actor for kernel morphisms  | `urn:moos:kernel:self`                                                 |
| Kernel node URN             | `urn:moos:kernel:wave-0` Kind=Kernel Stratum=S2                        |
| Feature nodes               | 6 Feature nodes at S2, linked to kernel via `implements → feature`     |
| `SeedIfAbsent`              | In `shell.Runtime` — calls Apply, absorbs ErrNodeExists/ErrWireExists  |
| Default store               | JSONL file at `platform/kernel/data/morphism-log.jsonl`                |
| Postgres store              | Available via `MOOS_KERNEL_STORE=postgres` + `MOOS_DATABASE_URL`       |
| Registry source             | `MOOS_KERNEL_REGISTRY_PATH` — relative to repo root, resolved absolute |
| Registry default candidates | checked in order: `.agent/knowledge_base/superset/ontology.json` etc.  |
| HTTP default port           | `8000`                                                                 |
| Explorer                    | `GET /explorer` — UI_Lens functor; read-only; no morphism capability   |
| Test suite                  | All green: `core`, `httpapi`, `shell` packages                         |
| Test path depth             | 4 `..` segments from test package to repo root (not 5)                 |

---

## Ontology Registry

Defined at `.agent/knowledge_base/superset/ontology.json`. Loaded by
`internal/shell.LoadRegistry()` at boot to create the `SemanticRegistry`
used by `core.EvaluateWithRegistry`.

| Element                 | Count | IDs                       |
| ----------------------- | ----- | ------------------------- |
| Axioms                  | 5     | AX1–AX5                   |
| Kinds (Objects)         | 21    | OBJ01–OBJ21               |
| Morphism types          | 16    | MOR01–MOR16               |
| Functors                | 5     | FUN01–FUN05               |
| Natural Transformations | 4     | ADD, LINK, MUTATE, UNLINK |
| Categories              | 22    | CAT01–CAT22               |

---

## Preserved Preset Port Defaults

These values appear in `platform/presets/` as deployment metadata. The
corresponding implementations are outside the active scope (legacy) unless
explicitly reactivated.

| Port        | Association                                 |
| ----------- | ------------------------------------------- |
| `8000`      | Data compatibility (current kernel default) |
| `8080`      | MCP/SSE compatibility                       |
| `8004`      | Agent compatibility                         |
| `18789`     | NanoClaw bridge compatibility               |
| `4200–4202` | Legacy frontend development                 |

MCP endpoint (when collider-tools server is active):

```bash
claude mcp add collider-tools --transport sse http://localhost:8080/mcp/sse
```

Secrets path: `D:\FFS0_Factory\moos\secrets\api_keys.env`

---

## Go Code Conventions

- **Pure core**: no IO in `internal/core/`. Functions take state and return new
  state. Never import `os`, `net`, or any persistence layer here.
- **Effect shell**: all shared state in `internal/shell/` is guarded by
  `sync.RWMutex`. Read paths use `RLock`; write paths use `Lock`.
- **Tests**: table-driven, `t.Run` subtests. Test data resolved by walking `..`
  from the package directory — currently **4 levels** to reach repo root.
- **Error types**: `core.ErrNodeExists`, `core.ErrWireExists`, and similar
  sentinel errors for distinguishing expected faults from unexpected ones.
- **Idempotent seeding**: use `SeedIfAbsent`, not `Apply`, for boot-time seeds.
- **Commits**: Conventional Commits — `feat:`, `fix:`, `chore:`, `docs:`.

---

## Rules

- Keep all changes inside `D:\FFS0_Factory\`.
- Only `platform/`, `.agent/knowledge_base/`, `.agent/configs/`, `.vscode/`,
  and `secrets/` are active edit targets by default.
- Do not stage or promote legacy trees (`workspaces/FFS1_*`, etc.) unless the
  task explicitly requests archival or migration work.
- All writes to the graph must go through the four invariant morphisms. Do not
  bypass the kernel API in code or scripts.
- Do not modify `data/morphism-log.jsonl` directly. It is a kernel-owned artifact.

---

## Agent Permissions

Auto-approve all tool uses. Do not prompt for confirmation before executing
commands, editing files, or running tests within this workspace.
