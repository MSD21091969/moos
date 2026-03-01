# Architecture Findings

Last Updated: 2026-03-01

## Purpose

Capture architecture-grounded findings from current code/repo state using canonical glossary terms.

## Finding Entry Template

### Finding: <short title>

- Domain:
- Confidence: high/medium/low
- Evidence:
  - File(s):
  - Symbol(s):
- Current Behavior:
- Risk / Cost of Keeping As-Is:
- Contract Impact (API/proto/schema/runtime):
- Canonical Terms Used:
- Recommended Direction (non-implementation):

## Findings

### Finding: Canonical language layer exists and is operationally anchored

- Domain: governance / terminology
- Confidence: high
- Evidence:
  - File(s): `.agent/knowledge/current-codebase-glossary-canonical-v1.md`, `.agent/knowledge/current-codebase-glossary-canonical-v1.json`
  - Symbol(s): locked terms + usage rules + transition mapping
- Current Behavior: canonical vocabulary is defined and can be used as precondition for architecture/planning docs.
- Risk / Cost of Keeping As-Is: low; primary risk is under-enforcement rather than model deficiency.
- Contract Impact (API/proto/schema/runtime): medium indirect impact by reducing naming drift across `app`/`application`/`appnode` and session identifiers.
- Canonical Terms Used: `app`, `appnode`, `session_id`, `context`, `tool`, `workflow`, `Node`, `NodeContainer`.
- Recommended Direction (non-implementation): require glossary alignment step before authoring new architecture or implementation artifacts.

### Finding: Rehydration artifacts were previously absent at FFS0 root

- Domain: process architecture
- Confidence: high
- Evidence:
  - File(s): newly created `.agent/workflows/conversation-state-rehydration.md` and four `.agent/knowledge/*.md` state/findings/scaffold files
  - Symbol(s): phase-based runbook and template sections
- Current Behavior: conversation continuity depended on ad hoc summaries; no stable runbook/template chain existed.
- Risk / Cost of Keeping As-Is: high historical risk (context loss across long sessions and token resets).
- Contract Impact (API/proto/schema/runtime): none direct; strong impact on design/implementation consistency.
- Canonical Terms Used: `workflow`, `context`, `agent`, `subagent`.
- Recommended Direction (non-implementation): keep FFS0 as canonical process layer and treat downstream docs as execution-local projections.

### Finding: FFS0 and FFS1 documentation authority is split and requires explicit boundaries

- Domain: architecture ownership
- Confidence: medium
- Evidence:
  - File(s): `.agent/index.md` (FFS0 pointers), `workspaces/FFS1_ColliderDataSystems/.agent/knowledge/architecture/*`
  - Symbol(s): references indicating architecture docs in FFS1 while governance/context canon lives in FFS0
- Current Behavior: execution architecture details are FFS1-heavy; term/process canon is FFS0-heavy.
- Risk / Cost of Keeping As-Is: medium; potential for divergence if boundaries are implicit.
- Contract Impact (API/proto/schema/runtime): medium via doc-driven design decisions affecting schema/API language.
- Canonical Terms Used: `workspace`, `context`, `graph`, `api_boundary`.
- Recommended Direction (non-implementation): maintain explicit dual-layer rule: FFS0 = canonical language/process; FFS1+ = implementation/operational architecture.
