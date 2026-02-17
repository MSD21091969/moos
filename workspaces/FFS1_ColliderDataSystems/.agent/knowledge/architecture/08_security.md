# Security

> Authentication, authorization, secrets management, and security boundaries.

## Authentication Flow

### DataServer (Current)

```
1. User submits credentials
   POST /api/v1/auth/login { username, password }
                    │
                    ▼
2. Data Server:
   ├── Verify password hash (bcrypt)
   ├── Lookup User in SQLite
   ├── Generate JWT token
   └── Return { access_token, user }
                    │
                    ▼
3. Client stores JWT, sends in Authorization header
   Authorization: Bearer <token>
```

### Chrome Extension (Planned)

```
1. User clicks "Login with Google" in Extension
                    │
                    ▼
2. Firebase Auth (firebase.auth.signInWithPopup)
                    │
                    ▼
3. Get Firebase ID Token → exchange for DataServer JWT
```

---

## User Model

```
┌───────────────────────────────────────────────────────┐
│                    USER (e.g. Sam)                     │
│                                                       │
│  ┌─────────────────────────────────────────────────┐ │
│  │ User                                             │ │
│  │                                                   │ │
│  │ • id (UUID)                                       │ │
│  │ • username (unique)                               │ │
│  │ • password_hash                                   │ │
│  │ • display_name                                    │ │
│  │ • system_role (superadmin | collider_admin |      │ │
│  │                 app_admin | app_user)              │ │
│  └─────────────────────────────────────────────────┘ │
│                                                       │
│  Test credentials: Sam/Lola/Menno / test123           │
└───────────────────────────────────────────────────────┘
```

- Every authenticated user gets a `User` record with a `system_role`
- `system_role` determines platform-level access (replaces AdminAccount)
- Only SAD and CAD can assign system roles via `POST /users/{id}/assign-role`

---

## Application Permissions

Source: `src/db/models.py` -- `AppPermission`

```
┌─────────────────────────────────────────┐
│            AppPermission                │
│                                         │
│  user_id ──────────► User              │
│  application_id ───► Application       │
│                                         │
│  role: AppRole (app_admin | app_user)  │
│                                         │
│  UNIQUE(user_id, application_id)       │
└─────────────────────────────────────────┘
```

### Access Request Flow

```
1. User requests access:
   POST /api/v1/apps/{id}/request-access { message? }

2. Admin reviews pending requests:
   GET /api/v1/apps/{id}/pending-requests

3. Admin approves (with role) or rejects:
   POST /api/v1/apps/{id}/requests/{req_id}/approve { role: "app_user" }
   POST /api/v1/apps/{id}/requests/{req_id}/reject
```

**Enforcement points:**
1. **Data Server**: Checks permissions on every API call
2. **Service Worker**: Filters available apps based on user permissions
3. **SSE**: Notifies clients of permission changes in real-time

---

## Secrets Management

### Principles

1. **Never in code** -- No secrets committed to repository
2. **Never to LLM** -- Agent never sees raw secret values
3. **Injection at runtime** -- Middleware injects secrets when tools need them

### Storage

Secrets are stored in the user's ADMIN container (`users.container` JSON):

```json
{
  "container": {
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

### Injection Flow

```
1. Tool definition declares required secrets:
   { "name": "github_search", "requires": ["GITHUB_TOKEN"] }

2. Agent calls tool: github_search({ query: "..." })

3. Tool executor (middleware):
   ├── Looks up GITHUB_TOKEN from contextManager.user.container.secrets
   ├── Injects into API call headers
   └── Executes tool

4. Agent receives result, never sees the token value
```

### Manifest-Level Secret Declaration

Source: `.agent/manifest.yaml`

```yaml
secrets:
  - OPENAI_API_KEY
  - GEMINI_API_KEY
  - FIREBASE_PROJECT_ID
```

Declares which secrets this workspace may use. Actual values are stored in the ADMIN container.

---

## Native Messaging Security

```
┌───────────────────────────────────────────────────┐
│              NATIVE HOST SECURITY                 │
│                                                   │
│  1. allowed_origins: Only registered extension    │
│     "chrome-extension://EXTENSION_ID/"            │
│                                                   │
│  2. Path restrictions: Host only accesses         │
│     permitted filesystem paths                    │
│                                                   │
│  3. JSON-only: No arbitrary code execution        │
│     All messages are parsed and validated JSON     │
│                                                   │
│  4. Registry-based: Windows requires entry at     │
│     HKCU\Software\Google\Chrome\                  │
│     NativeMessagingHosts\...                      │
└───────────────────────────────────────────────────┘
```

---

## CORS Policy

Source: `ColliderDataServer/src/main.py`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"^chrome-extension://.*$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Allows:
- Any Chrome extension origin (regex match)
- Configured additional origins (from settings)
- All methods and headers with credentials

---

## Context Security Layers

Security context is layered. Each layer can restrict or extend agent capabilities:

```
┌────────────────────────────────────────┐
│ Layer 3: ADMIN Context                 │  Secrets, global permissions
│          (Loaded on login)             │  Source: user.container
├────────────────────────────────────────┤
│ Layer 2: APP Context                   │  App-specific rules, domain
│          (Loaded on app navigation)    │  Source: application.config
├────────────────────────────────────────┤
│ Layer 1: NODE Context                  │  Node-specific tools, instructions
│          (Loaded on node navigation)   │  Source: node.container
├────────────────────────────────────────┤
│ Layer 0: Base Agent                    │  General capabilities
│          (Initialized on startup)      │  Source: built-in agent logic
└────────────────────────────────────────┘
```

**Layer resolution**: Higher layers override lower layers. A node context can restrict tools available at the app level. Admin context secrets are available to all layers but never exposed to the LLM.
