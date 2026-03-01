# Research Findings

Last Updated: 2026-03-01

## Purpose

Capture research inputs that can influence architecture or execution, with explicit confidence and applicability.

## Finding Entry Template

### Finding: <short title>

- Source Type: internal/external
- Source:
- Date:
- Confidence: high/medium/low
- Relevance to Current Objective:
- Actionable Signal:
- Adoption Notes (how to apply in this repo):
- Risks / Unknowns:

## Findings

### Finding: SkillsBench supports focused curated skills over broad dumps

- Source Type: external
- Source: `arXiv:2602.12670 (SkillsBench)`
- Date: 2026-02
- Confidence: high
- Relevance to Current Objective: validates glossary-first and selective-context discipline in rehydration and runtime design docs.
- Actionable Signal: prefer compact curated skill/context slices (2-3 focal units) and avoid comprehensive context flooding.
- Adoption Notes (how to apply in this repo): in planning docs, prioritize ranked findings and minimal executable slices instead of exhaustive prose bundles.
- Risks / Unknowns: benchmark-domain transfer to Collider-specific workflows is strong but not absolute.

### Finding: Harness engineering trend favors simpler, stable orchestration layers

- Source Type: external
- Source: synthesized industry material captured in prior architecture notes (Anthropic/OpenAI/Manus/Pi ecosystem signals)
- Date: 2026-02
- Confidence: medium
- Relevance to Current Objective: supports the runbook approach where process/state artifacts do the coordination and reduce ad hoc complexity.
- Actionable Signal: keep orchestration artifacts simple, explicit, and removable; avoid overloading runtime semantics into unstable prose.
- Adoption Notes: use typed templates (`conversation-state`, findings, scaffold) as persistent coordination substrate.
- Risks / Unknowns: external guidance evolves quickly; requires periodic refresh.

### Finding: Canonical glossary decisions are now an internal research baseline

- Source Type: internal
- Source: `.agent/knowledge/current-codebase-glossary-canonical-v1.md` and `.json`
- Date: 2026-02-28
- Confidence: high
- Relevance to Current Objective: provides a stable language contract for rehydration output quality.
- Actionable Signal: enforce canonical term checks before generating plans/specs; treat exceptions as explicit open items.
- Adoption Notes: include canonical term validation in every planning session closeout.
- Risks / Unknowns: future term expansions need governance cadence to avoid drift.
