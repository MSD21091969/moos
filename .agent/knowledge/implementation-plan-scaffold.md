# Implementation Plan Scaffold

Last Updated: 2026-03-01

## Objective

- Implementation objective: Run the first complete conversation-state rehydration cycle and produce a concrete downstream execution-ready slice set.
- Success criteria:
	- `conversation-state.md` reflects the active objective and constraints for the current cycle.
	- At least one new architecture finding and one research finding are recorded with evidence.
	- Execution slices map to specific files/symbols in target workspace(s) with validation steps.

## Inputs

- Conversation state reference: `.agent/knowledge/conversation-state.md`
- Architecture findings reference: `.agent/knowledge/architecture-findings.md`
- Research findings reference: `.agent/knowledge/research-findings.md`
- Canonical glossary reference: `.agent/knowledge/current-codebase-glossary-canonical-v1.md`

## Execution Slices

### Slice 1: Intake Refresh and Term Normalization

- Goal: Refresh objective/scope/constraints and normalize all planning nouns to canonical glossary terms.
- Files / Symbols:
	- `.agent/knowledge/conversation-state.md`
	- `.agent/knowledge/current-codebase-glossary-canonical-v1.md`
- Changes (concise):
	- Update objective, locked decisions, constraints, open questions, and next-session bootstrap.
	- Add any new term exceptions explicitly (if present).
- Risks:
	- Hidden term drift if updates are made without glossary check.
- Validation:
	- Manual check: no overloaded noun used without qualifier in updated state file.
	- Canonical check field remains `yes` or exceptions are explicitly listed.
- Rollback note:
	- Revert only the delta section entries if objective framing is incorrect.

### Slice 2: Findings Consolidation

- Goal: Capture new architecture and research signals derived from current code exploration/session work.
- Files / Symbols:
	- `.agent/knowledge/architecture-findings.md`
	- `.agent/knowledge/research-findings.md`
- Changes (concise):
	- Add at least one evidence-backed finding in each file.
	- Update confidence and impact with explicit rationale.
- Risks:
	- Mixing implementation proposals into findings (should remain finding-level).
- Validation:
	- Each finding includes evidence + implications + confidence.
	- Findings remain terminology-aligned with canonical glossary.
- Rollback note:
	- Remove or demote low-confidence findings to open questions.

### Slice 3: Downstream Execution Hand-off Draft

- Goal: Create the next actionable implementation hand-off for the target workspace without duplicating canon.
- Files / Symbols:
	- `.agent/knowledge/implementation-plan-scaffold.md`
	- target local docs in `workspaces/FFS1_ColliderDataSystems/.agent/...` (reference-only until execution begins)
- Changes (concise):
	- Translate findings into 2-4 execution tasks with file/symbol mapping and validation gates.
	- Add explicit pointers back to FFS0 canon artifacts.
- Risks:
	- Over-scoping beyond current cycle.
	- Reintroducing conflicting local canon downstream.
- Validation:
	- Each task has a measurable output and a test/build/check command or artifact verification step.
	- References point to FFS0 canon for terminology/process.
- Rollback note:
	- Trim to minimum executable slices and defer extras to backlog/open items.

## Assumptions

- Assumption: FFS0 remains canonical for glossary/process and downstream workspaces consume by reference.
- Verification plan: confirm downstream docs link to FFS0 artifacts instead of restating canon.

- Assumption: Current canonical glossary v1 is sufficient for ongoing implementation planning.
- Verification plan: track new ambiguities in `conversation-state.md`; only update glossary when ambiguity is blocking.

## Open Items

- Item: Define governance cadence for canonical glossary updates (release-driven vs session-driven).
- Owner / next action: project owner to choose cadence and record in `conversation-state.md` locked decisions.

- Item: Define propagation policy depth for FFS1/FFS2/FFS3 (link-only vs summary mirror).
- Owner / next action: decide policy before first large downstream architecture update.
