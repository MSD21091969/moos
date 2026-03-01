---
description: Preserve conversation intent as durable artifacts and rehydrate implementation context from FFS0 downward
---

# Conversation-State Rehydration Runbook

Use this workflow to convert an active conversation into persistent project context, then resume implementation without semantic drift.

## Scope

- Canonical source workspace: `FFS0`.
- Propagation target: downstream workspaces (`FFS1` -> `FFS2` / `FFS3`) by reference, not duplicate canon.
- Terminology guardrail: always align with `current-codebase-glossary-canonical-v1.md` before writing findings or plans.

## Required Artifacts

1. `knowledge/conversation-state.md`
2. `knowledge/architecture-findings.md`
3. `knowledge/research-findings.md`
4. `knowledge/implementation-plan-scaffold.md`

## Phase 1 - Intake and Alignment

1. Capture current objective, constraints, and decisions in `conversation-state.md`.
2. Normalize all key nouns to canonical glossary terms.
3. Record unresolved ambiguities as explicit open questions.

Exit gate:

- Objective, scope boundary, and success criteria are all explicit.
- No overloaded term is used without qualifier.

## Phase 2 - Findings Capture

1. Write architecture observations in `architecture-findings.md`.
2. Write external/internal research signals in `research-findings.md`.
3. Tag each finding with confidence and operational impact.

Exit gate:

- Every finding has evidence and implication.
- Findings are separable from implementation choices.

## Phase 3 - Implementation Scaffolding

1. Convert findings into execution slices in `implementation-plan-scaffold.md`.
2. For each slice, define files/symbols, risks, and validation target.
3. Mark explicit assumptions and rollback notes.

Exit gate:

- Plan slices are testable and ordered.
- Risks and verification are defined per slice.

## Phase 4 - Downward Rehydration

1. Reference FFS0 artifacts from FFS1/FFS2/FFS3 docs where execution occurs.
2. Keep canon in one place (FFS0); avoid copy forks.
3. Update only execution-local docs downstream.

Exit gate:

- Downstream docs point to FFS0 canonical state.
- No conflicting duplicate canon exists.

## Session Closeout Checklist

- `conversation-state.md` reflects final session state.
- Findings files updated (or explicitly marked unchanged).
- Implementation scaffold updated with next executable step.
- Any new canonical term change is reflected in both glossary `.md` and `.json`.
