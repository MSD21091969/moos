# Context Hierarchy

> Inheritance system across workspaces.

## Hierarchy Pattern

```
ROOT (FFS0 / RootContainer / RootAccount)
├── includes: []
└── exports: [rules, instructions, ...]
    │
    ▼
CHILD (FFS1 / App1 / UserAccount)
├── includes: [parent exports]
└── exports: [subset or additional]
    │
    ▼
GRANDCHILD (FFS2 / App1/dashboard / UserPrefs)
├── includes: [parent exports]
└── (leaf or continues)
```

## Cross-Domain Pattern

Same pattern works in all domains:

- **FILESYST**: FFS0 → FFS1 → FFS2...
- **CLOUD**: RootContainer → App1 → App1/subnodes...
- **ADMIN**: RootAccount → UserAccount → UserPrefs...

## manifest.yaml

```yaml
includes:
  - path: "../.agent"
    load: [rules/*, instructions/*]

exports:
  - instructions/agent_system.md
  - rules/extension_boundaries.md
```
