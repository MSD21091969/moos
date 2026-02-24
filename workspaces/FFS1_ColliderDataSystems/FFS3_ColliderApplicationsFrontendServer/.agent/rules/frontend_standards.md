---
description: Coding standards for FFS3 Nx monorepo — TypeScript strict, React
19, Vite, React Router, Zustand, XYFlow, CSS Modules, Vitest activation: always
---

# Frontend Standards

> Coding standards for FFS3 Nx monorepo: Vite + React 19.

---

## TypeScript Standards

- **Strict mode**: `"strict": true` in all `tsconfig.json`
- **No `any`**: Use `unknown` + type guards instead
- **Interfaces over types**: Prefer `interface` for object shapes, `type` for unions/intersections
- **Explicit return types**: Required on exported functions
- **Barrel exports**: Each library exposes a single `index.ts`

---

## Component Standards

- **Functional only**: No class components
- **Named exports**: `export function Component()` (no default exports for components)
- **Props interface**: Every component has a typed props interface named `{Component}Props`
- **Co-located files**: Component, styles, tests in same directory
- **Max 200 lines**: Split components exceeding this threshold

---

## File Organization

```text
src/
├── app/              ← Root component + router setup
├── components/       ← Reusable UI components
├── hooks/            ← Custom React hooks
├── stores/           ← Zustand stores
├── types/            ← TypeScript interfaces
├── utils/            ← Pure utility functions
├── pages/            ← Route-level page components
└── main.tsx          ← Entry point (DO NOT add logic here)
```

### Naming

- **Components**: PascalCase (`NodeCard.tsx`)
- **Hooks**: camelCase with `use` prefix (`useNodes.ts`)
- **Stores**: camelCase with `Store` suffix (`appStore.ts`)
- **Utils**: camelCase (`formatPath.ts`)
- **Tests**: Same name + `.spec.tsx` suffix

---

## Routing Rules

### Vite Apps (Default)

- Use **React Router DOM** (`react-router-dom`)
- Define routes in `app/app.tsx`
- Use `React.lazy()` for route-level code splitting
- Prefer `<Outlet />` for nested layouts

---

## State Management

- **Zustand** for app-level state (applications, tree, selection)
- **React state** for component-local UI state
- **No prop drilling** beyond 2 levels — use Zustand or context
- **Immutable updates**: Always return new state objects

---

## Data Fetching

- Use `fetch()` with `import.meta.env.VITE_API_BASE` for API calls
- Custom hooks for data fetching (`useNodes`, `useApplications`)
- Handle loading/error states in every data hook
- No direct API calls in components — always through hooks or stores

---

## XYFlow Standards

- Custom node types must implement `Handle` for connections
- Use shared design tokens for domain colors (no hardcoded hex values)
- Node data interfaces extend a `BaseNodeData` type
- Graph state managed via Zustand, not local state
- Always include `<Background />`, `<Controls />`, `<MiniMap />`

---

## Styling

- **CSS Modules** for component-scoped styles (`.module.css`)
- **CSS custom properties** for design tokens (colors, spacing)
- **No inline styles** except dynamic values (e.g., `style={{ borderColor }}`)
- **Mobile-first**: Use `min-width` media queries
- Domain colors defined as CSS custom properties in `:root`

---

## Testing

- **Framework**: Vitest + React Testing Library
- **Mocks**: `vi.fn()`, `vi.mock()` (NOT `jest.fn()`)
- **Co-located**: Tests next to source files (`.spec.tsx`)
- **Coverage**: Components must have render and interaction tests
- **No snapshot tests**: Use explicit assertions

---

## Performance

- `React.lazy()` for route-level code splitting
- `React.memo()` for expensive pure components
- `useMemo` / `useCallback` only when profiling shows need
- Avoid re-renders: use Zustand selectors (`useStore(selector)`)
- Images: Use standard `<img>` tags with lazy loading (`loading="lazy"`)

---

## Error Handling

- Error boundaries at route level
- API errors: catch, log, display user-friendly message
- Never swallow errors silently
- Use `ErrorBoundary` component wrapping each route

---

## Security

- No secrets in frontend code
- Use `import.meta.env.VITE_*` for public config only
- Sanitize user input before rendering
- Auth tokens stored in extension context, not localStorage

---

## Git Rules

- Feature branches: `feat/ffs6-node-viewer`
- Conventional commits: `feat(ffs6):`, `fix(shared-ui):`, `refactor(ffs4):`
- One logical change per commit
- Run `nx lint` and `nx test` before pushing
