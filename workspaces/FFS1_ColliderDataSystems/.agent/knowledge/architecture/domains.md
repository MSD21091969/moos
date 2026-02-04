# Domains

> Three primary domains in Collider architecture.

## Overview

| Domain   | Name               | Context Storage      | Backend          |
| -------- | ------------------ | -------------------- | ---------------- |
| FILESYST | File Folder System | `.agent/` folders    | Native Messaging |
| CLOUD    | Cloud Workspaces   | DB nodecontainer     | Data Server      |
| ADMIN    | User Accounts      | DB account container | Data Server      |

## FILESYST Domain

**Purpose**: Local file folder workspaces (IDE context)

**Storage**: `.agent/` folders on filesystem

- `D:\FFS0_Factory\.agent\` (root)
- `D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\.agent\` (child)
- etc.

**Access**: Native Messaging → Python host → filesystem

**Sync**:

- File → Server: Daily/manual (Chrome extension triggers)
- Server → File: On-demand (manual/API)

## CLOUD Domain

**Purpose**: Cloud workspace nodecontainers (applications)

**Storage**: `container` field in node (PostgreSQL)

```json
{
  "node_id": "uuid",
  "container": {
    "manifest": "...",
    "instructions": [],
    "workflows": [],
    ...
  },
  "subnodes": [...]
}
```

**Access**: Data Server REST API

**Applications**: App 1, App 2, App 3... (each is an appnode tree)

## ADMIN Domain

**Purpose**: User account management

**Storage**: `container` field in account (PostgreSQL)

**Access**: Data Server REST API

**Contains**: Profile, permissions, secrets, managed application accounts

## Universal Pattern

All three domains use the same **nodecontainer pattern**:

- Node has subnodes (recursive)
- Node has container (context storage)
- Container has: manifest, instructions, rules, skills, tools, knowledge, workflows, configs

Difference is only in **storage backend** and **available tools**.
