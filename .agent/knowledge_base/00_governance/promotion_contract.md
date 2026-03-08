# Promotion Contract

## Purpose

Define how source material becomes canonical doctrine or structured registry content.

## Promotion gates

A concept may be promoted only if all of the following hold:

1. Its destination role is identified: doctrine, architecture, semantics, value, or reference.
2. Its terminology is normalized against `03_semantics/04_normalization_rules.md`.
3. If it requires typed ids or stable references, it is added to `superset/ontology.json`.
4. If it is contingent, environment-bound, runtime-specific, or identity-instance-specific, it is routed to `04_value_layer/`.
5. Its provenance is recorded.

## Source classes

- current canonical source docs in `.agent/knowledge/01_foundations/` and `02_architecture/`
- candidate design docs in `.agent/knowledge/05_moos_design/`
- planning material in `.agent/knowledge/06_planning/`
- value/config instances in `.agent/knowledge/datasets/`
- interpreted paper and transcript digests
- raw transcript files

## Anti-drift rule

No transcript, paper, or design note becomes canon merely by existence or persuasive phrasing. Promotion must be explicit.

## Provenance boundary

- Direct legacy-path citations belong in `00_governance/`, `05_reference/`, or `_legacy/` only.
- Canonical doctrine and structured registries should cite canonical KB locations or `00_governance/migration_map.md` for lineage.
- Promotion may use legacy material as input, but destination canon should not read as a mirror of source file layout.
