# Conversation State

Last Updated: 2026-03-01

## Current Objective

- Operationalize the glossary-first conversation methodology into a durable FFS0 rehydration workflow and linked knowledge artifacts used before downstream implementation.

## Scope Boundary

- In scope:
  - FFS0 `.agent` workflow + knowledge artifacts for conversation-state rehydration.
  - Root discoverability updates in `.agent/index.md` and `.agent/knowledge/README.md`.
  - Template-driven architecture/research/implementation capture.
- Out of scope:
  - Runtime/service code refactors in FFS2/FFS3.
  - Repairing unrelated legacy/broken architecture references.
  - Canonical glossary term-set expansion beyond already-locked v1 terms.

## Locked Decisions

- Decision: Keep findings/scaffold docs at top-level `.agent/knowledge`.
  - Rationale: Treat these as cross-workspace operational artifacts, not architecture-subtree internals.
  - Impacted artifacts: `.agent/knowledge/{conversation-state,architecture-findings,research-findings,implementation-plan-scaffold}.md`.

- Decision: Rehydration workflow uses runbook + frontmatter style.
  - Rationale: Align with existing root workflow conventions and ensure repeatable execution phases.
  - Impacted artifacts: `.agent/workflows/conversation-state-rehydration.md`.

- Decision: Defer unrelated broken-reference cleanup.
  - Rationale: Keep this cycle scoped to conversation-state system implementation.
  - Impacted artifacts: planning scope and execution slices only.

## Active Constraints

- Constraint: Canonical vocabulary must be used in new docs.
  - Source (policy/code/user): User-requested glossary-first governance + canonical glossary v1.
  - Effect on implementation: All state/findings/plans use explicit terms (`AppTemplate`, graph variants, `session_id`, etc.).

- Constraint: FFS0 is canonical root for context and governance.
  - Source (policy/code/user): Root `CLAUDE.md` + `.agent/index.md` hierarchy.
  - Effect on implementation: Canon remains in FFS0; downstream references should point back instead of duplicating canon.

- Constraint: Minimal scope execution.
  - Source (policy/code/user): explicit choice to defer ref-cleanup and avoid unrelated edits.
  - Effect on implementation: only requested workflow artifacts and indexing links were added.

## Canonical Term Checks

- Verified against `current-codebase-glossary-canonical-v1.md`: yes
- Any term exceptions: none

## Open Questions / Ambiguities

- Question: When should downstream workspaces embed local summaries vs link-only references to FFS0 canon?
  - Why unresolved: no explicit depth policy yet for FFS1/FFS2/FFS3 local adaptation.
  - Needed to unblock: define a propagation policy (link-only, mirrored summary, or hybrid).

- Question: Should glossary v1 term lock cadence be tied to release tags or working-session checkpoints?
  - Why unresolved: governance cadence not formalized.
  - Needed to unblock: agree on update trigger policy for canonical term changes.

## Next Session Bootstrap

- First action: Run Phase 1 intake from `workflows/conversation-state-rehydration.md` and refresh this file with new objective deltas.
- Files to open first:
  - `.agent/knowledge/current-codebase-glossary-canonical-v1.md`
  - `.agent/knowledge/conversation-state.md`
  - `.agent/knowledge/architecture-findings.md`
  - `.agent/knowledge/research-findings.md`
  - `.agent/knowledge/implementation-plan-scaffold.md`
- Validation target: Produce an implementation scaffold with at least one executable slice mapped to concrete files/symbols.

## Session Wrap (2026-03-01)

- Completed: DRY doc alignment across FFS0/FFS1/FFS2/FFS3 (`CLAUDE.md` + key `README.md` files) with canonical FFS0 references.
- Completed: removed active `GEMINI.md` files in FFS0, FFS1, and FFS3.
- Completed: verified `ffs6` build/typecheck path (`pnpm nx build ffs6`, `pnpm nx run ffs6:typecheck`).
- Next focus: finish FFS0 hydration review/sign-off, then generate per-workspace rebuild checklists for FFS1 → FFS6.
