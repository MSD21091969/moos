# FFS0 Factory - Agent Context

> Minimal root semantic index for FFS0.

## Core Model

```text
.agent/ = governance + constraints + executable contracts
```

## Semantic Layers (minimal)

- `rules/` = hard constraints
- `tools/` = atomic executable contracts
- `workflows/` = composed executable contracts
- `instructions/` = compact intent framing
- `configs/` = shared settings
- `knowledge/` = canonical reference (not runtime contract)

`skills/` is optional at root and may remain empty.

## Inheritance Direction

```text
FFS0 .agent (canonical)
  -> FFS1 .agent (execution context)
    -> FFS2 / FFS3 local execution artifacts
```

## Export Contract

See `manifest.yaml` for authoritative exports.

Current exported categories:

- `rules/*`
- `instructions/agent_system.md`
- `configs/*`

## Canonical References

- [Conversation Rehydration Runbook](workflows/conversation-state-rehydration.md)
- [Canonical Glossary v1](knowledge/current-codebase-glossary-canonical-v1.md)
- [Container-Graph Logic JSON Schema v0](knowledge/container-graph-logic-json-schema-v0.md)
- [Conversation State](knowledge/conversation-state.md)
- [Architecture Findings](knowledge/architecture-findings.md)
- [Research Findings](knowledge/research-findings.md)
- [Implementation Plan Scaffold](knowledge/implementation-plan-scaffold.md)

---

Version: v4.0.0 — 2026-03-01
