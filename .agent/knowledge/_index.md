# Factory Knowledge Graph

> Single source of truth for all development knowledge

## Structure

```text
knowledge/
├── domains/          # WHAT you know (technical depth)
│   ├── mathematics/  # Category theory, tensors, boundary theory
│   ├── architectures/# System design patterns
│   ├── languages/    # Python, TypeScript, Rust idioms
│   └── infrastructure/# Docker, K8s, cloud patterns
│
├── projects/         # WHAT you build (active work)
│   ├── collider/     # Linked Data Ecosystem
│   ├── maassen_hochrath/# Personal AI workspace
│   └── _archive/     # Completed/paused projects
│
├── references/       # EXTERNAL sources (curated)
│   ├── papers/       # PDFs, citations
│   ├── specs/        # RFCs, API docs
│   └── snippets/     # Reusable code patterns
│
├── workflows/        # HOW you work (process)
│
└── journal/          # WHEN things happened (temporal)
    └── decisions/    # Architecture Decision Records
```

## Access Pattern

- **Factory root** owns all knowledge
- **Projects** receive read-only junctions to relevant nodes
- **Agents** have Read-Only access to this folder

## Last Updated

2026-01-25 - Initial Factory migration
