# FFS1 ColliderDataSystems - Agent Context

> IDE workspace for Collider Data Systems code.

## Location

```text
D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\.agent\
```

## Hierarchy

```text
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

```text
.agent/
├── manifest.yaml          ← Inheritance config
├── index.md               ← You are here
│
├── instructions/          ← Agent prompts for IDE context
│   └── agent_system.md
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
│   └── _index.md
│
├── knowledge/
│   ├── _index.md
│   ├── architecture/      ← System architecture docs
│   │   └── _archive/      ← Archived architecture references
│   └── _archive_devlog/   ← Development session logs
│
└── workflows/
    ├── cross-service-validation-gates.md
    ├── dev-start.md
    ├── markdown-quality.md
    └── markdown-quality-all.md
```

## What Belongs Here

- **IDE code assist** context (skills, tools)
- **Architecture knowledge** (what we're building)
- **Development workflows** (testing, building)
- **Workspace-level** guidance for DB-backed NodeContainer runtime

## What Does NOT Belong Here

Per-application context belongs in the DataServer (node containers), not here:

- Application-specific tools → stored in `node.container.tools`
- Application-specific instructions → stored in `node.container.instructions`
- User secrets → stored in user's ADMIN container on DataServer
- DOM agent skills → Chrome Extension codebase (FFS2)

## Quick Links

- [Architecture Archive Index](knowledge/architecture/_archive/_index.md)
- [Skills Index](skills/_index.md)
- [Tools Index](tools/_index.md)
- [Dev Start](workflows/dev-start.md)
- [Cross-Service Validation Gates](workflows/cross-service-validation-gates.md)
