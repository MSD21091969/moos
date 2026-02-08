# Codebase: FFS4 Sidepanel Appnode Browser

> Chrome Extension Sidepanel UI built with React + Plasmo framework for container tree navigation

## Overview

The Sidepanel is a persistent browser UI that provides always-available access to the Collider container tree. Built as part of the Chrome Extension using the Plasmo framework, it leverages Chrome's Side Panel API to stay visible alongside web pages. The component architecture emphasizes real-time updates and smooth tree interactions.

## Directory Structure

```
FFS2_ColliderBackends_MultiAgentChromeExtension/ColliderMultiAgentsChromeExtension/
├── sidepanel.tsx                  # Main sidepanel entry point
├── src/
│   ├── components/
│   │   ├── sidepanel/
│   │   │   ├── AppnodeTree.tsx        # Tree view component
│   │   │   ├── ContainerCard.tsx      # Individual container UI
│   │   │   ├── QuickActionsToolbar.tsx
│   │   │   └── SearchBar.tsx
│   ├── hooks/
│   │   ├── useSidepanel.ts            # Sidepanel-specific hook
│   │   ├── useContainerTree.ts        # Tree data management
│   │   └── useExtensionMessaging.ts   # Chrome messaging
│   ├── stores/
│   │   ├── sidepanelStore.ts          # Zustand store for UI state
│   │   ├── extensionStore.ts          # Shared extension state
│   ├── types/
│   │   └── sidepanel.ts               # TypeScript interfaces
│   └── services/
│       └── api.ts                     # Backend API client calls
```

## Component Architecture

### Core Components

**AppnodeTree** (`src/components/sidepanel/AppnodeTree.tsx`)
- **Purpose**: Renders hierarchical tree of containers
- **Props**:
  - `containers: Container[]` - Tree data
  - `selectedId: string | null` - Currently selected node
  - `onSelect: (id: string) => void` - Selection handler
- **State**: Expanded nodes, hover state
- **Dependencies**: ContainerCard (child nodes)
- **Integration**: Fetches from ColliderDataServer `/api/containers`

**ContainerCard** (`src/components/sidepanel/ContainerCard.tsx`)
- **Purpose**: Display individual container with metadata and actions
- **Props**:
  - `container: Container` - Container data
  - `depth: number` - Tree depth for indentation
  - `isSelected: boolean` - Selection state
  - `onSelect: () => void` - Click handler
  - `onExpand: () => void` - Expand/collapse handler
- **State**: Context menu open/closed
- **Dependencies**: QuickActionsButton component
- **Integration**: Emits Chrome messages on actions

**QuickActionsToolbar** (`src/components/sidepanel/QuickActionsToolbar.tsx`)
- **Purpose**: Toolbar with common operations
- **Props**: None (uses global state)
- **State**: None (stateless)
- **Dependencies**: Icon components
- **Integration**: Triggers API calls and Chrome messages

**SearchBar** (`src/components/sidepanel/SearchBar.tsx`)
- **Purpose**: Filter containers by name/tags
- **Props**:
  - `onSearch: (query: string) => void`
- **State**: Input value, debounced query
- **Dependencies**: None
- **Integration**: Filters tree data client-side

### Shared Components

Uses these from Chrome Extension shared components:
- `<Icon>` - Consistent iconography
- `<Button>` - Standard button component
- `<Tooltip>` - Hover tooltips

## Data Flow

### State Management

```
1. Sidepanel mounts → Sends SIDEPANEL_READY message
2. Background service responds with initial container tree
3. Tree data stored in sidepanelStore (Zustand)
4. User interacts → Updates local UI state immediately
5. Action triggers API call → Updates backend
6. Backend broadcasts change → Extension receives update
7. Extension sends CONTAINER_UPDATED → Sidepanel refreshes
```

### API Integration

Uses custom API client for backend calls:

```typescript
// src/services/api.ts
import { PLASMO_PUBLIC_API_BASE } from '~env';

const API_BASE = PLASMO_PUBLIC_API_BASE || 'http://localhost:8000';

export const api = {
  containers: {
    list: async () => {
      const res = await fetch(`${API_BASE}/api/containers`);
      return await res.json();
    },
    create: async (data) => {
      const res = await fetch(`${API_BASE}/api/containers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      return await res.json();
    },
    delete: async (id) => {
      await fetch(`${API_BASE}/api/containers/${id}`, {
        method: 'DELETE',
      });
    },
  },
};
```

**Key Endpoints:**
- `GET /api/containers` - Fetch full tree
- `POST /api/containers` - Create new container
- `DELETE /api/containers/:id` - Delete container
- `PATCH /api/containers/:id` - Update container metadata

### Chrome Extension Communication

**Messages Sent:**
```typescript
// Notify extension sidepanel is ready
chrome.runtime.sendMessage({
  type: 'SIDEPANEL_READY',
  payload: { timestamp: Date.now() }
});

// User selected a container
chrome.runtime.sendMessage({
  type: 'CONTAINER_SELECTED',
  payload: { containerId: 'container-123' }
});

// Request to open in PiP
chrome.runtime.sendMessage({
  type: 'OPEN_IN_PIP',
  payload: { containerId: 'container-123' }
});
```

**Messages Received:**
```typescript
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'CONTAINER_UPDATED') {
    // Refresh tree data
    refreshContainerTree();
  }

  if (message.type === 'SYNC_STATE') {
    // Sync state from background
    useSidepanelStore.getState().syncState(message.payload);
  }

  sendResponse({ success: true });
});
```

## Key Features Implementation

### Feature 1: Appnode Browser

**Implementation:**
- Component: `src/components/sidepanel/AppnodeTree.tsx`
- Logic: Recursive tree rendering with virtualization for performance
- Dependencies: React, Zustand

**Code Example:**
```typescript
export function AppnodeTree({ containers, selectedId, onSelect }: AppnodeTreeProps) {
  const expandedNodes = useSidepanelStore(state => state.expandedNodes);
  const toggleExpand = useSidepanelStore(state => state.toggleExpand);

  return (
    <div className="tree-view">
      {containers.map(container => (
        <ContainerCard
          key={container.id}
          container={container}
          depth={0}
          isSelected={selectedId === container.id}
          isExpanded={expandedNodes.has(container.id)}
          onSelect={() => onSelect(container.id)}
          onExpand={() => toggleExpand(container.id)}
        />
      ))}
    </div>
  );
}
```

### Feature 2: Container Tree Visualization

**Implementation:**
- Component: `src/components/sidepanel/ContainerCard.tsx`
- Logic: Recursive rendering with depth-based indentation
- Dependencies: CSS-in-JS for dynamic styling

**Code Example:**
```typescript
export function ContainerCard({
  container,
  depth,
  isSelected,
  isExpanded,
  onSelect,
  onExpand
}: ContainerCardProps) {
  return (
    <div
      className={`container-card depth-${depth} ${isSelected ? 'selected' : ''}`}
      onClick={onSelect}
    >
      <span onClick={onExpand}>{isExpanded ? '▼' : '▶'}</span>
      <span>{container.name}</span>
      {isExpanded && container.children && (
        <div className="children">
          {container.children.map(child => (
            <ContainerCard
              key={child.id}
              container={child}
              depth={depth + 1}
              {...props}
            />
          ))}
        </div>
      )}
    </div>
  );
}
```

### Feature 3: Quick Actions

**Implementation:**
- Component: `src/components/sidepanel/QuickActionsToolbar.tsx`
- Logic: Action buttons trigger API calls and Chrome messages
- Dependencies: API client, Chrome messaging

## Styling Approach

- **Framework**: Tailwind CSS + CSS Modules for component-specific styles
- **Theme System**: Inherits from Chrome Extension theme (light/dark mode)
- **Responsive Design**: Fixed width (320px sidepanel), responsive height

## Performance Considerations

- **Virtualization**: Large trees use virtual scrolling (react-window)
- **Lazy Loading**: Child nodes loaded on expand
- **Memoization**: Tree nodes memoized with React.memo()
- **Debounced Search**: 300ms debounce on search input

## Testing

### Unit Tests
```bash
cd ColliderMultiAgentsChromeExtension
pnpm test sidepanel
```

### Test Structure
- Component tests: `src/components/sidepanel/__tests__/*.test.tsx`
- Hook tests: `src/hooks/__tests__/*.test.ts`
- Integration tests: Test Chrome messaging flows

## Known Issues / Technical Debt

- Tree virtualization not yet implemented (performance issue with 1000+ nodes)
- Search only works on currently loaded nodes (should search backend)
- Drag-and-drop to reorganize tree not yet implemented

## Special Considerations

### Browser Compatibility
- Chrome 114+ required (Side Panel API)
- Not compatible with Firefox/Safari

### Security
- Uses Chrome Extension content security policy
- API calls authenticated via extension ID
- No sensitive data stored in sidepanel (uses Chrome Storage)

### Accessibility
- Keyboard navigation support (arrow keys, enter, space)
- ARIA labels on tree nodes
- Screen reader announcements for tree updates

## Related Code

- **Chrome Extension Background**: `background.ts` (handles messaging)
- **Shared Components**: `src/components/shared/`
- **Backend API**: `../../../FFS2_ColliderBackends/ColliderDataServer/`

## Development Workflow

1. **Adding a new feature**:
   ```bash
   # Create component in src/components/sidepanel/
   # Add types to src/types/sidepanel.ts
   # Wire up Chrome messaging if needed
   # Write tests
   ```

2. **Debugging**:
   - Chrome DevTools (right-click sidepanel → Inspect)
   - Console logging (use `console.log` in dev, remove in production)
   - Chrome Extension debugging tools

3. **Building for production**:
   ```bash
   cd ColliderMultiAgentsChromeExtension
   pnpm build
   # Output in build/ directory
   ```
