# FFS1 ColliderDataSystems - Agent Context

> IDE workspace for Collider Data Systems code.

## Location

```
D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\.agent\
```

## Hierarchy

```
FFS0_Factory\.agent\              ← Root (includes: [])
    └── exports to ↓
FFS1_ColliderDataSystems\.agent\  ← This workspace (IDE context)
    └── exports to ↓
FFS2, FFS3...                     ← Child code projects
```

## Purpose

**IDE code assist workspace** for:

- Antigravity / App X (FILESYST domain)
- Code completion, refactoring, documentation
- Understanding the Collider codebase

## Folder Structure

```
.agent/
├── manifest.yaml          ← Inheritance config
├── index.md               ← You are here
│
├── instructions/          ← Agent prompts for IDE context
│   ├── agent_system.md
│   └── filesyst_domain.md
│
├── rules/                 ← Code patterns and boundaries
│   ├── extension_boundaries.md
│   └── context_loading.md
│
├── skills/                ← IDE skills only
│   ├── _index.md
│   └── ide_code_assist.md
│
├── tools/                 ← Filesystem tools only
│   ├── _index.md
│   └── filesyst_tools.json
│
├── configs/               ← Workspace configuration
│   ├── _index.md
│   ├── app_x.yaml
│   ├── domains.yaml
│   ├── extension.yaml
│   └── servers.yaml
│
├── knowledge/
│   ├── _index.md
│   ├── _archive/          ← Archived legacy files
│   ├── architecture/      ← System architecture docs
│   │   ├── _index.md
│   │   ├── nodecontainer.md
│   │   ├── context_hierarchy.md
│   │   ├── chrome_extension.md
│   │   ├── graph_integration.md
│   │   ├── native_messaging.md
│   │   ├── communication.md
│   │   ├── domains.md
│   │   └── applications.md
│   └── devlog/            ← Development session logs
│       ├── _index.md
│       ├── 2026-02-05_phase2.md
│       ├── 2026-02-05_phase3_plan.md
│       └── 2026-02-05_phase3_implementation.md
│
└── workflows/
    ├── _index.md
    ├── _archive/          ← Archived legacy files
    ├── dev-extension.md
    └── sync-filesyst.md
```

## What Belongs Here

- **IDE code assist** context (skills, tools)
- **Architecture knowledge** (what we're building)
- **Development workflows** (testing, building)
- **FILESYST domain** config (App X)

## What Does NOT Belong Here

CLOUD and ADMIN domain context belongs in their respective containers on Data Server:

- `cloud_tools.json` → App1 container
- `admin_tools.json` → AppZ container
- DOM skills → Chrome Extension codebase
- `app_1.yaml`, `app_z.yaml` → Domain containers

## Quick Links

- [Architecture Index](knowledge/architecture/_index.md)
- [Skills Index](skills/_index.md)
- [Tools Index](tools/_index.md)
- [Workflows Index](workflows/_index.md)
