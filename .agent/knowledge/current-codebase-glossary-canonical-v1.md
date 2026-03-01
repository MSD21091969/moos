# Current Codebase Glossary — Canonicalization v1

Locked on 2026-02-28.

## Locked Terms

- **workspace**: Admin control-plane context.
- **app**: Template + policy envelope.
- **graph**: Must be explicit as `ContainerGraph`, `ExecutionGraph`, or `ViewGraph`.
- **skill**: Compatibility projection (derived/generated), not runtime source-of-truth.
- **session**: `session_id` external contract, `sessionKey` internal runtime key.
- **metadata**: Canonical `metadata`; `metadata_` is alias/adapter naming.
- **roles**: Two-layer canonical model: `SystemRole` + `AppRole`; frontend `ContextRole` is projection.
- **context**: Typed runtime state; prompt/prose are projections.
- **tool**: Atomic executable contract (smallest capability unit).
- **workflow**: Composed executable contract (ordered/conditional composition of tools and/or subworkflows).
- **node**: Persisted graph entity row (`Node`) that carries container payload and hierarchy coordinates.
- **container**: Typed recursive runtime state payload (`NodeContainer`) attached to a node.
- **identifier axis**: `app_id` canonical for contracts; `id`/`application_id` are legacy or layer-specific aliases.
- **boundary axis**: `domain` = profile label, `species` = container classification, `api_boundary` = enforceable protocol permissions.
- **runtime/provider axis**: provider selection and runtime implementation are distinct dimensions.
- **agent**: Runtime process role executing over state/effects.
- **subagent**: Capability-scoped delegated runtime process with trace linkage.
- **appnode**: Frontend runtime surface (e.g., `ffs4`, `ffs5`, `ffs6`) for interacting with application state.

## Usage Rules

- Do not use overloaded nouns without qualifier.
- Prefer explicit names in docs/contracts:
  - `AppTemplate`, `AppInstance`, `Appnode`
  - `ContainerGraph`, `ExecutionGraph`, `ViewGraph`
  - `session_id` (public), `sessionKey` (internal)
- Keep compatibility layers clearly marked as derived (`skill` family terms).
- Use `Node` when referring to DB graph entities and `NodeContainer` when referring to runtime payload shape.
- Use `tool`/`workflow` only for executable contracts, not for prose task descriptions.
- Use `app_id` in new API/interface definitions unless constrained by existing adapter contracts.

## Transition Mapping (Current -> Canonical)

- `Application` (current persisted DB entity) maps to canonical `AppTemplate` semantics.
- Hydrated user/tenant runtime realization maps to canonical `AppInstance`.
- `Appnode` remains frontend surface terminology and must not replace template/instance semantics.
- During migration, preserve existing DB/API names for compatibility; apply canonical names in architecture/specs first.

## Canonicalization Status

- v1 is complete for current top-level ambiguities and core runtime nouns.
- New terms must be added through the same clarify-then-lock workflow and recorded in both `.md` and `.json` files.
