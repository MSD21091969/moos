# Template Topology

> **Template** = A cluster of containers with a specific graph topology and hydration context.

## Core Concept

A "Template" is not a separate class of object. It is simply a **pre-configured NodeContainer** (or cluster of them) that is hydrated with a specific context.

### Topology vs. Hierarchy

- **Hierarchy** (Foundation) = Parent/Child relationships (ownership, permissions).
- **Topology** (Templates) = The functional graph of how nodes connect and interact.

## Hydration Context

The behavior of a container is determined by how it is **hydrated** (loaded with context).

It is NOT about "types" of containers (e.g. "ToolContainer" vs "AppContainer").  
It IS about what the **Context & Config** allows:

| Context Setting    | Behavior                                        |
| ------------------ | ----------------------------------------------- |
| `can_spawn: true`  | Agent can create new subnodes (morphing/growth) |
| `can_spawn: false` | Agent is fixed, can only execute tools          |
| `domain: FILESYST` | Hydrates from local `.agent` folder (IDE mode)  |
| `domain: CLOUD`    | Hydrates from Database container (App mode)     |

## Template Clusters

A template often defines a **cluster** of nodes, not just one.

**Example: "Research Team" Template**

```
Researcher (Head)
├── Searcher (Tool-focused, specific search tools)
└── Writer (Tool-focused, specific writing tools)
```

- **Topology**: Head controls two subordinates.
- **Hydration**:
  - `Researcher`: Full agency, can spawn sub-tasks.
  - `Searcher`: Restricted context, read-only tools.
  - `Writer`: Restricted context, write-only tools.

## ApplicationGraph

The **ApplicationGraph** is the instantiated topology of a specific application.

- Starts with a **Root Node** (App Container).
- Unfolds based on the **Templates** used.
- Evolving topology as agents create new nodes (if permitted).

## Hydration Paradigm

1. **Definition**: Unhydrated template (static files/json).
2. **Injection**: User/System injects configuration (secrets, specific goals).
3. **Hydration**: System loads the definition + config into a running Container.
4. **Execution**: The Container becomes a Node in the Graph.
