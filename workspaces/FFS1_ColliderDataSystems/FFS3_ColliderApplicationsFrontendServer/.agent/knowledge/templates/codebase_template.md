# Codebase: [APP_NAME]

> [One-line technical description including key technologies]

## Overview

[2-3 sentences describing the implementation approach, architecture decisions, and technical stack]

## Directory Structure

```
[APP_DIRECTORY]/
├── components/
│   ├── [ComponentCategory]/
│   │   ├── Component1.tsx
│   │   └── Component2.tsx
├── pages/ or app/          # Next.js routing
│   ├── [route]/
│   │   └── page.tsx
├── hooks/
│   ├── useCustomHook.ts
├── services/
│   ├── api.ts
│   ├── storage.ts
├── types/
│   └── index.ts
├── utils/
│   └── helpers.ts
└── styles/
    └── [styling approach]
```

## Component Architecture

### Core Components

**[ComponentName]** (`path/to/component.tsx`)
- **Purpose**: What it does
- **Props**: Key props it accepts
- **State**: What state it manages
- **Dependencies**: Other components it uses
- **Integration**: APIs/services it calls

**[AnotherComponent]** (`path/to/another.tsx`)
- [Same structure as above]

### Shared Components

Uses these from `@collider/shared-ui`:
- `<SharedComponent1>` - Usage in this app
- `<SharedComponent2>` - Usage in this app

## Data Flow

### State Management

```
[Describe the state management pattern used]

Example:
1. User action triggers event
2. Event updates state in [store/context]
3. State change triggers re-render
4. UI reflects new state
```

### API Integration

Uses `@collider/api-client` for:
```typescript
// Example API calls
import { apiClient } from '@collider/api-client';

apiClient.resource.method()
```

**Key Endpoints:**
- `GET /api/path` - What it fetches
- `POST /api/path` - What it creates/updates

### Chrome Extension Communication (if applicable)

**Messages Sent:**
```typescript
chrome.runtime.sendMessage({
  type: 'MESSAGE_TYPE',
  payload: { ... }
});
```

**Messages Received:**
```typescript
chrome.runtime.onMessage.addListener((message) => {
  if (message.type === 'MESSAGE_TYPE') {
    // Handle message
  }
});
```

### Native Host Communication (if applicable)

**Protocol:**
```typescript
// Message format
{
  command: 'COMMAND_NAME',
  params: { ... }
}
```

**Supported Commands:**
- `command1` - Purpose and return value
- `command2` - Purpose and return value

## Key Features Implementation

### Feature 1: [Feature Name]

**Implementation:**
- Component: `path/to/component.tsx`
- Logic: [Describe how it works]
- Dependencies: [List dependencies]

**Code Example:**
```typescript
// Key implementation snippet
```

### Feature 2: [Feature Name]

[Same structure as Feature 1]

## Styling Approach

- **Framework**: [Tailwind CSS / CSS Modules / styled-components / etc.]
- **Theme System**: [How theming works]
- **Responsive Design**: [Breakpoints, mobile-first, etc.]

## Performance Considerations

- [Any special optimizations]
- [Lazy loading approaches]
- [Memoization strategies]
- [Code splitting]

## Testing

### Unit Tests
```bash
pnpm test [app-name]
```

### Test Structure
- Component tests: `__tests__/*.test.tsx`
- Hook tests: `hooks/__tests__/*.test.ts`
- Integration tests: `__tests__/integration/*.test.tsx`

## Known Issues / Technical Debt

- [List any known issues]
- [Technical debt items]
- [Future improvements planned]

## Special Considerations

### Browser Compatibility
- [Any browser-specific notes]

### Security
- [Authentication approach]
- [Authorization considerations]
- [Data handling notes]

### Accessibility
- [A11y considerations]
- [ARIA usage]
- [Keyboard navigation]

## Related Code

- **Shared UI Library**: `../../libs/shared-ui/`
- **API Client**: `../../libs/api-client/`
- **Backend Services**: `../../../FFS2_ColliderBackends/`

## Development Workflow

1. **Adding a new feature**:
   ```bash
   # Create component
   # Add route if needed
   # Update types
   # Write tests
   ```

2. **Debugging**:
   - Chrome DevTools
   - [Framework-specific debug tools]
   - [Logging approach]

3. **Building for production**:
   ```bash
   npx nx build [app-name]
   ```
