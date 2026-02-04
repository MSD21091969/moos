# Foundation

> Core data model: NodeContainer, domains, hierarchy, applications.

## NodeContainer Pattern

Every node in Collider follows this universal structure:

```
NODE
├── subnodes[]              ← Child nodes (recursive)
└── container/              ← Context storage (.agent)
    ├── manifest.yaml       ← Inheritance config
    ├── index.md            ← Node description
    ├── instructions/       ← Agent instructions
    ├── rules/              ← Behavioral constraints
    ├── skills/             ← Capabilities
    ├── tools/              ← Available tools
    ├── knowledge/          ← Reference docs
    ├── workflows/          ← Executable workflows
    └── configs/            ← Configuration files
```

**Principles:**

- Node = Workspace (every node is a workspace)
- Recursive (subnodes follow same pattern)
- Workflows create subnodes (agent creates workflow → new subnode)

---

## Three Domains

| Domain       | Purpose                      | Storage                         | Backend          |
| ------------ | ---------------------------- | ------------------------------- | ---------------- |
| **FILESYST** | Local file workspaces (IDE)  | `.agent/` folders on filesystem | Native Messaging |
| **CLOUD**    | Cloud workspace applications | `container` field in DB         | Data Server      |
| **ADMIN**    | User accounts & permissions  | `container` field in account    | Data Server      |

### FILESYST

```
D:\FFS0_Factory\.agent\                                    # Root
D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\.agent\ # Child
D:\...\FFS2_ColliderBackends_MultiAgentChromeExtension\.agent\ # Grandchild
```

### CLOUD

```json
{
  "node_id": "uuid",
  "container": {
    "manifest": "...",
    "instructions": [],
    "workflows": []
  },
  "subnodes": [...]
}
```

### ADMIN

Same as CLOUD but for accounts: UserAccount, AdminAccount, ApplicationAccount.

---

## Hierarchy & Inheritance

Nodes inherit context from parents via `manifest.yaml`:

```yaml
includes:
  - path: "../.agent"
    load: [rules/*, instructions/*]

exports:
  - instructions/agent_system.md
  - rules/extension_boundaries.md
```

**Pattern:**

```
ROOT (FFS0 / RootContainer / RootAccount)
├── exports: [rules, instructions]
    │
    ▼
CHILD (FFS1 / App1 / UserAccount)
├── includes: [parent exports]
├── exports: [subset or additional]
    │
    ▼
GRANDCHILD (FFS2 / App1/dashboard)
├── includes: [parent exports]
└── (leaf or continues)
```

---

## Applications

### Application Hierarchy

```
App 0 (Root Portal)
├── Always present
├── Domain-agnostic context
└── General agent instruction set

App X (FILESYST Domain)
├── IDE for Collider Data Systems
├── Context from .agent/ folders
└── Skills: code assist

App Z (ADMIN Domain)
├── Account management
├── Context from account containers
└── Admin functions

App 1, 2, 3... (CLOUD Domain)
├── Cloud workspace applications
├── Context from node containers
└── Full nodecontainer pattern
```

### ApplicationConfig vs .agent Context

**Two completely different things:**

| Aspect              | ApplicationConfig                            | .agent Context                 |
| ------------------- | -------------------------------------------- | ------------------------------ |
| **Purpose**         | Backend governance                           | Workspace intelligence         |
| **Contains**        | API permit/block, rate limits, secrets rules | Instructions, tools, workflows |
| **Storage**         | ApplicationAccount in DB                     | ContainerNodes in DB           |
| **Access**          | Admin CRUD only                              | SW fetches for agent           |
| **Sent to browser** | Never                                        | Yes, hydrates agent            |

### Application Ownership

```
┌───────────────────────────────────────────────┐
│           APPLICATION (appid#)                 │
│                                                │
│  Owner: ApplicationAdmin                       │
│                                                │
│  ApplicationConfig (backend-only):             │
│  • API permit/block                            │
│  • Rate limits                                 │
│  • Secrets rules                               │
│                                                │
│  Appnode Graph (.agent context):               │
│  • Each node has container                     │
│  • Instructions, tools, workflows              │
│  • Delivered to browser                        │
└───────────────────────────────────────────────┘
```
