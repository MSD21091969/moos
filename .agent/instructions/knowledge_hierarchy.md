# Knowledge Hierarchy Instructions

> These instructions define how knowledge flows through the factory workspace system.
> All agents MUST follow this hierarchy when reading or contributing knowledge.

## Knowledge Sources (Read-Only from Downstream)

| Source | Path | Purpose |
|--------|------|---------|
| Research | `factory/knowledge/research/` | New insights, experiments, discoveries |
| Development | `factory/knowledge/development/` | Implementation patterns, code recipes |
| Domains | `factory/knowledge/domains/` | Domain expertise (math, AI, etc.) |
| Projects | `factory/knowledge/projects/` | Project-specific accumulated knowledge |
| References | `factory/knowledge/references/` | External docs, specs, standards |
| Skills | `factory/knowledge/skills/` | Reusable capabilities, techniques |
| Workflows | `factory/knowledge/workflows/` | Process definitions, pipelines |
| Journal | `factory/knowledge/journal/` | Temporal notes, session logs |

## Access Pattern

```
FACTORY (upstream)
├── knowledge/              ← WRITE: Factory agents only
│   └── [all categories]
│
└── workspaces/
    ├── collider_apps/
    │   ├── knowledge/
    │   │   ├── factory_* → READ-ONLY (junctions to factory/knowledge)
    │   │   └── [local]   → WRITE: Workspace-level dev notes
    │   └── applications/
    │       └── my-tiny-data-collider/
    │           └── knowledge/
    │               ├── math, project → READ-ONLY (junctions)
    │               └── [local]       → WRITE: App impl logs
    │
    └── maassen_hochrath/
        └── knowledge/
            ├── factory_* → READ-ONLY (junctions)
            └── [local]   → WRITE: Personal dev notes
```

## Writing Knowledge

### Factory Level (knowledge/)
- **Who**: Factory architect, research agents
- **What**: Generalized patterns, reusable insights
- **When**: After validating in downstream projects
- **Format**: Markdown with code examples

### Workspace Level (workspaces/*/knowledge/)
- **Who**: Workspace agents, developers
- **What**: Cross-application dev knowledge, workspace-specific decisions
- **When**: During development, design decisions
- **Format**: Markdown, decision logs

### Application Level (applications/*/knowledge/)
- **Who**: Application agents, developers  
- **What**: Implementation details, bug fixes, feature logs
- **When**: During implementation
- **Format**: Implementation logs, troubleshooting notes

## Knowledge Promotion Flow

```
Application knowledge (specific)
        ↓ generalize
Workspace knowledge (cross-app patterns)
        ↓ validate & abstract
Factory knowledge (universal patterns)
```

## Junction Naming Convention

| Junction Name | Target |
|---------------|--------|
| `factory_research` | `knowledge/research/` |
| `factory_development` | `knowledge/development/` |
| `factory_domains` | `knowledge/domains/` |
| `math` | `knowledge/domains/mathematics/` |
| `project` | `knowledge/projects/[project_name]/` |
| `personal` | `knowledge/projects/maassen_hochrath/` |

---
*Factory Knowledge System v1.0*
