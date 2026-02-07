# FFS0 Factory - Agent Context

> Root workspace for all Collider development.

## Location

```
D:\FFS0_Factory\.agent\
```

## Hierarchy

```
FFS0_Factory\.agent\              ← This workspace (ROOT)
    └── exports to ↓
FFS1_ColliderDataSystems\.agent\  ← Child (IDE context)
    └── exports to ↓
FFS2, FFS3...                     ← Grandchildren (code projects)
```

## Folder Structure

```
.agent/
├── manifest.yaml          ← Root (includes: [])
├── index.md               ← You are here
│
├── instructions/
│   └── agent_system.md    ← Root instruction
│
├── rules/
│   ├── sandbox.md         ← Sandbox boundaries
│   ├── identity.md        ← Identity patterns
│   └── code_patterns.md   ← Coding standards
│
├── skills/
│   └── _index.md          ← Placeholder
│
├── tools/
│   └── _index.md          ← Placeholder
│
├── configs/
│   ├── users.yaml         ← User accounts
│   ├── api_providers.yaml ← API keys config
│   └── workspace_defaults.yaml
│
├── knowledge/             ← Factory-level knowledge
│
└── workflows/             ← Factory-level workflows
```

## Exports to Children

All child workspaces (FFS1, etc.) inherit:

| Category     | Files                                                   |
| ------------ | ------------------------------------------------------- |
| Rules        | sandbox.md, identity.md, code_patterns.md               |
| Instructions | agent_system.md                                         |
| Configs      | users.yaml, api_providers.yaml, workspace_defaults.yaml |

## Child Workspaces

| Workspace | Path                                   | Purpose              |
| --------- | -------------------------------------- | -------------------- |
| FFS1      | `workspaces/FFS1_ColliderDataSystems/` | Collider IDE context |

## MVP Status (2026-02-05)

**Fully Operational:**
- Backend API (FastAPI :8000)
- Portal Frontend (Next.js :3001)
- Chrome Extension (Plasmo)
- Database (PostgreSQL :5432)

**Running Guide:** `FFS1_ColliderDataSystems/.agent/knowledge/RUNNING.md`
