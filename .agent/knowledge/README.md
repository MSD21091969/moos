# Knowledge Folder README

This folder stores canonical reference artifacts for FFS0.

## Role

- Canonical terminology and planning references.
- Not an execution contract layer.
- Not a replacement for service API/proto/schema sources.

## Minimal Set

- `current-codebase-glossary-canonical-v1.md`
- `current-codebase-glossary-canonical-v1.json`
- `container-graph-logic-json-schema-v0.md`
- `conversation-state.md`
- `architecture-findings.md`
- `research-findings.md`
- `implementation-plan-scaffold.md`

## Read Order

1. `current-codebase-glossary-canonical-v1.md`
2. `container-graph-logic-json-schema-v0.md`
3. `conversation-state.md`
4. `architecture-findings.md` + `research-findings.md`
5. `implementation-plan-scaffold.md`

## Maintenance Rules

- Keep term decisions synchronized across canonical `.md` and `.json` files.
- Record ambiguities in `conversation-state.md` before adding new canonical terms.
- Prefer root-reference links in downstream workspaces instead of duplicating canon.

## Non-Goals

- Execution logic and runtime behavior belong to `tools/`, `workflows/`, and service code.
- Avoid broad narrative docs here unless they directly support canonical decisions.
