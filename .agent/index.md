# FFS0 Factory - Agent Context

> Root workspace for the Collider ecosystem.

## Location

```text
D:\FFS0_Factory\.agent\
```

## Core Concept

```text
.agent/ = workspace state = purpose + relations + capabilities
```

All components (tools, workflows, apps) are the **same pattern at different
scales**.

## Folder Structure

```text
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

```text
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

## Backend API Configs

Applications carry a "domain" label — a set of permitted backend APIs:

| Config   | APIs Enabled                     | Use Case             |
| -------- | -------------------------------- | -------------------- |
| FILESYST | Native Messaging, sync, file ops | Local workspace apps |
| CLOUD    | REST, SSE, WebSocket workflows   | Cloud-hosted apps    |
| ADMIN    | User management, role assignment | System management    |

This is a backend API config label on the application, not an architectural
concept.

## Key Docs

Architecture docs live in FFS1 (the IDE workspace):

- [Architecture Index](../workspaces/FFS1_ColliderDataSystems/.agent/knowledge/architecture/_index.md)
- [Backend Services](../workspaces/FFS1_ColliderDataSystems/.agent/knowledge/architecture/01_ffs2_backend_services.md)
- [Chrome Extension](../workspaces/FFS1_ColliderDataSystems/.agent/knowledge/architecture/02_ffs2_chrome_extension.md)
- [Frontend Appnodes](../workspaces/FFS1_ColliderDataSystems/.agent/knowledge/architecture/03_ffs3_frontend_appnodes.md)
- [Communication Protocols](../workspaces/FFS1_ColliderDataSystems/.agent/knowledge/architecture/04_communication_protocols.md)

---

Version: v3.0.0 — 2026-02-22
