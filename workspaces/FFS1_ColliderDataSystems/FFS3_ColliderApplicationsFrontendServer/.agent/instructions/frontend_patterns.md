# Frontend Patterns

> Patterns for FFS3 Nx monorepo: Vite + React 19 default, Next.js optional.

## Monorepo Structure Pattern

```
apps/ffs4/src/app/    ← Each app has its own app/ with root component
apps/ffs5/src/app/
apps/ffs6/src/app/
libs/shared-ui/src/   ← Shared components imported via @collider/shared-ui
```

### Import Pattern (Workspace Protocol)

```typescript
// From any app, import shared library
import { Button, NodeGraph } from '@collider/shared-ui';

// Within an app, use relative imports
import { AppTree } from './components/AppTree';
```

---

## Component Patterns

### Functional Components (React 19)

```tsx
interface NodeCardProps {
  node: AppNode;
  isSelected: boolean;
  onSelect: (nodeId: string) => void;
}

export function NodeCard({ node, isSelected, onSelect }: NodeCardProps) {
  return (
    <div
      className={`node-card ${isSelected ? 'selected' : ''}`}
      onClick={() => onSelect(node.id)}
    >
      <h3>{node.path}</h3>
      <span className="domain-badge">{node.metadata?.domain}</span>
    </div>
  );
}
```

### Component File Organization

```
src/
├── app/
│   ├── app.tsx           ← Root component + router
│   └── app.module.css
├── components/
│   ├── NodeCard/
│   │   ├── NodeCard.tsx
│   │   ├── NodeCard.module.css
│   │   └── NodeCard.spec.tsx
│   └── AppTree/
│       └── ...
├── hooks/
│   ├── useNodes.ts
│   └── useWebSocket.ts
├── stores/
│   └── appStore.ts       ← Zustand store
├── types/
│   └── index.ts
└── main.tsx              ← Entry point
```

---

## Routing (React Router DOM)

Default routing for Vite apps:

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Suspense, lazy } from 'react';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const Workspace = lazy(() => import('./pages/Workspace'));

export function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<div>Loading...</div>}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/workspace/:nodeId" element={<Workspace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
```

### Code Splitting

Use `React.lazy()` for route-level splitting:

```tsx
const AdminPanel = lazy(() => import('./pages/AdminPanel'));
```

> **Next.js apps**: If using `@nx/next`, use the App Router with `next/dynamic` instead of `React.lazy()`.

---

## State Management (Zustand)

```typescript
import { create } from 'zustand';

interface AppState {
  applications: Application[];
  selectedAppId: string | null;
  tree: AppNodeTree[];
  selectedNodePath: string | null;
  loading: boolean;
  error: string | null;

  setApplications: (apps: Application[]) => void;
  selectApp: (appId: string) => void;
  setTree: (tree: AppNodeTree[]) => void;
  selectNode: (path: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  applications: [],
  selectedAppId: null,
  tree: [],
  selectedNodePath: null,
  loading: false,
  error: null,

  setApplications: (apps) => set({ applications: apps }),
  selectApp: (appId) => set({ selectedAppId: appId }),
  setTree: (tree) => set({ tree }),
  selectNode: (path) => set({ selectedNodePath: path }),
}));
```

---

## Data Fetching

### Client-Side (Default)

```typescript
async function fetchNodes(appId: string): Promise<AppNodeTree[]> {
  const response = await fetch(
    `${import.meta.env.VITE_API_BASE}/api/v1/nodes?app_id=${appId}`,
  );
  if (!response.ok)
    throw new Error(`Failed to fetch nodes: ${response.statusText}`);
  return response.json();
}
```

### Custom Hook Pattern

```typescript
import { useState, useEffect } from 'react';

export function useNodes(appId: string | null) {
  const [nodes, setNodes] = useState<AppNodeTree[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!appId) return;
    setLoading(true);
    fetchNodes(appId)
      .then(setNodes)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [appId]);

  return { nodes, loading, error };
}
```

---

## XYFlow Graph Patterns

### Basic Graph Component

```tsx
import { ReactFlow, Background, Controls, MiniMap } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { WorkspaceNode } from './nodes/WorkspaceNode';

const nodeTypes = {
  workspace: WorkspaceNode,
};

export function NodeGraph({ nodes, edges }: NodeGraphProps) {
  return (
    <div style={{ width: '100%', height: '600px' }}>
      <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView>
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
}
```

### Custom Node Type

```tsx
import { Handle, Position, type NodeProps } from '@xyflow/react';

interface WorkspaceNodeData {
  label: string;
  domain: string;
  path: string;
}

export function WorkspaceNode({ data }: NodeProps<WorkspaceNodeData>) {
  const domainColor = getDomainColor(data.domain);

  return (
    <div className="workspace-node" style={{ borderColor: domainColor }}>
      <Handle type="target" position={Position.Top} />
      <div className="node-header" style={{ backgroundColor: domainColor }}>
        {data.domain}
      </div>
      <div className="node-body">
        <strong>{data.label}</strong>
        <code>{data.path}</code>
      </div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

function getDomainColor(domain: string): string {
  const colors: Record<string, string> = {
    FILESYST: '#4caf50',
    CLOUD: '#2196f3',
    ADMIN: '#ff9800',
  };
  return colors[domain] || '#9e9e9e';
}
```

---

## Testing (Vitest)

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { NodeCard } from './NodeCard';

describe('NodeCard', () => {
  it('renders node path', () => {
    const node = { id: '1', path: 'root/research', metadata: {} };
    render(<NodeCard node={node} isSelected={false} onSelect={vi.fn()} />);
    expect(screen.getByText('root/research')).toBeInTheDocument();
  });

  it('applies selected class', () => {
    const node = { id: '1', path: 'root', metadata: {} };
    const { container } = render(
      <NodeCard node={node} isSelected={true} onSelect={vi.fn()} />
    );
    expect(container.firstChild).toHaveClass('selected');
  });
});
```

### Run Tests

```bash
nx test ffs6           # Test specific app
nx test shared-ui      # Test shared library
nx run-many -t test    # Test all
```

---

## CSS Patterns

### CSS Modules (Default)

```tsx
import styles from './NodeCard.module.css';

export function NodeCard({ node }: NodeCardProps) {
  return <div className={styles.card}>{node.path}</div>;
}
```

### Global Styles

Each app has a `src/styles.css` for global styles and CSS custom properties:

```css
:root {
  --color-filesyst: #4caf50;
  --color-cloud: #2196f3;
  --color-admin: #ff9800;
  --border-radius: 8px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
}
```
