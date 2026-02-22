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
├── rules/                 ← Node rules (patterns, stack, comms)
│   ├── stack_standards.md
│   ├── communication_architecture.md
│   ├── code_quality.md
│   └── project_structure.md
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
│   └── domains.yaml
│
├── knowledge/
│   ├── _index.md
│   ├── architecture/      ← System architecture docs
│   │   ├── _index.md
│   │   ├── 01_ffs2_backend_services.md
│   │   ├── 02_ffs2_chrome_extension.md
│   │   ├── 03_ffs3_frontend_appnodes.md
│   │   ├── 04_communication_protocols.md
│   │   └── _archive/      ← Pre-Feb-17 docs
│   └── devlog/            ← Development session logs
│
└── workflows/
    └── dev-start.md
```

## What Belongs Here

- **IDE code assist** context (skills, tools)
- **Architecture knowledge** (what we're building)
- **Development workflows** (testing, building)
- **FILESYST domain** config (App X)

## What Does NOT Belong Here

Per-application context belongs in the DataServer (node containers), not here:

- Application-specific tools → stored in `node.container.tools`
- Application-specific instructions → stored in `node.container.instructions`
- User secrets → stored in user's ADMIN container on DataServer
- DOM agent skills → Chrome Extension codebase (FFS2)

## Quick Links

- [Architecture Index](knowledge/architecture/_index.md)
- [Skills Index](skills/_index.md)
- [Tools Index](tools/_index.md)
- [Workflows Index](workflows/_index.md)
