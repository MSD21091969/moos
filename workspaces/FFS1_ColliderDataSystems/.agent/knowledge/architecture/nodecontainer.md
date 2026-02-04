# Universal NodeContainer Pattern

> Core pattern for all nodes across all domains.

## Structure

Every node in Collider follows this pattern regardless of domain:

```
NODE
├── subnodes[]              ← Child nodes (recursive)
└── container/              ← Context storage
    ├── manifest.yaml       ← Inheritance config
    ├── instructions/
    ├── rules/
    ├── skills/
    ├── tools/
    ├── knowledge/
    ├── workflows/
    └── configs/
```

## Key Principles

1. **Node = Workspace**: Every node is a workspace
2. **Recursive**: Subnodes follow same pattern
3. **Node defined by subnodes**: Container + subnodes = the node
4. **Workflows create subnodes**: Agent creates workflow → new subnode with container

## Domain Storage

| Domain   | Container Storage               |
| -------- | ------------------------------- |
| FILESYST | `.agent/` folders on filesystem |
| CLOUD    | `container` field in DB         |
| ADMIN    | `container` field in account    |

## Inheritance

Nodes inherit context from parent via `manifest.yaml`:

- `includes:` what to load from parent
- `exports:` what children can inherit
