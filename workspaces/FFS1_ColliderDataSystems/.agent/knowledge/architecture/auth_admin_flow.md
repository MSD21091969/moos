# Authentication & ADMIN Context

> Flow from Login to Admin Capabilities.

## The Concept

Authentication isn't just about identity; it's about **Context Loading**.
When you log in, you aren't just "User Bob"; you are "Admin of Workspace X" with "Access to Secret Y".

## The Flow

1.  **Trigger**: User clicks "Login with Google" in Extension Popup/Sidepanel.
2.  **Firebase Auth**: Extensions authenticates via `firebase.auth`.
3.  **Token Exchange**: ID Token sent to Data Server.
4.  **Account Lookup**:
    - Data Server verifies token.
    - Looks up `UserNode` in `ADMIN` domain (PostgreSQL).
5.  **Context Fetch**:
    - The `UserNode` contains a `container` field.
    - **Container** holds:
      - `permissions`: ["read:all", "write:app_x"]
      - `secrets`: { "OPENAI_KEY": "sk-..." }
      - `settings`: { "theme": "dark" }
6.  **Hydration**:
    - Data Server returns this container.
    - Extension "hydrates" the **ADMIN Context Layer**.

## Layers in Action

```
[Layer 3] ADMIN Context (Secrets, Perms)  <-- LOADED ON LOGIN
[Layer 2] FILESYST Context (IDE Tools)
[Layer 1] Chrome Context (Tabs, DOM)
[Layer 0] Base Agent
```

## Security

- **Secrets**: Never stored in plain text in the repo. Stored in the ADMIN container in DB.
- **Injection**: When a tool needs a secret (e.g., `cloud_tools.json` needs `API_KEY`), the Agent middleware injects it from the Active ADMIN Context. The LLM never sees the key, only the "System" does.
