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

- canonical doctrine already present in `01_foundations/`, `02_architecture/`, and `03_semantics/`
- contingent value/config instances in `04_value_layer/`
- interpreted paper and transcript digests in `05_reference/`
- raw transcript files and archived provenance inputs under `_legacy/`

## Anti-drift rule

No transcript, paper, or design note becomes canon merely by existence or persuasive phrasing. Promotion must be explicit.

## Provenance boundary

- Direct legacy-path citations belong in `00_governance/`, `05_reference/`, or `_legacy/` only.
- Canonical doctrine and structured registries should cite canonical KB locations or explicit provenance notes inside the destination file.
- Promotion may use legacy material as input, but destination canon should not read as a mirror of source file layout.
