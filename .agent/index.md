# FFS0 Factory - Agent Context

> Root workspace for the Collider ecosystem.

## Location

```
D:\FFS0_Factory\.agent\
```

## Core Concept

```
.agent/ = workspace state = purpose + relations + capabilities
```

All components (tools, workflows, apps) are the **same pattern at different scales**.

## Folder Structure

```
.agent/
├── manifest.yaml          ← Inheritance, exports
├── index.md               ← You are here
│
├── instructions/          ← WHO (role)
├── rules/                 ← WHAT constraints
├── skills/                ← HOW complex tasks
├── tools/                 ← WHAT atomic actions
├── workflows/             ← WHAT sequences
├── configs/               ← SETTINGS
└── knowledge/             ← REFERENCE
    └── architecture/      ← Core architecture docs
```

## Hierarchy

```
FFS0_Factory\.agent\              ← ROOT
    └── exports to ↓
FFS1_ColliderDataSystems\.agent\  ← IDE Context
    └── exports to ↓
FFS2, FFS3...                     ← Code Projects
```

## Exports to Children

| Category     | Files                          |
| ------------ | ------------------------------ |
| Rules        | sandbox.md, code_patterns.md   |
| Instructions | agent_system.md                |
| Configs      | users.yaml, api_providers.yaml |

## Three Domains

| Domain   | App         | Context             |
| -------- | ----------- | ------------------- |
| FILESYST | App X (IDE) | `.agent/` folders   |
| CLOUD    | Apps 1-N    | `node.container`    |
| ADMIN    | App Z       | `account.container` |

## Key Docs

- [Architecture Overview](./knowledge/architecture/00_overview.md)
- [Component Pattern](./knowledge/architecture/01_components.md)
- [Three Domains](./knowledge/architecture/02_domains.md)

---

_v2.0.0 — 2026-02-07_
