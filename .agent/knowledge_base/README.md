# Knowledge Base vNext

This directory is the clean-slate canonical destination for the Collider knowledge base.

## Purpose

`knowledge_base/` separates:

- doctrine from contingent runtime facts
- semantics from syntax and projection
- reference sources from promoted canon
- structured registries from prose doctrine

## Canonical zones

1. `00_governance/` — authority, read order, promotion, migration
2. `01_foundations/` — axioms, primitives, category language, invariants
3. `02_architecture/` — kernel, strata, functors, governance, provider and benchmark architecture
4. `03_semantics/` — hydration, syntax vs semantics, state/topology/time, normalization, agent interpretation
5. `04_value_layer/` — contingent instances: providers, identities, workstation, runtime, platform distribution
6. `05_reference/` — non-canonical digests and raw sources
7. `superset/` — machine-readable canonical registry and derivative exports
8. `_legacy/` — archived source structure and migration inputs

## Rules

- Markdown is canonical for doctrine.
- JSON is canonical for structured registries and contingent value instances.
- CSV is derivative only.
- Raw `.txt` and `.pdf` sources are reference-only.
- A concept has one canonical home.

## Current status

This tree has been scaffolded and seeded for controlled-provenance migration.
Provenance records belong in `00_governance/`; destination doctrine and registries should remain decoupled from legacy file paths.
Downstream manifests and ingestion should only be switched after destination content is sufficiently populated and verified.
