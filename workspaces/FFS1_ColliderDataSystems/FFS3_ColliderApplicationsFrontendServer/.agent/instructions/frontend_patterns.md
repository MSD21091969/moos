# Frontend Development Patterns

> Nx + Next.js monorepo patterns and best practices for FFS3 ColliderFrontend

## Nx Monorepo Structure

### Organization

```
collider-frontend/
├── apps/
│   ├── portal/                    # Main Next.js application
│   └── portal-e2e/                # E2E tests
├── libs/
│   ├── api-client/                # @collider/api-client
│   ├── shared-ui/                 # @collider/shared-ui
│   └── node-container/            # @collider/node-container
├── nx.json                        # Nx workspace configuration
├── tsconfig.base.json             # Shared TypeScript config
└── package.json                   # Monorepo dependencies
```

### Path Aliases

Use TypeScript path aliases defined in `tsconfig.base.json`:

```typescript
// Instead of relative imports:
import { Button } from '../../../libs/shared-ui/src/components/Button';

// Use path alias:
import { Button } from '@collider/shared-ui';
```

## Next.js App Router Patterns

### File-Based Routing

```
apps/portal/app/
├── layout.tsx                     # Root layout (wraps all pages)
├── page.tsx                       # Homepage (/)
├── [route]/
│   ├── layout.tsx                 # Route-specific layout
│   ├── page.tsx                   # Route page
│   ├── loading.tsx                # Loading UI
│   └── error.tsx                  # Error handling
└── api/
    └── [endpoint]/
        └── route.ts               # API route handler
```

### Layout Pattern

```typescript
// app/layout.tsx
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
```

### Page Pattern

```typescript
// app/[route]/page.tsx
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Page Title',
  description: 'Page description',
};

export default async function PageName() {
  // Server-side data fetching
  const data = await fetchData();

  return (
    <main>
      <ClientComponent data={data} />
    </main>
  );
}
```

### Client Components

```typescript
// Mark components that need interactivity
'use client';

import { useState } from 'react';

export function InteractiveComponent() {
  const [state, setState] = useState();

  return (
    // Component JSX
  );
}
```

## Shared Libraries Pattern

### Creating a New Library

```bash
cd collider-frontend
npx nx g @nx/react:library my-lib
```

### Exporting from Libraries

```typescript
// libs/shared-ui/src/index.ts
export { Button } from './components/Button';
export { Card } from './components/Card';
export type { ButtonProps, CardProps } from './types';
```

### Using Shared Libraries

```typescript
// In any app or lib
import { Button, Card } from '@collider/shared-ui';
import { apiClient } from '@collider/api-client';
import { NodeContainer } from '@collider/node-container';
```

## Component Patterns

### Server Components (Default)

```typescript
// No 'use client' directive = server component
export async function DataComponent() {
  const data = await fetch('https://api.example.com/data');

  return <div>{/* Render data */}</div>;
}
```

### Client Components

```typescript
'use client';

import { useState, useEffect } from 'react';

export function ClientComponent() {
  const [data, setData] = useState(null);

  useEffect(() => {
    // Client-side logic
  }, []);

  return <div>{/* Interactive UI */}</div>;
}
```

### Hybrid Pattern (Server + Client)

```typescript
// ServerWrapper.tsx (server component)
import { ClientComponent } from './ClientComponent';

export async function ServerWrapper() {
  const serverData = await fetchServerData();

  return (
    <ClientComponent initialData={serverData} />
  );
}

// ClientComponent.tsx
'use client';

export function ClientComponent({ initialData }) {
  const [data, setData] = useState(initialData);
  // Client-side interactivity
  return <div>{/* UI */}</div>;
}
```

## State Management Patterns

### Local State (useState)

Use for component-local UI state:

```typescript
'use client';

export function Component() {
  const [isOpen, setIsOpen] = useState(false);
  const [inputValue, setInputValue] = useState('');

  return (/* UI */);
}
```

### Context API

Use for shared state within a feature:

```typescript
// contexts/FeatureContext.tsx
'use client';

import { createContext, useContext, useState } from 'react';

const FeatureContext = createContext(null);

export function FeatureProvider({ children }) {
  const [state, setState] = useState();

  return (
    <FeatureContext.Provider value={{ state, setState }}>
      {children}
    </FeatureContext.Provider>
  );
}

export const useFeature = () => useContext(FeatureContext);
```

### Zustand (for global state)

```typescript
// stores/useStore.ts
'use client';

import { create } from 'zustand';

interface StoreState {
  count: number;
  increment: () => void;
}

export const useStore = create<StoreState>((set) => ({
  count: 0,
  increment: () => set((state) => ({ count: state.count + 1 })),
}));

// Usage in component
'use client';

import { useStore } from '@/stores/useStore';

export function Component() {
  const { count, increment } = useStore();
  return <button onClick={increment}>{count}</button>;
}
```

## Data Fetching Patterns

### Server-Side Fetching (Preferred)

```typescript
// Server component - automatic caching
export default async function Page() {
  const data = await fetch('https://api.example.com/data', {
    next: { revalidate: 3600 } // Revalidate every hour
  });

  return <div>{/* Render data */}</div>;
}
```

### Client-Side Fetching

```typescript
'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@collider/api-client';

export function ClientDataComponent() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    apiClient.resource.get()
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  return <div>{/* Render data */}</div>;
}
```

### Using @collider/api-client

```typescript
import { apiClient } from '@collider/api-client';

// GET request
const data = await apiClient.resource.list();

// POST request
const created = await apiClient.resource.create(payload);

// PUT/PATCH request
const updated = await apiClient.resource.update(id, payload);

// DELETE request
await apiClient.resource.delete(id);
```

## Styling Patterns

### Tailwind CSS (Recommended)

```typescript
export function StyledComponent() {
  return (
    <div className="flex items-center gap-4 p-4 bg-gray-100 rounded-lg">
      <button className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
        Click Me
      </button>
    </div>
  );
}
```

### CSS Modules (Alternative)

```typescript
// Component.module.css
.container {
  padding: 1rem;
  background: #f0f0f0;
}

// Component.tsx
import styles from './Component.module.css';

export function Component() {
  return <div className={styles.container}>Content</div>;
}
```

### Shared UI Components

```typescript
import { Button, Card, Input } from '@collider/shared-ui';

export function Form() {
  return (
    <Card>
      <Input placeholder="Enter text" />
      <Button variant="primary">Submit</Button>
    </Card>
  );
}
```

## Type Safety Patterns

### Shared Types

```typescript
// libs/api-client/src/types.ts
export interface User {
  id: string;
  name: string;
  email: string;
}

export interface ApiResponse<T> {
  data: T;
  error?: string;
}
```

### Component Props

```typescript
interface ButtonProps {
  variant?: 'primary' | 'secondary';
  size?: 'small' | 'medium' | 'large';
  onClick?: () => void;
  children: React.ReactNode;
}

export function Button({ variant = 'primary', size = 'medium', onClick, children }: ButtonProps) {
  return (/* button */);
}
```

### API Response Types

```typescript
import { User, ApiResponse } from '@collider/api-client';

async function fetchUsers(): Promise<ApiResponse<User[]>> {
  const response = await apiClient.users.list();
  return response;
}
```

## Error Handling Patterns

### Error Boundaries

```typescript
// components/ErrorBoundary.tsx
'use client';

import { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || <div>Something went wrong</div>;
    }
    return this.props.children;
  }
}
```

### Try-Catch Pattern

```typescript
async function handleAction() {
  try {
    const result = await apiClient.resource.action();
    // Handle success
  } catch (error) {
    console.error('Action failed:', error);
    // Show user-friendly error message
    toast.error('Failed to complete action');
  }
}
```

## Testing Patterns

### Component Tests

```typescript
// Component.test.tsx
import { render, screen } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click</Button>);
    screen.getByText('Click').click();
    expect(handleClick).toHaveBeenCalled();
  });
});
```

### Running Tests

```bash
# Test all
npx nx test

# Test specific app/lib
npx nx test portal
npx nx test shared-ui

# Watch mode
npx nx test portal --watch
```

## Nx Commands

### Building

```bash
# Build all
npx nx build portal

# Build with dependencies
npx nx build portal --with-deps

# Build affected by changes
npx nx affected:build
```

### Testing

```bash
# Test all
npx nx test

# Test affected
npx nx affected:test

# E2E tests
npx nx e2e portal-e2e
```

### Development

```bash
# Serve app
npx nx serve portal

# Serve with specific port
npx nx serve portal --port 3001
```

### Dependency Graph

```bash
# View visual dependency graph
npx nx graph
```

## Performance Optimization

### Code Splitting

```typescript
// Lazy load heavy components
import dynamic from 'next/dynamic';

const HeavyComponent = dynamic(() => import('./HeavyComponent'), {
  loading: () => <div>Loading...</div>,
  ssr: false, // Disable SSR if needed
});
```

### Image Optimization

```typescript
import Image from 'next/image';

export function OptimizedImage() {
  return (
    <Image
      src="/image.jpg"
      alt="Description"
      width={500}
      height={300}
      priority // For above-the-fold images
    />
  );
}
```

### Memoization

```typescript
'use client';

import { useMemo, useCallback } from 'react';

export function ExpensiveComponent({ data }) {
  const expensiveValue = useMemo(() => {
    return expensiveCalculation(data);
  }, [data]);

  const handleClick = useCallback(() => {
    // Handler logic
  }, [/* dependencies */]);

  return <div>{/* UI */}</div>;
}
```

## Best Practices

1. **Use Server Components by default** - Only add 'use client' when needed
2. **Leverage Nx generators** - Use Nx CLI to generate consistent code
3. **Centralize shared code** - Put reusable code in libs/
4. **Type everything** - Use TypeScript strictly
5. **Test critical paths** - Focus tests on important user flows
6. **Optimize images** - Always use Next.js Image component
7. **Cache strategically** - Use Next.js caching features
8. **Monitor bundle size** - Keep bundle sizes small

## Related Documentation

- Next.js App Router: https://nextjs.org/docs/app
- Nx Monorepo: https://nx.dev/
- TypeScript: https://www.typescriptlang.org/
- Tailwind CSS: https://tailwindcss.com/
