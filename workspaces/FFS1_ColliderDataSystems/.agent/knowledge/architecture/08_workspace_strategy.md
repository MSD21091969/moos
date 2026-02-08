# Workspace Strategy

## Overview

This document explains when to use VSCode `.code-workspace` files vs `.vscode/settings.json` vs `.agent/` directories in the FFS structure.

## Current Structure

```
FFS0_Factory/
├── FFS0_Factory.code-workspace ✓
├── .agent/
└── workspaces/
    ├── FFS1_ColliderDataSystems/
    │   ├── FFS1_ColliderDataSystems.code-workspace ✓
    │   ├── .agent/
    │   ├── FFS2_ColliderBackends_MultiAgentChromeExtension/
    │   │   ├── .agent/
    │   │   ├── ColliderDataServer/
    │   │   │   ├── .vscode/settings.json ✓
    │   │   │   └── .agent/
    │   │   ├── ColliderGraphToolServer/
    │   │   │   ├── .vscode/settings.json ✓
    │   │   │   └── .agent/
    │   │   ├── ColliderVectorDbServer/
    │   │   │   ├── .vscode/settings.json ✓
    │   │   │   └── .agent/
    │   │   └── ColliderMultiAgentsChromeExtension/
    │   │       ├── .vscode/settings.json ✓
    │   │       └── .agent/
    │   └── FFS3_ColliderApplicationsFrontendServer/
    │       ├── .agent/
    │       └── collider-frontend/
    │           ├── .vscode/settings.json ✓
    │           └── apps/
    │               ├── FFS4_application00_ColliderSidepanelAppnodeBrowser/.agent/
    │               ├── FFS5_application01_ColliderPictureInPictureMainAgentSeat/.agent/
    │               ├── FFS6_applicationx_FILESYST_ColliderIDE_appnodes/.agent/
    │               ├── FFS7_applicationz_ADMIN_ColliderAccount_appnodes/.agent/
    │               ├── FFS8_application1_CLOUD_my-tiny-data-collider_appnodes/.agent/
    │               ├── FFS9_application2_CLOUD_future-external-website1_appnodes/.agent/
    │               └── FFS10_application3_CLOUD_future-external-website2_appnodes/.agent/
    └── maassen_hochrath/
        ├── maassen_hochrath.code-workspace ✓
        └── .agent/
```

## Three Configuration Systems

### 1. `.code-workspace` Files

**Purpose:** Define multi-root workspaces for VSCode with workspace-level settings.

**Use When:**
- Independent development context (different team, client, or product area)
- Need to open as standalone workspace
- Multi-folder workspace needed (multiple related folders as roots)
- Different tool configurations at workspace level
- Separate development workflows

**Current Usage:**
- `FFS0_Factory.code-workspace` - Master view, multi-project orchestration
- `FFS1_ColliderDataSystems.code-workspace` - Daily development, full-stack work
- `maassen_hochrath.code-workspace` - Separate client/project

**Do NOT Use For:**
- Leaf projects (FFS4-10 apps)
- Tightly coupled components that are worked on together
- Pure organizational subdirectories

### 2. `.vscode/settings.json` Files

**Purpose:** Project-specific VSCode editor settings and tool configurations.

**Use When:**
- Specific language server configuration (Pylance, TypeScript)
- Formatter preferences (Black, Prettier)
- Linter settings (ESLint, Ruff)
- File associations and exclusions
- Editor behavior customization

**Current Usage:**
- All FFS2 servers (Python servers: Pylance + Black)
- Chrome extension (TypeScript + Prettier)
- FFS3 collider-frontend (Nx + Next.js + TypeScript + ESLint)

**Key Settings for AI Visibility:**
```json
{
  "search.exclude": {
    "**/.agent": false
  },
  "files.watcherExclude": {
    "**/.agent": false
  },
  "files.associations": {
    "**/.agent/**/*.md": "markdown",
    "**/.agent/**/*.yaml": "yaml"
  },
  "github.copilot.enable": {
    "*": true
  }
}
```

### 3. `.agent/` Directories

**Purpose:** AI agent context, instructions, and knowledge for code assistance.

**Use At Every Level:**
- FFS0 (Factory root)
- FFS1 (Data systems)
- FFS2 (Backend layer)
- Each FFS2 server
- FFS3 (Frontend layer)
- FFS4-10 (Each application)

**Structure:**
```
.agent/
├── manifest.yaml       # Inheritance config
├── index.md           # Overview/README
├── configs/           # Configuration files
├── instructions/      # Coding guides
├── knowledge/         # Documentation
├── rules/            # Code standards
├── skills/           # AI skills
├── tools/            # Tool definitions
└── workflows/        # Automation workflows
```

**Inheritance Chain:**
```
FFS0 exports → FFS1 includes from FFS0
FFS1 exports → FFS2/FFS3 include from FFS1
FFS3 exports → FFS4-10 include from FFS3
```

## Decision Matrix

| Level                  | .code-workspace | .vscode/settings.json    | .agent/            |
| ---------------------- | --------------- | ------------------------ | ------------------ |
| FFS0 (Factory)         | ✅ Master view   | ❌ Use workspace settings | ✅ Root context     |
| FFS1 (Data Systems)    | ✅ Daily dev     | ❌ Use workspace settings | ✅ IDE context      |
| FFS2 (Backends)        | ❌ Not needed    | ❌ Layer level only       | ✅ Backend context  |
| FFS2 Servers           | ❌ Use FFS1      | ✅ Python configs         | ✅ Server-specific  |
| FFS3 (Frontend)        | ❌ Not needed    | ❌ Layer level only       | ✅ Frontend context |
| FFS3 collider-frontend | ❌ Use FFS1      | ✅ Nx + TypeScript        | ✅ Monorepo context |
| FFS4-10 (Apps)         | ❌ Use FFS1      | ❌ Inherit from parent    | ✅ App-specific     |

## Workflow Recommendations

### Daily Development
**Open:** `FFS1_ColliderDataSystems.code-workspace`
- Includes all subsystems (FFS2, FFS3)
- Full context for backend + frontend work
- All .agent directories visible to AI

### Factory Overview
**Open:** `FFS0_Factory.code-workspace`
- Multi-project management
- High-level architecture work
- Cross-project orchestration

### Separate Team Model (Optional)
If you split backend/frontend teams, you could add:
- `FFS2_ColliderBackends.code-workspace`
- `FFS3_ColliderFrontendServer.code-workspace`

But this is NOT recommended unless teams work independently.

## AI Assistant Integration

All `.agent/` directories are made visible to AI assistants through:

1. **Workspace settings** (in .code-workspace files):
```json
"search.exclude": {
  "**/.agent": false
}
```

2. **Project settings** (in .vscode/settings.json):
```json
"search.exclude": {
  "**/.agent": false
},
"files.watcherExclude": {
  "**/.agent": false
}
```

3. **Manifest inheritance** (.agent/manifest.yaml):
```yaml
includes:
  - path: "../.agent"
    type: workspace
```

This ensures:
- AI can read instructions at all levels
- Context inheritance works properly
- Knowledge is accessible in searches
- Rules and patterns are enforced

## Best Practices

1. **Minimize .code-workspace files** - Only at logical workspace boundaries
2. **Use .vscode/settings.json** for project-specific tooling
3. **Always include .agent/** at every architectural level
4. **Document inheritance** in manifest.yaml files
5. **Test AI visibility** after adding new .agent directories

## Related Documentation

- `01_components.md` - Component architecture
- `02_domains.md` - Domain structure
- `manifest.yaml` files - Inheritance configuration
