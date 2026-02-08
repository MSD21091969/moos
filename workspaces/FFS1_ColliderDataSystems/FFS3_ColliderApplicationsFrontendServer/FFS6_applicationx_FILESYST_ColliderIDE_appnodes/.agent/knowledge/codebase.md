# Codebase: FFS6 Collider IDE - FILESYST Domain

> Next.js web-based IDE with Monaco Editor, XTerm.js terminal, and Chrome Native Messaging for local file system access

## Overview

The Collider IDE is a browser-based development environment that provides VS Code-like functionality through web technologies. It leverages Chrome Extension Native Messaging to bridge the gap between the browser sandbox and the local file system, enabling users to edit local files, run terminal commands, and manage Git repositories directly from the browser.

## Directory Structure

```
collider-frontend/apps/ide/
├── app/
│   ├── ide/
│   │   ├── page.tsx                    # Main IDE page
│   │   ├── layout.tsx                  # IDE layout wrapper
│   │   └── project/
│   │       └── [projectId]/
│   │           └── page.tsx            # Project-specific IDE view
├── components/
│   ├── FileExplorer/
│   │   ├── FileExplorer.tsx            # Main tree view
│   │   ├── FileTreeNode.tsx            # Individual file/folder node
│   │   └── ContextMenu.tsx             # Right-click actions
│   ├── CodeEditor/
│   │   ├── CodeEditor.tsx              # Monaco wrapper
│   │   ├── EditorSettings.tsx          # Editor configuration UI
│   │   └── IntelliSenseProvider.tsx    # Code completion
│   ├── Terminal/
│   │   ├── Terminal.tsx                # XTerm.js wrapper
│   │   ├── TerminalTabs.tsx            # Multiple terminal sessions
│   │   └── TerminalCommands.tsx        # Command palette
│   ├── EditorTabs/
│   │   ├── EditorTabs.tsx              # Tab bar
│   │   ├── Tab.tsx                     # Individual tab
│   │   └── TabContextMenu.tsx          # Tab actions
│   ├── SearchPanel/
│   │   ├── SearchPanel.tsx             # File/content search
│   │   ├── SearchResults.tsx           # Results list
│   │   └── ReplaceDialog.tsx           # Find and replace
│   ├── GitPanel/
│   │   ├── GitPanel.tsx                # Git UI
│   │   ├── CommitHistory.tsx           # Commit log
│   │   ├── DiffViewer.tsx              # File diffs
│   │   └── BranchSelector.tsx          # Branch management
│   └── StatusBar/
│       └── StatusBar.tsx               # Bottom status bar
├── hooks/
│   ├── useNativeHost.ts                # Native messaging
│   ├── useFileSystem.ts                # File operations
│   ├── useTerminal.ts                  # Terminal control
│   ├── useGit.ts                       # Git operations
│   └── useEditor.ts                    # Editor state
├── stores/
│   ├── ideStore.ts                     # Main IDE state
│   ├── fileSystemStore.ts              # File tree state
│   ├── terminalStore.ts                # Terminal sessions
│   └── gitStore.ts                     # Git state
├── services/
│   ├── nativeHost.ts                   # Native host client
│   ├── fileWatcher.ts                  # File change detection
│   └── gitClient.ts                    # Git command wrapper
└── types/
    ├── ide.ts                          # IDE types
    ├── file.ts                         # File system types
    └── nativeHost.ts                   # Native messaging types
```

## Component Architecture

### Core Components

**FileExplorer** (`components/FileExplorer/FileExplorer.tsx`)
- **Purpose**: Tree view of project files and folders
- **Props**:
  - `rootPath: string` - Root directory path
  - `onFileSelect: (path: string) => void` - File selection handler
- **State**: Expanded folders, selected file
- **Dependencies**: FileTreeNode (recursive child nodes)
- **Integration**: Uses `useFileSystem` hook for file operations

**CodeEditor** (`components/CodeEditor/CodeEditor.tsx`)
- **Purpose**: Monaco Editor wrapper for code editing
- **Props**:
  - `filePath: string` - Currently opened file
  - `content: string` - File contents
  - `language: string` - Syntax highlighting language
  - `onChange: (content: string) => void` - Content change handler
- **State**: Editor instance, cursor position, selection
- **Dependencies**: `@monaco-editor/react`
- **Integration**: Loads/saves via `useNativeHost`

**Terminal** (`components/Terminal/Terminal.tsx`)
- **Purpose**: XTerm.js terminal emulator
- **Props**:
  - `sessionId: string` - Terminal session ID
  - `cwd: string` - Current working directory
- **State**: Terminal instance, command history
- **Dependencies**: `@xterm/xterm`, `@xterm/addon-fit`
- **Integration**: Executes commands via native host

**EditorTabs** (`components/EditorTabs/EditorTabs.tsx`)
- **Purpose**: Multi-file tab management
- **Props**:
  - `files: OpenFile[]` - List of opened files
  - `activeFileId: string` - Currently active file
  - `onTabChange: (fileId: string) => void` - Tab switch handler
  - `onTabClose: (fileId: string) => void` - Tab close handler
- **State**: Tab order, unsaved changes indicators
- **Dependencies**: Tab component
- **Integration**: Syncs with `useIDEStore`

## Data Flow

### File Operations Flow

```
1. User clicks file in FileExplorer
2. FileExplorer → onFileSelect(path)
3. useFileSystem → nativeHost.sendMessage({ command: 'READ_FILE', params: { path } })
4. Chrome Extension → forwards to Native Host
5. Native Host → reads file from disk
6. Response → Chrome Extension → Web App
7. useIDEStore → setActiveFile(path, content)
8. CodeEditor → displays content with syntax highlighting
```

### Terminal Command Flow

```
1. User types command in Terminal
2. Terminal → useTerminal hook
3. useTerminal → nativeHost.sendMessage({ command: 'EXECUTE_COMMAND', params: { command, cwd } })
4. Native Host → executes command via subprocess
5. stdout/stderr → streamed back to extension
6. Extension → forwards to Terminal component
7. XTerm.js → displays output
```

### File Watching Flow

```
1. IDE opens file → registers watch
2. useFileSystem → nativeHost.sendMessage({ command: 'WATCH_FILE', params: { path } })
3. Native Host → sets up file watcher (chokidar)
4. File changes externally → Native Host sends notification
5. Extension → forwards FILE_CHANGED message
6. useFileSystem → updates file content
7. CodeEditor → prompts user to reload if file has unsaved changes
```

## Native Host Integration

### useNativeHost Hook

```typescript
// hooks/useNativeHost.ts
import { useEffect, useState } from 'react';

interface NativeMessage {
  command: string;
  params: Record<string, any>;
}

interface NativeResponse {
  success: boolean;
  data?: any;
  error?: string;
}

export function useNativeHost() {
  const [connected, setConnected] = useState(false);

  const sendMessage = async (message: NativeMessage): Promise<NativeResponse> => {
    return new Promise((resolve, reject) => {
      // Send message via Chrome Extension
      chrome.runtime.sendMessage(
        { type: 'NATIVE_MESSAGE', payload: message },
        (response) => {
          if (response.success) {
            resolve(response);
          } else {
            reject(new Error(response.error));
          }
        }
      );
    });
  };

  const readFile = async (path: string): Promise<string> => {
    const response = await sendMessage({
      command: 'READ_FILE',
      params: { path }
    });
    return response.data.content;
  };

  const writeFile = async (path: string, content: string): Promise<void> => {
    await sendMessage({
      command: 'WRITE_FILE',
      params: { path, content }
    });
  };

  const listDirectory = async (path: string): Promise<FileEntry[]> => {
    const response = await sendMessage({
      command: 'LIST_DIRECTORY',
      params: { path }
    });
    return response.data.entries;
  };

  const executeCommand = async (command: string, cwd: string): Promise<string> => {
    const response = await sendMessage({
      command: 'EXECUTE_COMMAND',
      params: { command, cwd }
    });
    return response.data.output;
  };

  return {
    connected,
    readFile,
    writeFile,
    listDirectory,
    executeCommand
  };
}
```

## Key Features Implementation

### Feature 1: File Browsing and Editing

**Implementation:**
- Component: `FileExplorer` + `CodeEditor`
- Logic: Native host provides file system access, Monaco provides editing
- Dependencies: `@monaco-editor/react`, `useNativeHost` hook

**Code Example:**
```typescript
// components/CodeEditor/CodeEditor.tsx
'use client';

import { Editor } from '@monaco-editor/react';
import { useEffect, useState } from 'react';
import { useNativeHost } from '@/hooks/useNativeHost';

interface CodeEditorProps {
  filePath: string;
}

export function CodeEditor({ filePath }: CodeEditorProps) {
  const [content, setContent] = useState('');
  const [language, setLanguage] = useState('plaintext');
  const { readFile, writeFile } = useNativeHost();

  useEffect(() => {
    if (filePath) {
      readFile(filePath).then(setContent);
      setLanguage(detectLanguage(filePath));
    }
  }, [filePath]);

  const handleChange = (value: string | undefined) => {
    if (value !== undefined) {
      setContent(value);
      // Auto-save or mark dirty
    }
  };

  const handleSave = async () => {
    await writeFile(filePath, content);
  };

  return (
    <Editor
      height="100%"
      language={language}
      value={content}
      onChange={handleChange}
      theme="vs-dark"
      options={{
        minimap: { enabled: true },
        fontSize: 14,
        wordWrap: 'on'
      }}
    />
  );
}
```

### Feature 2: Integrated Terminal

**Implementation:**
- Component: `Terminal`
- Logic: XTerm.js for UI, native host executes commands
- Dependencies: `@xterm/xterm`, `useNativeHost`

**Code Example:**
```typescript
// components/Terminal/Terminal.tsx
'use client';

import { useEffect, useRef } from 'react';
import { Terminal as XTerm } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import { useNativeHost } from '@/hooks/useNativeHost';

export function Terminal({ sessionId, cwd }: TerminalProps) {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<XTerm | null>(null);
  const { executeCommand } = useNativeHost();

  useEffect(() => {
    if (!terminalRef.current) return;

    const xterm = new XTerm({
      cursorBlink: true,
      fontSize: 14,
      fontFamily: 'Consolas, monospace'
    });

    const fitAddon = new FitAddon();
    xterm.loadAddon(fitAddon);
    xterm.open(terminalRef.current);
    fitAddon.fit();

    let currentLine = '';

    xterm.onData((data) => {
      if (data === '\r') {
        // Enter pressed - execute command
        xterm.write('\r\n');
        executeCommand(currentLine, cwd).then((output) => {
          xterm.write(output);
          xterm.write('\r\n$ ');
        });
        currentLine = '';
      } else if (data === '\u007F') {
        // Backspace
        if (currentLine.length > 0) {
          currentLine = currentLine.slice(0, -1);
          xterm.write('\b \b');
        }
      } else {
        currentLine += data;
        xterm.write(data);
      }
    });

    xtermRef.current = xterm;

    return () => {
      xterm.dispose();
    };
  }, [sessionId]);

  return <div ref={terminalRef} className="w-full h-full" />;
}
```

### Feature 3: Git Integration

**Implementation:**
- Component: `GitPanel`
- Logic: Execute git commands via native host, parse output
- Dependencies: `useGit` hook

## Styling Approach

- **Framework**: Tailwind CSS for layout, custom CSS for IDE themes
- **Theme System**: VS Code Dark/Light themes
- **Layout**: CSS Grid for IDE panels (explorer, editor, terminal, sidebar)

## Performance Considerations

- **Monaco Editor**: Lazy load language support, virtualize large files
- **File Tree**: Virtualize large directories (react-window)
- **Terminal**: Limit scrollback buffer, clear old output
- **File Watching**: Debounce file change notifications

## Testing

### Unit Tests
```bash
cd collider-frontend
npx nx test ide
```

### Test Structure
- Component tests: `components/**/__tests__/*.test.tsx`
- Hook tests: `hooks/__tests__/*.test.ts`
- Integration tests: Test native host communication flows

## Known Issues / Technical Debt

- Large file editing (>10MB) causes performance issues
- Git operations block UI (should be async with loading states)
- Terminal doesn't support full PTY (no interactive programs like vim)
- File watcher can miss rapid changes

## Special Considerations

### Browser Compatibility
- Chrome/Edge only (Native Messaging API)
- Requires Chrome Extension installed
- Native host must be installed on user's system

### Security
- Native host runs with user's file system permissions
- Sandboxed to user-selected project directories
- Terminal commands validated (no shell injection)
- File paths sanitized

### Accessibility
- Keyboard shortcuts for all IDE actions
- Screen reader support for file tree
- High contrast themes available

## Related Code

- **Chrome Extension**: `FFS2_ColliderBackends/ColliderMultiAgentsChromeExtension/`
- **Native Host**: `FFS2_ColliderBackends/ColliderMultiAgentsChromeExtension/native-host/`
- **Shared UI**: `libs/shared-ui/`
- **API Client**: `libs/api-client/`

## Development Workflow

1. **Adding a new editor feature**:
   ```bash
   # Create component
   # Update useEditor hook
   # Add Monaco configuration
   # Write tests
   ```

2. **Debugging Native Host**:
   - Check Chrome Extension logs: `chrome://extensions` → Details → Inspect views: service worker
   - Native Host logs: OS-specific (Windows: Event Viewer, macOS/Linux: console)
   - Test native messaging: `chrome.runtime.connectNative()`

3. **Building for production**:
   ```bash
   npx nx build ide
   # Output in dist/apps/ide
   ```