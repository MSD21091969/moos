# Security

> Authentication, permissions, secrets management.

## Authentication Flow

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         AUTH FLOW                                           │
│                                                                             │
│  1. User clicks "Login with Google" in Extension                           │
│                        │                                                    │
│                        ▼                                                    │
│  2. Firebase Auth (firebase.auth.signInWithPopup)                          │
│                        │                                                    │
│                        ▼                                                    │
│  3. Get ID Token                                                            │
│                        │                                                    │
│                        ▼                                                    │
│  4. Send Token to Data Server                                               │
│     POST /api/v1/auth/verify { idToken }                                   │
│                        │                                                    │
│                        ▼                                                    │
│  5. Data Server:                                                            │
│     - Verify token with Firebase Admin SDK                                 │
│     - Lookup UserAccount in PostgreSQL                                     │
│     - Return container (permissions, settings)                             │
│                        │                                                    │
│                        ▼                                                    │
│  6. SW hydrates ADMIN Context (Main Context)                               │
│     - context_manager.main.user = userAuth                                 │
│     - context_manager.main.permissions = permissions[]                     │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## User & Admin Model

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER (@test.com)                         │
│                                                                  │
│  ┌────────────────────┐    ┌────────────────────────────────┐   │
│  │   UserAccount      │    │   AdminAccount(s) (optional)   │   │
│  │                    │    │                                │   │
│  │  • id, email       │    │  • Manages appid#123           │   │
│  │  • profile         │    │  • Can CRUD ApplicationConfig  │   │
│  │  • container       │    │  • Can manage app permissions  │   │
│  │    (ADMIN .agent)  │    │                                │   │
│  │  • adminAccounts[] │    │                                │   │
│  └────────────────────┘    └────────────────────────────────┘   │
│                                                                  │
│  Test credentials: *@test.com / test123                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Application Permissions

Users have permissions per application:

```typescript
interface ApplicationPermission {
  userId: string;
  applicationId: string;
  permissions: {
    read: boolean; // Can view app
    write: boolean; // Can modify nodes
    admin: boolean; // Can manage app config
  };
}
```

**Storage:** `ApplicationPermission` table in PostgreSQL

**Enforcement:**

- Data Server checks permissions on every API call
- SW filters available apps based on permissions
- SSE notifies of permission changes

---

## Secrets Management

### Storage

Secrets are stored in the **ADMIN container** (UserAccount.container):

```json
{
  "container": {
    "permissions": ["read:all", "write:app_x"],
    "secrets": {
      "OPENAI_KEY": "sk-...",
      "GITHUB_TOKEN": "ghp_..."
    },
    "settings": {
      "theme": "dark"
    }
  }
}
```

### Principles

1. **Never in code** - No secrets in repository
2. **Never to LLM** - Agent never sees raw secret values
3. **Injection at runtime** - Middleware injects secrets when tool needs them

### Injection Flow

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         SECRET INJECTION                                    │
│                                                                             │
│  1. Tool definition requests secret:                                        │
│     { "name": "github_search", "requires": ["GITHUB_TOKEN"] }              │
│                                                                             │
│  2. Agent calls tool: github_search({ query: "..." })                      │
│                                                                             │
│  3. Tool executor (middleware):                                             │
│     - Looks up GITHUB_TOKEN from context_manager.main.secrets              │
│     - Injects into API call headers                                        │
│     - Executes tool                                                         │
│                                                                             │
│  4. LLM sees result, never sees token                                       │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Native Messaging Security

```
┌─────────────────────────────────────────────────────────────────┐
│                    NATIVE HOST SECURITY                          │
│                                                                  │
│  1. allowed_origins: Only registered extension can connect      │
│     "allowed_origins": ["chrome-extension://EXTENSION_ID/"]     │
│                                                                  │
│  2. Path restrictions: Host only accesses permitted paths       │
│     Configured in host manifest or hardcoded                    │
│                                                                  │
│  3. JSON-only: No arbitrary code execution                      │
│     All messages are JSON, parsed and validated                 │
│                                                                  │
│  4. Registry-based: Windows requires registry entry             │
│     HKCU\Software\Google\Chrome\NativeMessagingHosts\...       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Context Layers

Security context is layered:

```
┌────────────────────────────────────────┐
│ Layer 3: ADMIN Context                 │  ← Secrets, permissions
│          (Loaded on login)             │
├────────────────────────────────────────┤
│ Layer 2: APP Context                   │  ← App-specific rules
│          (Loaded on app navigation)    │
├────────────────────────────────────────┤
│ Layer 1: NODE Context                  │  ← Node-specific tools
│          (Loaded on node navigation)   │
├────────────────────────────────────────┤
│ Layer 0: Base Agent                    │  ← General capabilities
└────────────────────────────────────────┘
```

Each layer can restrict or extend what the agent can do.
