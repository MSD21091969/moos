---
description: Frontend development patterns for React, Vite, and ReactFlow
applyTo: "frontend/**"
---

# Frontend Instructions

## Architecture
- **Framework:** React + Vite
- **State Management:** Zustand (`useWorkspaceStore`)
  - **Persist Middleware:** Saves state to `workspace-storage` in localStorage.
  - **Selectors:** Use granular selectors to avoid unnecessary re-renders.
- **Canvas:** ReactFlow 12
  - **Nodes:** `CustomNode` (wraps `ContainerVisualState`)
  - **Edges:** `CustomEdge` (represents `ResourceLink.input_mappings`)
  - **Viewport:** Managed via `useReactFlow` and `useWorkspaceStore`.

## Terminology Mapping
| User UX | Code Component |
|---|---|
| **Sticky Note** | `ContainerVisualState` (type='session') |
| **Agent Card** | `ContainerVisualState` (type='agent') |
| **Tool Card** | `ContainerVisualState` (type='tool') |
| **Data Source** | `ContainerVisualState` (type='source') |

## Critical Workflows
### 1. Sync API Types
When backend API changes, regenerate TypeScript types:
```powershell
npm run types:sync
```

### 2. Mode Detection (CRITICAL)
- **Do not** compare `import.meta.env.VITE_MODE` directly in feature logic.
- Always use `isDemoMode()` (from `frontend/src/lib/env.ts`) to avoid mode drift (e.g. whitespace in `.env`, inconsistent defaults), which can cause Demo Mode to accidentally hit the real backend.

### 3. Bridge Communication
- **Dev/Demo Mode:** Use `window.__colliderBridge` to communicate with MCP or external tools.
- **Events:** Listen for `browser_console_messages` for debugging.

## Best Practices (React)
### Good Patterns
- **Top-Level Components:** Define components at the top level, never nested inside others.
- **Derived State:** Calculate values during render (e.g., `const filtered = items.filter(...)`) instead of syncing state with `useEffect`.
- **Zustand Selectors:** Select only what you need: `const user = useStore(s => s.user)`.
- **Strict Mode:** Ensure components are resilient to double-mounting in development.
- **Playwright Locators:** Use `data-testid` attributes for stable testing selectors.

### Bad Patterns
- **Mutating State:** Never mutate state directly (e.g., `state.value = 1`). Use setters.
- **Missing Dependencies:** Lying to `useEffect` or `useCallback` dependency arrays.
- **Props Drilling:** Pass data through too many layers; use Context or Zustand instead.
- **Fragile Selectors:** Avoid testing with CSS classes (e.g., `.btn-primary`); use `getByRole` or `getByTestId`.

## Best Practices (ReactFlow)
- **Memoization:** Wrap custom nodes in `memo` to prevent re-renders on canvas pan/zoom.
- **Handles:** Ensure `Handle` IDs are unique per node.
- **Viewport:** Use `useReactFlow().setViewport` for programmatic navigation, not direct state manipulation.

## Non-Trivial Invariants (UOM Rendering)
- **Cycle-safe derived state:** any tree-walk (depth, counts, ancestry) must guard against cycles (use a `visited` set or iterative traversal). Unbounded recursion can crash the workspace view.
- **ID semantics:** distinguish `instance_id` (container identity) from `link_id` (ResourceLink identity). Use the correct identifier for mutations/sync to avoid “resource not found after update” style failures.

## Unified Grid Model (Link-Centric UI)
The grid renders **ResourceLinks**, not containers directly.

### Core Principle
```
Grid = f(ResourceLinks)    // What's on screen
Menus = f(Rules)           // What actions are available
```

### Library Pattern (Orphans)
- **Library:** Containers with `parent_id === null` (orphans)
- **SSE Sync:** Container events update `containerRegistry` but don't render Library continuously
- **Menu Read:** "Add Existing" reads from registry on-demand when menu opens

```typescript
// Compute orphans from containerRegistry
const orphanContainers = useMemo(() => {
  return Object.values(containerRegistry)
    .filter(entry => entry.container?.parent_id === null)
    .map(entry => entry.container)
    .filter(Boolean);
}, [containerRegistry]);

// Filter by type for picker modal
const getOrphansByType = (type: 'agent' | 'tool' | 'source') => {
  return orphanContainers.filter(c => c?.instance_id?.startsWith(type));
};
```

### SSE Sync Modes
| Data Type | Action |
|-----------|--------|
| Visual (position, color) | Immediate render update |
| Library (parent_id change) | Registry update only, read on menu open |
