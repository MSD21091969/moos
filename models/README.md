# Collider Models v3

> Clean slate Pydantic models

## Status

🚧 **Under Development**

## Structure (planned)

```text
models/
├── __init__.py
├── container.py      # Workspace context holder
├── definition.py     # Versioned I/O contract
├── graph.py          # Topology
└── node.py           # Base node
```

## Design Principles

1. **Container** = workspace context in graph (minimal)
2. **Definition** = versioned, immutable I/O contract
3. **Graph** = pure topology, no execution
4. **Composition over inheritance**
