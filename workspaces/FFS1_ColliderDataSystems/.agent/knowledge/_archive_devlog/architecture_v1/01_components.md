# Component Patterns

> The universal NodeContainer structure and inheritance model.

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
