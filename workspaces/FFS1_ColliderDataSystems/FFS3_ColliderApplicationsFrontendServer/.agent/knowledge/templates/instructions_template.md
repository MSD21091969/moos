# [APP_NAME] Development Instructions

> Guidelines and patterns for developing features in [APP_NAME]

## Getting Started

### Prerequisites
- [List required tools, versions, access]
- [Environment setup requirements]

### Initial Setup
```bash
# Commands to set up the development environment
cd collider-frontend
pnpm install
pnpm dev
```

## Code Organization Patterns

### Component Structure

Follow this pattern when creating components:

```typescript
// [AppName]Component.tsx
import React from 'react';

interface [ComponentName]Props {
  // Props definition
}

export const [ComponentName]: React.FC<[ComponentName]Props> = ({ ...props }) => {
  // 1. Hooks (useState, useEffect, custom hooks)
  // 2. Derived state & memoization
  // 3. Event handlers
  // 4. Effects
  // 5. Render logic

  return (
    <div>
      {/* JSX */}
    </div>
  );
};
```

### File Naming Conventions

- **Components**: `PascalCase.tsx` (e.g., `UserProfile.tsx`)
- **Hooks**: `camelCase.ts` starting with 'use' (e.g., `useDataSync.ts`)
- **Utils**: `camelCase.ts` (e.g., `formatters.ts`)
- **Types**: `PascalCase.ts` or `types.ts` (e.g., `UserTypes.ts`)
- **Tests**: `*.test.tsx` or `*.test.ts`

### Directory Organization

```
src/
├── components/
│   ├── [FeatureArea]/        # Group by feature
│   │   ├── Component.tsx
│   │   └── Component.test.tsx
├── hooks/                     # Custom hooks
├── services/                  # API clients, external services
├── types/                     # TypeScript types/interfaces
├── utils/                     # Pure utility functions
└── constants/                 # App constants
```

## Common Patterns

### State Management

**When to use useState:**
- Component-local state
- UI-only state (modals, toggles, form inputs)

**When to use Context/Zustand:**
- Shared state across multiple components
- Global application state
- [App-specific state management rules]

**Example:**
```typescript
// [App-specific example]
```

### API Calls

Always use `@collider/api-client`:

```typescript
import { apiClient } from '@collider/api-client';

// In component or hook
const fetchData = async () => {
  try {
    const data = await apiClient.[resource].[method]();
    // Handle success
  } catch (error) {
    // Handle error
  }
};
```

### Error Handling

```typescript
// Standard error handling pattern for this app
try {
  // Operation
} catch (error) {
  console.error('[Context]:', error);
  // Show user-friendly error
  // Log to error tracking service
}
```

### Loading States

```typescript
// Standard loading pattern
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState<Error | null>(null);

const performAction = async () => {
  setIsLoading(true);
  setError(null);
  try {
    // Action
  } catch (err) {
    setError(err as Error);
  } finally {
    setIsLoading(false);
  }
};
```

## Feature-Specific Patterns

### [Feature Area 1]

**When building [feature type]:**
1. [Step-by-step guidance]
2. [Key considerations]
3. [Common pitfalls to avoid]

**Example:**
```typescript
// Example code
```

### [Feature Area 2]

[Same structure]

## Integration Guidelines

### Backend Integration

**API Endpoints:**
- Base URL: `process.env.NEXT_PUBLIC_API_BASE`
- Authentication: [How auth is handled]
- Request format: [Standard request structure]

### Chrome Extension Integration (if applicable)

**Messaging Pattern:**
```typescript
// Send message to extension
chrome.runtime.sendMessage({
  type: '[MESSAGE_TYPE]',
  payload: data
}, (response) => {
  // Handle response
});

// Listen for messages
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === '[MESSAGE_TYPE]') {
    // Handle message
    sendResponse({ success: true });
  }
});
```

### Native Host Integration (if applicable)

**Command Pattern:**
```typescript
// Send command to native host
const sendCommand = async (command: string, params: any) => {
  // Implementation
};
```

## Styling Guidelines

### Using [Styling System]

```typescript
// [App-specific styling examples]
```

### Responsive Design

- Mobile-first approach
- Breakpoints: [List breakpoints]
- [Responsive patterns used in this app]

### Theming

```typescript
// How to use theme variables
```

## Testing Guidelines

### Unit Tests

```typescript
import { render, screen } from '@testing-library/react';
import { [ComponentName] } from './[ComponentName]';

describe('[ComponentName]', () => {
  it('should [test case]', () => {
    render(<[ComponentName] />);
    // Assertions
  });
});
```

### Integration Tests

```typescript
// [App-specific integration test patterns]
```

## Performance Best Practices

1. **Memoization**: Use `React.memo()`, `useMemo()`, `useCallback()` appropriately
2. **Code Splitting**: Lazy load heavy components
3. **Image Optimization**: Use Next.js Image component
4. **[App-specific performance tips]**

## Security Considerations

- **Input Validation**: Always validate user input
- **XSS Prevention**: Sanitize HTML content
- **API Keys**: Never commit secrets, use env variables
- **[App-specific security notes]**

## Debugging Tips

### Chrome DevTools
- React DevTools for component inspection
- Network tab for API calls
- [App-specific debug tools]

### Common Issues

**Issue 1: [Common Problem]**
- **Symptom**: [What you see]
- **Cause**: [Why it happens]
- **Solution**: [How to fix]

**Issue 2: [Common Problem]**
[Same structure]

## Code Review Checklist

Before submitting a PR, ensure:
- [ ] Code follows naming conventions
- [ ] Components are properly typed
- [ ] Error handling is implemented
- [ ] Loading states are handled
- [ ] Tests are written and passing
- [ ] No console.log statements in production code
- [ ] Code is properly formatted (Prettier)
- [ ] ESLint passes with no warnings
- [ ] [App-specific checklist items]

## Resources

- [Link to relevant internal docs]
- [External documentation links]
- [Team communication channels]
