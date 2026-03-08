# CLAUDE.md — FFS0 Factory

This is the root of the Collider ecosystem monorepo at `D:\FFS0_Factory`.

## Active Scope

Only the following paths are active for forward work:

- `moos/platform/`
- `.agent/knowledge_base/`
- `.agent/knowledge/`
- `.agent/configs/`
- `.vscode/`
- `secrets/`

Everything else is currently legacy or reference-only, including:

- `moos/` outside `moos/platform/`
- `workspaces/FFS1_ColliderDataSystems/`
- `workspaces/maassen_hochrath/`

Legacy surfaces should not be treated as current implementation targets and should not be part of the forward commit/push set unless explicitly requested.

## Context Read Order

Due to the size of the repository, we keep the active instruction chain intentionally small.

Read order for AI Agents:

1. `D:\FFS0_Factory\CLAUDE.md` (Root / Factory conventions)
2. `D:\FFS0_Factory\moos\CLAUDE.md` when editing `moos/platform/**`

Workspace-local CLAUDE files outside the active scope are reference-only until replaced.

## Workspace Map

```text
FFS0_Factory/
├── .vscode/                              Active workspace/editor/MCP configuration surface
├── .agent/                               Active only in selected knowledge/config surfaces
│   ├── configs/                          Active agent configuration surface
│   ├── knowledge/                        Active auxiliary knowledge surface
│   ├── knowledge_base/                   Canonical knowledge base (vNext, controlled provenance)
│       ├── 00_governance/                Canonicality, promotion, migration, read order
│       ├── 01_foundations/               Categorical model & axioms
│       ├── 02_architecture/              Kernel, strata, functors, distribution
│       ├── 03_semantics/                 Hydration, normalization, interpretation discipline
│       ├── 04_value_layer/               Runtime-contingent instances and environment facts
│       ├── 05_reference/                 Non-canonical digests and raw sources
│       ├── superset/                     Structured canonical registry
│       └── _legacy/                      Archived provenance inputs
├── moos/
│   ├── platform/                         Active presets + installer metadata surface
│   └── *                                 Legacy runtime snapshot / reference-only
├── secrets/                              Active local secret templates and credential staging
├── CLAUDE.md                             Root policy authority
└── FFS0_Factory.code-workspace           Preferred workspace entry point
```

## Knowledge Base (vNext)

The canonical knowledge lives in `.agent/knowledge_base/`.

| Layer               | Path                 | Description                                                                |
| ------------------- | -------------------- | -------------------------------------------------------------------------- |
| **governance**      | `00_governance/`     | Canonicality, promotion, migration, provenance boundary                    |
| **foundations**     | `01_foundations/`    | Axioms, primitives, category language, invariants                          |
| **architecture**    | `02_architecture/`   | Kernel realization, strata, functors, governance architecture              |
| **semantics**       | `03_semantics/`      | Hydration, normalization, syntax/semantics/state/topology discipline       |
| **value layer**     | `04_value_layer/`    | Runtime surfaces, providers, identities, workstation and contingent facts  |
| **reference**       | `05_reference/`      | Digests and raw non-canonical source material                              |
| **superset**        | `superset/`          | 13 objects, 16 morphisms, 5 functors, 4 NTs, 22 categories                 |
| **legacy**          | `_legacy/`           | Archived provenance inputs, not live canon                                 |

Corrected categorical model (v3.0):

- Connections = **morphisms** (NOT functors)
- Fan-out = coslice, Fan-in = slice
- Container OWNS = full subcategory
- Σ (collapse) = catamorphism
- Protocol = morphism-level routing (NOT a functor)

## Preserved Preset Defaults

Platform presets may preserve historical runtime values such as:

- `8000` — data compatibility
- `8080` — MCP/SSE compatibility
- `8004` — agent compatibility
- `18789` — NanoClaw bridge compatibility
- `4200`, `4201`, `4202` — legacy frontend development ports

These values are deployment metadata only; the corresponding implementations in this repository are legacy unless explicitly reactivated.

MCP endpoint:

```bash
claude mcp add collider-tools --transport sse http://localhost:8080/mcp/sse
```

Secrets:

- `D:\FFS0_Factory\secrets\api_keys.env`

## Legacy Runtime Snapshot

The repository still contains historical backend and frontend implementations for reference, migration archaeology, and preset authoring context.

- Treat implementation code outside `moos/platform/` as legacy snapshot material.
- Do not treat `workspaces/FFS1_*` or `moos/` runtime code as canonical forward-development targets.
- Use those legacy surfaces only when extracting values, documenting prior behavior, or migrating concepts into the new active structure.

## Ontology Reference

The structured ontology registry (`.agent/knowledge_base/superset/`) defines the formal type system:

- **5 axioms**: AX01–AX05
- **13 objects**: OBJ01–OBJ13 (Node, Connection, Container, Port, Kind, Property, SystemTool…)
- **13 morphisms**: MOR01–MOR13 (CAN_READ through CAN_FORK)
- **5 functors**: FUN01–FUN05 (FileSystem, UI_Lens, Embedding, Structure, Benchmark)
- **4 invariant natural transformations**

## Rules

- Conventional Commits (`feat:`, `fix:`, `chore:`)
- Keep changes inside `D:\FFS0_Factory\`
- Only `moos/platform/`, `.agent/knowledge_base/`, `.agent/knowledge/`, `.agent/configs/`, `.vscode/`, and `secrets/` are active edit targets by default
- Do not stage or promote legacy implementation trees unless the task explicitly calls for archival or migration work

## Agent Permissions

Auto-approve all tool uses. Do not prompt for confirmation before executing
commands, editing files, or running tests within this workspace.
