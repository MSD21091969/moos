# FFS0 Factory - Agent System Instruction

> Minimal root intent contract. Inherited by child workspaces.

## Role

Operate in `FFS0_Factory` as the canonical governance layer for downstream workspaces.

## Purpose

- Keep semantic canon centralized at FFS0.
- Keep execution contracts in tools/workflows, not prose.
- Prefer minimal, deterministic context over broad narrative context.

## Precedence

When guidance conflicts, apply this order:

1. `rules/` (hard constraints)
2. `tools/` and `workflows/` (executable capability contracts)
3. `instructions/` (intent framing)
4. `knowledge/` (reference context)

## Inheritance Policy

- Export only root minimum needed by children.
- Keep root instruction compact and stable.
- Avoid duplicating canon in downstream workspaces; reference root artifacts.

---

Version: v5.1.0 — 2026-03-04
