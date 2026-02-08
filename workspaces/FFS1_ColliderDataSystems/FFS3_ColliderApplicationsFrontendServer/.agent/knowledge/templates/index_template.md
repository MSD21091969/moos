# [APP_NAME] - Agent Context

> [One sentence description of what this application does]

## Location

`[FULL_PATH_TO_APP]/.agent/`

## Hierarchy

```
FFS0_Factory (Root)
  └── FFS1_ColliderDataSystems (IDE Context)
        └── FFS3_ColliderFrontend (Frontend Server)
              └── [APP_NAME] (This Application)
```

## Purpose

[Detailed description of the application's purpose, including:]
- **User-Facing Purpose**: What users do with this app
- **Technical Role**: How it fits in the larger system
- **Key Responsibilities**: Main functions and features

## Key Components

### Pages/Routes
- `/path1` - Description
- `/path2` - Description

### Main Components
- **ComponentName** (`path/to/component.tsx`) - Purpose
- **AnotherComponent** (`path/to/another.tsx`) - Purpose

### State Management
- [Describe state management approach: Context API, Zustand, Redux, etc.]
- Key stores/contexts:
  - `StoreName` - What it manages

### Integration Points

**Backend APIs:**
- `GET /api/endpoint` - Purpose
- `POST /api/endpoint` - Purpose

**Chrome Extension (if applicable):**
- Messages sent/received
- Storage keys used

**Native Host (if applicable):**
- Commands supported
- Data formats

## Development

### Running Locally

```bash
cd collider-frontend
pnpm dev
# Access at http://localhost:3000/[app-route]
```

### Key Dependencies

- [List special dependencies unique to this app]
- [e.g., monaco-editor, xterm.js, etc.]

### Environment Variables

```bash
NEXT_PUBLIC_[VAR_NAME]=[description]
```

## Domain Context

- **Domain**: [filesyst | cloud | admin | sidepanel | pip-main-seat]
- **App Type**: [web-app | native-integration | extension-ui | admin-panel | picture-in-picture]
- **Features**: [List from manifest.yaml]

## Related Documentation

- FFS3 Frontend: `../knowledge/codebase.md`
- FFS1 System: `../../knowledge/architecture/`
- Backend APIs: `../../../FFS2_ColliderBackends/.agent/`
