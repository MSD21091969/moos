# FFS6 Collider IDE - FILESYST Domain - Agent Context

> Web-based IDE for local file system access via Chrome Extension Native Messaging

## Location

`D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS3_ColliderApplicationsFrontendServer\FFS6_applicationx_FILESYST_ColliderIDE_appnodes\.agent\`

## Hierarchy

```
FFS0_Factory (Root)
  └── FFS1_ColliderDataSystems (IDE Context)
        └── FFS3_ColliderFrontend (Frontend Server)
              └── FFS6_IDE (This Application)
```

## Purpose

### User-Facing Purpose
The Collider IDE provides a full-featured development environment in the browser:
- Browse and edit local files via native host integration
- Code editing with syntax highlighting and IntelliSense
- Integrated terminal for command execution
- Project tree navigation
- Git integration
- File search and replace
- Multi-file editing with tabs

### Technical Role
Acts as a bridge between web-based IDE features and local file system:
- Uses Chrome Extension Native Messaging to access local files
- Renders Monaco Editor for code editing
- Provides XTerm.js for terminal emulation
- Manages project state and file changes
- Syncs with backend for persistence and collaboration

### Key Responsibilities
- Communicate with native host for file operations (read, write, delete)
- Provide rich code editing experience (Monaco Editor)
- Execute terminal commands via native host
- Manage project workspace and opened files
- Handle file watching and auto-reload
- Integrate with version control (Git)

## Key Components

### Pages/Routes
- `/ide` - Main IDE interface
- `/ide/project/:projectId` - Specific project view
- `/ide/file/:fileId` - Direct file access

### Main Components
- **FileExplorer** (`src/components/FileExplorer.tsx`) - Tree view of project files
- **CodeEditor** (`src/components/CodeEditor.tsx`) - Monaco Editor wrapper
- **Terminal** (`src/components/Terminal.tsx`) - XTerm.js terminal emulator
- **EditorTabs** (`src/components/EditorTabs.tsx`) - Multi-file tab management
- **SearchPanel** (`src/components/SearchPanel.tsx`) - File and content search
- **GitPanel** (`src/components/GitPanel.tsx`) - Version control UI
- **StatusBar** (`src/components/StatusBar.tsx`) - File info, cursor position, etc.

### State Management
- **Zustand stores** for IDE state
- Key stores:
  - `useIDEStore` - Opened files, active file, tabs
  - `useFileSystemStore` - File tree, watched files
  - `useTerminalStore` - Terminal sessions, history
  - `useGitStore` - Git status, branches, commits

### Integration Points

**Native Host (via Chrome Extension):**
- `READ_FILE` - Read file contents
- `WRITE_FILE` - Write file changes
- `LIST_DIRECTORY` - Get directory contents
- `WATCH_FILE` - Watch for file changes
- `EXECUTE_COMMAND` - Run terminal commands
- `GIT_COMMAND` - Execute Git operations

**Chrome Extension Messages:**
- Sent:
  - `NATIVE_MESSAGE` - Forward native host requests
  - `FILE_OPENED` - Notify file opened in IDE
- Received:
  - `NATIVE_RESPONSE` - Response from native host
  - `FILE_CHANGED` - External file change notification

**Backend APIs:**
- `POST /api/projects` - Create/save project
- `GET /api/projects/:id` - Load project configuration
- `POST /api/projects/:id/sync` - Sync project state

**Other FFS Apps:**
- FFS4 (Sidepanel): Navigate to files from Appnode Browser
- FFS8 (my-tiny-data): Store project metadata

## Development

### Running Locally

```bash
cd collider-frontend
pnpm dev
# Navigate to http://localhost:3000/ide
```

### Key Dependencies

- `@monaco-editor/react` - VS Code editor component
- `@xterm/xterm` - Terminal emulator
- `@xterm/addon-fit` - Terminal sizing
- `@xterm/addon-web-links` - Clickable links in terminal
- `@collider/api-client` - Backend API calls
- `prismjs` - Syntax highlighting fallback
- `file-icons-js` - File type icons

### Environment Variables

```bash
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_NATIVE_HOST_NAME=com.collider.nativehost
```

## Native Host Integration

The IDE requires a native host application installed on the user's system to access local files.

### Native Host Setup

1. **Install Native Host**:
   ```bash
   # Windows
   cd native-host
   python install-host.py

   # macOS/Linux
   cd native-host
   ./install-host.sh
   ```

2. **Verify Installation**:
   Chrome Extension will show "Native Host: Connected" in status

### Native Message Protocol

**Request Format:**
```typescript
{
  command: 'READ_FILE' | 'WRITE_FILE' | 'LIST_DIRECTORY' | 'EXECUTE_COMMAND',
  params: {
    path?: string,
    content?: string,
    command?: string,
    cwd?: string
  }
}
```

**Response Format:**
```typescript
{
  success: boolean,
  data?: any,
  error?: string
}
```

## Domain Context

- **Domain**: filesyst
- **App Type**: native-integration
- **Features**:
  - file_browser - Local file system access
  - code_editor - Monaco-based code editing
  - native_messaging - Chrome Native Messaging API
  - project_tree - Project workspace management
  - integrated_terminal - XTerm.js terminal
  - git_integration - Version control

## Security Considerations

- Native host requires explicit user permission
- File access limited to user-selected directories
- Terminal commands run with user's permissions
- No automatic file execution
- All native messages validated and sanitized

## Related Documentation

- FFS3 Frontend: `../knowledge/codebase.md`
- Chrome Extension: `../../../FFS2_ColliderBackends_MultiAgentChromeExtension/.agent/`
- Native Host: `../../../FFS2_ColliderBackends_MultiAgentChromeExtension/ColliderMultiAgentsChromeExtension/native-host/`
- Backend API: `../../../FFS2_ColliderBackends_MultiAgentChromeExtension/ColliderDataServer/.agent/`