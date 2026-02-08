# Frontend Standards & Rules

> Enforced standards for FFS3 ColliderFrontend development

## Code Quality Standards

### TypeScript Configuration

**REQUIRED:**
- ✅ Strict mode enabled in `tsconfig.json`
- ✅ No implicit `any` types
- ✅ All props interfaces exported
- ✅ Return types on functions (except simple React components)

**FORBIDDEN:**
- ❌ Using `any` type (use `unknown` if type is truly unknown)
- ❌ `@ts-ignore` or `@ts-expect-error` without explanation comment
- ❌ Empty interfaces extending other interfaces just to rename

```typescript
// ❌ BAD
function fetchData(): any {
  return fetch('/api/data');
}

// ✅ GOOD
async function fetchData(): Promise<ApiResponse> {
  return await fetch('/api/data');
}
```

### Component Standards

**REQUIRED:**
- ✅ Functional components only (no class components)
- ✅ Props interface defined for all components
- ✅ One component per file (except tightly related helpers)
- ✅ PascalCase for component names and filenames

**FORBIDDEN:**
- ❌ Default exports for components (use named exports)
- ❌ Props spreading without explicit typing
- ❌ Inline styles (use Tailwind CSS or CSS modules)

```typescript
// ❌ BAD
export default function component(props: any) {
  return <div style={{ color: 'red' }}>Content</div>;
}

// ✅ GOOD
interface ComponentProps {
  title: string;
  onClick?: () => void;
}

export function Component({ title, onClick }: ComponentProps) {
  return <div className="text-red-500">{title}</div>;
}
```

### File Organization Rules

**REQUIRED Structure:**
```
feature/
├── components/
│   ├── FeatureComponent.tsx
│   └── FeatureComponent.test.tsx
├── hooks/
│   ├── useFeature.ts
│   └── useFeature.test.ts
├── types.ts
├── utils.ts
└── index.ts (exports)
```

**Naming Conventions:**
- ✅ Components: `PascalCase.tsx` (e.g., `UserProfile.tsx`)
- ✅ Hooks: `camelCase.ts` with `use` prefix (e.g., `useAuth.ts`)
- ✅ Utils: `camelCase.ts` (e.g., `formatDate.ts`)
- ✅ Types: `PascalCase` interfaces/types (e.g., `UserProfile`)
- ✅ Constants: `SCREAMING_SNAKE_CASE` (e.g., `API_BASE_URL`)

**FORBIDDEN:**
- ❌ Generic names like `utils.ts` or `helpers.ts` at root
- ❌ Mixing UI components and business logic in same file
- ❌ Files over 300 lines (split into smaller modules)

## Next.js App Router Rules

### Server vs Client Components

**REQUIRED:**
- ✅ Use Server Components by default
- ✅ Add `'use client'` directive ONLY when needed:
  - Using React hooks (useState, useEffect, etc.)
  - Event handlers (onClick, onChange, etc.)
  - Browser APIs (localStorage, window, etc.)
  - Third-party libraries that require client-side

**FORBIDDEN:**
- ❌ Adding `'use client'` to every component by default
- ❌ Fetching data client-side when it can be done server-side
- ❌ Using server-only APIs in client components

```typescript
// ❌ BAD - Unnecessary client component
'use client';

export function StaticContent() {
  return <div>Static content</div>;
}

// ✅ GOOD - Server component (default)
export function StaticContent() {
  return <div>Static content</div>;
}

// ✅ GOOD - Client component when needed
'use client';

export function InteractiveButton() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

### Routing Rules

**REQUIRED:**
- ✅ Use App Router file conventions (page.tsx, layout.tsx, etc.)
- ✅ Place API routes in `app/api/` directory
- ✅ Use route groups `(group)` for organization without URL impact

**FORBIDDEN:**
- ❌ Mixing Pages Router (`pages/`) and App Router (`app/`)
- ❌ Direct file system navigation (use Next.js `Link` or `useRouter`)
- ❌ Hardcoded URLs (use constants or env variables)

## State Management Rules

### When to Use Each Pattern

**Local State (useState):**
- ✅ Component-specific UI state
- ✅ Form inputs
- ✅ Toggle states (open/closed, visible/hidden)

**Context API:**
- ✅ Feature-scoped state (3-10 related components)
- ✅ Theme/settings within a feature
- ✅ Non-frequently changing state

**Zustand:**
- ✅ Global application state
- ✅ User session/auth state
- ✅ Frequently accessed across many components

**Server State:**
- ✅ Data from APIs (prefer React Server Components or TanStack Query)

**FORBIDDEN:**
- ❌ Using Context for frequently changing state
- ❌ Prop drilling beyond 2-3 levels
- ❌ Storing server data in local state without caching strategy

```typescript
// ❌ BAD - Prop drilling
<A data={data}>
  <B data={data}>
    <C data={data}>
      <D data={data} />
    </C>
  </B>
</A>

// ✅ GOOD - Context for shared state
<DataProvider value={data}>
  <A><B><C><D /></C></B></A>
</DataProvider>
```

## Data Fetching Rules

### Server-Side Data Fetching

**REQUIRED:**
- ✅ Use Server Components for initial data loading
- ✅ Use `fetch` with Next.js caching options
- ✅ Handle errors with error.tsx boundary

**FORBIDDEN:**
- ❌ Client-side fetching for initial page data
- ❌ Ignoring cache configuration
- ❌ Not handling loading states

```typescript
// ✅ GOOD - Server component with proper caching
export default async function Page() {
  const data = await fetch('https://api.example.com/data', {
    next: { revalidate: 3600 } // Cache for 1 hour
  });

  return <div>{/* Render data */}</div>;
}
```

### Client-Side Data Fetching

**REQUIRED:**
- ✅ Use `@collider/api-client` for all API calls
- ✅ Handle loading, error, and success states
- ✅ Clean up in useEffect if needed

**FORBIDDEN:**
- ❌ Raw `fetch()` calls without error handling
- ❌ Not showing loading indicators
- ❌ Memory leaks (unmounted component updates)

```typescript
// ✅ GOOD - Proper client-side fetching
'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@collider/api-client';

export function DataComponent() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;

    apiClient.resource.get()
      .then(result => mounted && setData(result))
      .catch(err => mounted && setError(err))
      .finally(() => mounted && setLoading(false));

    return () => { mounted = false; };
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;
  return <div>{/* Render data */}</div>;
}
```

## Styling Rules

### Tailwind CSS Standards

**REQUIRED:**
- ✅ Use Tailwind utility classes
- ✅ Use `className` prop (not `style`)
- ✅ Extract repeated patterns to components or `@apply` directives

**FORBIDDEN:**
- ❌ Inline styles with `style` prop (except dynamic values)
- ❌ !important in custom CSS
- ❌ Arbitrary values when Tailwind class exists

```typescript
// ❌ BAD
<div style={{ padding: '16px', backgroundColor: '#f0f0f0' }}>Content</div>

// ✅ GOOD
<div className="p-4 bg-gray-100">Content</div>

// ✅ GOOD - Dynamic values
<div
  className="p-4"
  style={{ backgroundColor: dynamicColor }}
>
  Content
</div>
```

### Component Styling

**REQUIRED:**
- ✅ Use components from `@collider/shared-ui` when available
- ✅ Create variants for reusable patterns
- ✅ Keep styling DRY (Don't Repeat Yourself)

**FORBIDDEN:**
- ❌ Duplicating component styles across files
- ❌ Creating one-off components that should be in shared-ui

## Error Handling Rules

### Error Boundaries

**REQUIRED:**
- ✅ Wrap major features in ErrorBoundary
- ✅ Provide fallback UI
- ✅ Log errors to monitoring service

**FORBIDDEN:**
- ❌ Silent failures (swallowed errors)
- ❌ Generic error messages without context
- ❌ Exposing stack traces to users in production

### Try-Catch Standards

**REQUIRED:**
```typescript
// ✅ GOOD
try {
  await apiClient.resource.create(data);
  toast.success('Created successfully');
} catch (error) {
  console.error('Failed to create resource:', error);
  toast.error('Failed to create. Please try again.');
  // Optionally: log to error tracking service
}
```

**FORBIDDEN:**
```typescript
// ❌ BAD
try {
  await apiClient.resource.create(data);
} catch (error) {
  // Silent failure - user has no feedback
}
```

## Performance Rules

### Bundle Size

**REQUIRED:**
- ✅ Lazy load large components with `dynamic()`
- ✅ Use Next.js Image component for images
- ✅ Import only what you need from libraries

**FORBIDDEN:**
- ❌ Importing entire libraries (e.g., `import _ from 'lodash'`)
- ❌ Bundling large files without code splitting
- ❌ Unoptimized images

```typescript
// ❌ BAD
import _ from 'lodash';
const result = _.debounce(fn, 300);

// ✅ GOOD
import debounce from 'lodash/debounce';
const result = debounce(fn, 300);
```

### React Optimization

**REQUIRED:**
- ✅ Use React.memo() for expensive components
- ✅ Use useMemo() for expensive calculations
- ✅ Use useCallback() for memoized callbacks

**FORBIDDEN:**
- ❌ Premature optimization (measure first!)
- ❌ Memoizing simple operations
- ❌ Creating new objects/arrays in render

```typescript
// ❌ BAD
function Component({ items }) {
  return items.map(item => /* render */); // Creates new array every render
}

// ✅ GOOD
function Component({ items }) {
  const processedItems = useMemo(() =>
    items.map(item => processItem(item)),
    [items]
  );
  return processedItems.map(item => /* render */);
}
```

## Testing Rules

### Test Coverage

**REQUIRED:**
- ✅ Write tests for all shared library components
- ✅ Test critical user flows (authentication, checkout, etc.)
- ✅ Test error states and edge cases

**FORBIDDEN:**
- ❌ Testing implementation details
- ❌ Tests that don't add value
- ❌ Skipping tests without reason

### Test Structure

**REQUIRED:**
```typescript
// ✅ GOOD
describe('ComponentName', () => {
  it('renders with default props', () => {
    // Arrange
    render(<ComponentName />);

    // Act
    const element = screen.getByText('Expected text');

    // Assert
    expect(element).toBeInTheDocument();
  });

  it('calls onClick when button is clicked', () => {
    const handleClick = jest.fn();
    render(<ComponentName onClick={handleClick} />);

    fireEvent.click(screen.getByRole('button'));

    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

## Security Rules

### Input Validation

**REQUIRED:**
- ✅ Validate all user input
- ✅ Sanitize HTML content before rendering
- ✅ Use parameterized queries (handled by backend)

**FORBIDDEN:**
- ❌ Trusting user input
- ❌ Using `dangerouslySetInnerHTML` without sanitization
- ❌ Storing passwords or sensitive data in localStorage

### Authentication

**REQUIRED:**
- ✅ Check auth status before rendering protected content
- ✅ Redirect unauthenticated users
- ✅ Clear auth tokens on logout

**FORBIDDEN:**
- ❌ Relying only on client-side auth checks
- ❌ Storing tokens in insecure storage
- ❌ Exposing API keys in client code

## Git & Version Control Rules

### Commit Standards

**REQUIRED:**
- ✅ Clear, descriptive commit messages
- ✅ One logical change per commit
- ✅ Run tests before committing

**Format:**
```
type(scope): description

feat(sidepanel): add container tree view
fix(api-client): handle network timeouts
docs(readme): update installation instructions
```

### Branch Naming

**REQUIRED:**
- `feature/description` - New features
- `fix/description` - Bug fixes
- `refactor/description` - Code refactoring
- `docs/description` - Documentation updates

**FORBIDDEN:**
- ❌ Working directly on main branch
- ❌ Generic branch names like `updates` or `fixes`
- ❌ Long-lived feature branches (merge frequently)

## Code Review Checklist

Before requesting review:
- [ ] Code follows TypeScript standards
- [ ] Components are properly typed
- [ ] Error handling implemented
- [ ] Loading states handled
- [ ] Tests written and passing
- [ ] No console.log in production code
- [ ] Code formatted with Prettier
- [ ] ESLint passing with no warnings
- [ ] No hardcoded values (use constants/env)
- [ ] Branch updated with latest main

## Enforcement

These rules are enforced through:
1. **ESLint** - Automated linting
2. **TypeScript compiler** - Type checking
3. **Prettier** - Code formatting
4. **Pre-commit hooks** - Run checks before commit
5. **CI/CD pipeline** - Automated testing
6. **Code reviews** - Human verification

## Related Documentation

- [Frontend Patterns](./frontend_patterns.md)
- [FFS1 Code Quality Rules](../../.agent/rules/code_quality.md)
- [FFS1 Stack Standards](../../.agent/rules/stack_standards.md)
