# Applications

> Application structure in Collider.

## Application Hierarchy

```
App 0 (Root Portal)
├── Always present
├── Domain-agnostic context
├── General agent instruction set
└── Domain indexes

App X (FILESYST Domain)
├── IDE for Collider Data Systems
├── Context from .agent/ folders
└── Skills: IDE code assist

App Z (ADMIN Domain)
├── Account management
├── Context from account containers
└── Admin functions

App 1, 2, 3... (CLOUD Domain)
├── Cloud workspace applications
├── Context from node containers
└── Full nodecontainer pattern
```

## Context Layering

```
┌────────────────────────────────────────┐
│ ACTIVE TAB CONTEXT (Layer N)           │
│ Specific appnode context               │
│ (App1/dashboard, AppX/FFS2, etc.)     │
├────────────────────────────────────────┤
│ APP 0 DEFAULT CONTEXT (Layer 0)        │
│ Always present                         │
│ General capabilities                   │
└────────────────────────────────────────┘
```

## Application Configuration

Each application has an ApplicationConfig that determines:

- Which domain it connects to
- Which backend to use
- Available tools/skills (admin-managed)
- User permissions (RBAC)

## Admin-Managed Settings

Features are **not hardcoded**. All applications have all features available. Admins configure which features are enabled per application.

Example: `configs/app_x.yaml` for FILESYST application settings.
